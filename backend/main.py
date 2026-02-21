import os
import io
import csv
import json
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
from google.api_core import exceptions
from langchain_google_genai import ChatGoogleGenerativeAI
from pypdf import PdfReader

load_dotenv()

# --- API KEY ROTATION SETUP ---
keys_env = os.getenv("GEMINI_API_KEYS", "")
api_keys = [k.strip() for k in keys_env.split(",") if k.strip()]

if not api_keys:
    single_key = os.getenv("GOOGLE_API_KEY")
    if single_key:
        api_keys = [single_key.strip()]
    else:
        raise ValueError("No API keys found! Check your .env file.")

current_key_index = 0

def get_current_llm():
    """Dynamically loads the LangChain LLM using the currently active API key."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0,
        google_api_key=api_keys[current_key_index]
    )

def rotate_api_key():
    """Shifts the index to the next API key in the list."""
    global current_key_index
    current_key_index = (current_key_index + 1) % len(api_keys)
    print(f"[*] 429 Rate Limit hit. Rotating to API Key {current_key_index + 1}/{len(api_keys)}")


# --- SCHEMAS ---
class Requirement(BaseModel):
    title: str = Field(description="Short title of the requirement")
    priority: str = Field(description="HIGH, MEDIUM, or LOW")
    description: str = Field(description="Detailed technical description")

class ProjectAnalysis(BaseModel):
    requirements: List[Requirement]
    conflicts: List[str] = Field(description="List of logical contradictions found")
    mermaid_code: str = Field(description="Mermaid.js code for a flowchart or ERD representing these requirements")


# --- APP SETUP ---
app = FastAPI(title="DK2B Enterprise Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- HELPERS ---
def extract_text_from_pdf(file_file):
    reader = PdfReader(file_file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text

def chunk_text(text: str, chunk_size: int = 25000):
    """Breaks massive text into smaller strings of `chunk_size` characters."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


# --- ENDPOINTS ---
@app.post("/analyze-project")
async def analyze_project(
    text_data: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    global current_key_index

    # REAL-TIME STREAMING GENERATOR
    async def generate_analysis():
        try:
            # 1. Send Initial Progress to Frontend
            yield json.dumps({"type": "progress", "msg": "Ingesting and parsing file data...", "percent": 5}) + "\n"
            await asyncio.sleep(0.1) # Tiny sleep to let the frontend breathe

            # Input Handling & Data Extraction
            raw_input = ""
            if file:
                if file.filename.endswith(".pdf"):
                    raw_input = extract_text_from_pdf(file.file)
                elif file.filename.endswith(".csv"):
                    # Process CSV safely
                    content = await file.read()
                    decoded_content = content.decode("utf-8", errors="ignore")
                    csv_reader = csv.reader(io.StringIO(decoded_content))
                    for row in csv_reader:
                        raw_input += " | ".join(row) + "\n"
                else:
                    content = await file.read()
                    raw_input = content.decode("utf-8", errors="ignore")
            elif text_data:
                raw_input = text_data
            else:
                yield json.dumps({"type": "error", "msg": "No input provided"}) + "\n"
                return

            yield json.dumps({"type": "progress", "msg": "Fragmenting massive datasets...", "percent": 15}) + "\n"
            await asyncio.sleep(0.1)

            # Fragment / Chunk the Data
            chunks = chunk_text(raw_input, chunk_size=25000)
            total_chunks = len(chunks)
            print(f"[*] Processing {total_chunks} fragments of data...")

            # Aggregation containers
            all_requirements = []
            all_conflicts = []
            final_mermaid = ""

            # 2. Process Fragments and Stream Live Progress
            for index, chunk in enumerate(chunks):
                # Calculate real progress percentage (scaling from 15% up to 85%)
                progress_step = 15 + int(((index + 1) / total_chunks) * 70)
                yield json.dumps({"type": "progress", "msg": f"Analyzing fragment {index + 1} of {total_chunks}...", "percent": progress_step}) + "\n"
                
                print(f"    -> Analyzing fragment {index + 1}/{total_chunks}...")
                
                prompt = (
                    "You are a Senior Solutions Architect. Analyze the following FRAGMENT of project data. "
                    "1. Extract key functional requirements from this fragment. "
                    "2. Identify logical conflicts within this fragment. "
                    "3. Generate a 'Mermaid.js' flowchart representing ONLY the logic in this fragment. "
                    f"DATA FRAGMENT: {chunk}"
                )

                max_attempts = len(api_keys)
                chunk_success = False

                for attempt in range(max_attempts):
                    try:
                        llm = get_current_llm()
                        structured_llm = llm.with_structured_output(ProjectAnalysis)
                        
                        # Use ainvoke (async invoke) so the streaming response doesn't get blocked
                        result = await structured_llm.ainvoke(prompt)
                        
                        # Aggregate the results!
                        all_requirements.extend(result.requirements)
                        all_conflicts.extend(result.conflicts)
                        
                        if result.mermaid_code and len(result.mermaid_code) > 10:
                            final_mermaid = result.mermaid_code

                        chunk_success = True
                        break # Break out of the retry loop, move to the next chunk

                    except exceptions.ResourceExhausted:
                        rotate_api_key()
                        continue 
                        
                    except Exception as e:
                        print(f"    -> Error on fragment {index + 1}: {e}")
                        break # If it's a structural error, skip this chunk and continue

                if not chunk_success:
                    print(f"    -> Fragment {index + 1} completely failed due to quota limits on all keys. Skipping fragment.")

            # 3. Final Verification
            if not all_requirements:
                yield json.dumps({"type": "error", "msg": "Quota Limit hit on all keys, or the file was unreadable."}) + "\n"
                return

            yield json.dumps({"type": "progress", "msg": "Aggregating master report...", "percent": 95}) + "\n"
            await asyncio.sleep(0.5)

            # 4. Finalize Master Report
            master_report = {
                # Ensure Pydantic models are converted to dicts for JSON serialization
                "requirements": [r.dict() for r in all_requirements],
                "conflicts": all_conflicts,
                "mermaid_code": final_mermaid if final_mermaid else "graph TD; A[Data Ingested] --> B[Processing Complete]"
            }

            # 5. Send Final Data payload
            yield json.dumps({"type": "complete", "data": master_report}) + "\n"

        except Exception as e:
            print(f"Fatal Streaming Error: {e}")
            yield json.dumps({"type": "error", "msg": str(e)}) + "\n"

    # Return the stream directly to the frontend's reader!
    return StreamingResponse(generate_analysis(), media_type="application/x-ndjson")


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
