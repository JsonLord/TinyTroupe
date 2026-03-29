from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SimulationRequest(BaseModel):
    focus_group_id: str = Field(..., description="ID of the focus group to use")
    content_type: str = Field(..., description="Type of content (e.g., article, post)")
    content_payload: str = Field(..., description="The actual content text to simulate")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters like creativity, duration")

class GeneratePersonasRequest(BaseModel):
    business_description: str = Field(..., description="Description of the business or product")
    customer_profile: str = Field(..., description="Profile of the target customer")
    num_personas: int = Field(default=5, ge=1, le=10, description="Number of personas to generate")

class SimulationResponse(BaseModel):
    job_id: str = Field(..., description="Unique ID for the simulation job")
    status: str = Field(..., description="Status of the job (PENDING, RUNNING, COMPLETED, FAILED)")
    message: Optional[str] = Field(None, description="Additional information about the job status")
    progress_percentage: int = Field(0, description="Progress percentage (0-100)")
    results: Optional[Dict[str, Any]] = Field(None, description="Results of the simulation if completed")

class BulkSimulationRequest(BaseModel):
    requests: List[SimulationRequest] = Field(..., description="List of simulation requests")

class Persona(BaseModel):
    id: str = Field(..., description="ID of the persona")
    name: str = Field(..., description="Name of the persona")
    agent_count: Optional[int] = Field(None, description="Number of agents in a focus group (if this represents a group)")
