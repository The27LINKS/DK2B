from pydantic import BaseModel, Field
from typing import List

class Requirement(BaseModel):
    title: str = Field(description="Title of the requirement")
    category: str = Field(description="Functional, Non-functional, or Constraint")
    description: str = Field(description="Detailed explanation")
    priority: str = Field(description="High, Medium, or Low")

# THIS IS THE KEY FOR PRODUCTION EXTRACTION
class RequirementList(BaseModel):
    """A collection of business requirements."""
    requirements: List[Requirement]

class AgentState(BaseModel):
    raw_input: str
    parsed_requirements: List[Requirement] = []
    conflicts: List[str] = []
    final_report: str = ""