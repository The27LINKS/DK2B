# DK2B — IntellIgence engIne DocumentatIon

## Version: 1.

## Project Type: AI-Assisted BRD Analysis Platform

## Executive Summary:

This document outlines the architecture, setup, and functional logic of DK2B, an AI-powered
Business Requirements Document (BRD) analysis engine. The system ingests text, PDFs, or
CSV files, extracts structured requirements, detects conflicts, and generates Mermaid.js
diagrams. It leverages Google's Gemini models via LangChain and LangGraph, orchestrating
workflows through a FastAPI backend and streaming real-time analysis to a single-page
frontend.

## 1. System Architecture & Core Modules

The DK2B platform is divided into a robust backend API, an alternative agentic pipeline, a
data parser, and a responsive frontend client.

## 1.1 Backend Orchestration (backend/main.py)

The core FastAPI application serves as the primary engine for processing data, orchestrating
LLM calls, and streaming responses back to the client.

- **Primary Endpoint:** /analyze-project handles incoming `text_data` (form data)
    or file (PDF/CSV uploads).
- **File Parsing & Chunking:** Uses pypdf.PdfReader to extract text from PDFs. Large text
    blocks are split using chunk_text(text, chunk_size=25000) to enable map-reduce style
    processing and prevent token limit issues.
- **LLM Integration:** Instantiates ChatGoogleGenerativeAI configured with strict Pydantic
    schemas (Requirement, ProjectAnalysis) to ensure the Gemini model outputs highly
    structured data.
- **API Key Rotation:** Implements rotate_api_key(). If the model throws
    a ResourceExhausted (429) error, the backend automatically advances
    the current_key_index to cycle through available keys.
- **Real-time Streaming:** Instead of making the user wait for full completion, the
    backend streams **NDJSON** progress events (progress, complete, error). Upon
    completion, it merges extracted requirements and preserves the most complex
    Mermaid.js fragment.

## 1.2 LangGraph Agent Pipeline (agent/)


An alternative, node-based workflow for parsing, auditing, and formatting BRDs using an
intelligent agent architecture.

- **State & Schemas (agent/schema.py):** Defines the AgentState passed between nodes
    (containing raw_input, parsed_requirements, conflicts, and final_report). Strict
    validation is enforced via Pydantic models like Requirement and RequirementList.
- **Functional Nodes (agent/nodes.py):**
    o extract_requirements: Queries the LLM to pull a structured RequirementList.
    o validate_requirements: Audits the parsed data and detects internal conflicts.
    o format_final_brd: Assembles the extracted requirements and identified
       conflicts into a formatted Markdown BRD.
- **Graph Compilation (agent/graph.py):** Builds a StateGraph linking
    the analyst → auditor → composer nodes, compiling them into the
    executable brd_agent.

### 1.3 Data Ingestion Pipeline (data_pipeline/email_parser.py)

- **Email Body Extraction:** Provides the get_clean_body(raw_email_path) function to
    strip out header metadata (e.g., -----Original Message-----) from raw text files,
    ensuring the LLM only processes relevant content.

### 1.4 Frontend Client (Engine/)

A static, single-page application (SPA) that provides the user interface for the intelligence
engine.

- **Structure (Engine/index.html):** Manages the layout for text input, file uploads, and
    drag-and-drop zones.
- **Logic & Rendering (Engine/script.js):**
    o Posts multi-part form data to the backend API.
    o Utilizes the ReadableStream reader to consume the NDJSON stream, updating
       progress bars dynamically.
    o Renders requirements and conflicts into the DOM.
    o Implements sanitizeMermaidFrontend(code) to clean and render LLM-
       generated Mermaid.js syntax accurately.

### 2. Configuration & Infrastructure

### 2.1 Cloudflare Tunneling (config.yml)


Contains Cloudflare Tunnel configurations mapping the public hostname
(e.g., https://dk2b.the27links.in) to local services. This facilitates secure external exposure
via cloudflared without opening inbound firewall ports.

### 2.2 Environment Variables

Required configurations stored in your .env file:

- GEMINI_API_KEYS: A comma-separated list of Gemini keys. Highly recommended for
    production to enable backend key rotation upon ResourceExhausted errors.
- GOOGLE_API_KEY: A fallback, single API key if rotation is not utilized.

### 3. Setup & Execution

### 3.1 Local Development Environment

Initialize your Python virtual environment and install the required dependencies (LangGraph,
LangChain, FastAPI, Uvicorn, Pydantic, python-dotenv, pypdf):

python -m venv venv

venv\Scripts\Activate.ps

pip install -r requirements.txt

### 3.2 Running the Backend

Start the Uvicorn server from the repository root:

venv\Scripts\Activate.ps

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

### 3.3 Running the Frontend

Open Engine/index.html in a web browser. To test locally alongside the backend, update
the API_URL variable inside Engine/script.js to point to [http://localhost:8000/analyze-](http://localhost:8000/analyze-)
project.

### 4. API Reference

**Endpoint: /analyze-project**

- **Method:** POST
- **Payload (Form Data):**
    o text_data (String, Optional) - Direct text input.


```
o file (File Upload, Optional) - PDF or CSV document.
```
- **Response Format:** Streaming NDJSON
- **Event Types:**
    o progress: Emits continuous updates during chunk processing.
    o complete: Final payload containing data.requirements, data.conflicts,
       and data.mermaid_code.
    o error: Emitted if processing fails.

### 5. Recommended Roadmap & Improvements

- **Testing:** Implement unit and integration tests specifically targeting stream parsing
    and the boundary behaviors of chunk_text.
- **Validation:** Develop a CLI utility or initialization script to validate .env entries,
    ensuring GEMINI_API_KEYS are well-formed before server startup.
- **Containerization:** Create a Dockerfile and docker-compose.yml to bundle the FastAPI
    backend and a static file server for the UI, making local testing and deployment
    entirely reproducible.
## 👥 Team Members

| S.No. | Name | Role |
| :--- | :--- | :--- |
| **1.** || **Divya Raj** | Frontend Developer |
| **2.** || **Pt. Sumit Kumar Sharma** | Backend Architech & Documentation Author  |
| **3.** || **Harikesh Singh** | Data Engineer  |
| **4.** || **Teena Parmar** | Pitch Lead & Presenter  |

---
<p align="center">
  <b>Powered By The27LINKS</b> <br>
  <i>Project Created By : Burner Bros</i> 
</p>
