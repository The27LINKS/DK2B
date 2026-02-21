import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from agent.schema import RequirementList, AgentState

# Load environment variables (Make sure GOOGLE_API_KEY is in your .env)
load_dotenv()

# Initialize the Free Gemini Model
# In agent/nodes.py
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", # Use a stable 2.5 model
    temperature=0,
    max_retries=3,            # Built-in retry for intermittent 429s
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

def extract_requirements(state: AgentState):
    """Analyst Node: Extracts structured requirements using Gemini for free."""
    # Gemini supports structured output just like GPT-4
    structured_llm = llm.with_structured_output(RequirementList)
    
    prompt = (
        "You are a Senior Business Analyst. "
        f"Extract all business requirements from this data: {state.raw_input}"
    )
    
    # Process the data
    response = structured_llm.invoke(prompt)
    
    return {"parsed_requirements": response.requirements}

def validate_requirements(state: AgentState):
    """Auditor Node: Checks for logical contradictions."""
    if not state.parsed_requirements:
        return {"conflicts": ["No requirements found to validate."]}
        
    req_text = "\n".join([f"- {r.title}: {r.description}" for r in state.parsed_requirements])
    
    prompt = f"Act as a Project Auditor. Review these requirements for contradictions or gaps: {req_text}"
    
    response = llm.invoke(prompt)
    return {"conflicts": [response.content]}

def format_final_brd(state: AgentState):
    """Composer Node: Generates the final professional Markdown report."""
    report = "# Business Requirements Document (BRD)\n\n"
    report += "## 1. Functional Requirements\n"
    
    for req in state.parsed_requirements:
        report += f"### {req.title}\n"
        report += f"- **Priority**: {req.priority}\n"
        report += f"- **Description**: {req.description}\n\n"
    
    report += "## 2. Auditor Insights\n"
    for conflict in state.conflicts:
        report += f"{conflict}\n"
        
    return {"final_report": report}