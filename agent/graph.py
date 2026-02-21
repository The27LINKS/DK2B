from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from agent.schema import AgentState
from agent.nodes import (
    extract_requirements, 
    validate_requirements, 
    format_final_brd
)

# 1. Define the Graph State
# This object is passed between nodes and updated at each step.
def create_agent():
    # We initialize the StateGraph with our Schema
    workflow = StateGraph(AgentState)

    # 2. Add Nodes
    # Each node is a function defined in agent/nodes.py
    workflow.add_node("analyst", extract_requirements)   # Extracts raw data
    workflow.add_node("auditor", validate_requirements)  # Checks for conflicts
    workflow.add_node("composer", format_final_brd)      # Final Markdown formatting

    # 3. Define the Flow (Edges)
    # Start -> Analyst -> Auditor -> Composer -> End
    workflow.set_entry_point("analyst")
    
    # We move from extraction to validation
    workflow.add_edge("analyst", "auditor")
    
    # We move from validation to the final document formatting
    workflow.add_edge("auditor", "composer")
    
    # The composer marks the end of the process
    workflow.add_edge("composer", END)

    # 4. Compile the Graph
    # This turns the logic into an executable "Agent"
    app = workflow.compile()
    return app

# Instantiate the agent for use in main.py
brd_agent = create_agent()