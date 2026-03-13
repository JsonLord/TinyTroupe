from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from typing import List, Dict, Any
import uuid

from backend.models.schemas import SimulationRequest, GeneratePersonasRequest, SimulationResponse, BulkSimulationRequest, Persona
from backend.core.job_registry import job_registry
from backend.services.tinytroupe_manager import tinytroupe_manager
from backend.services.persona_matcher import persona_matcher
from backend.core.config import settings

router = APIRouter(prefix="/api/v1")

@router.post("/simulations", response_model=SimulationResponse)
async def start_simulation(request: SimulationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job_registry.create_job(job_id, {"request": request.model_dump()})

    # In a real scenario, fetch personas from a DB/storage based on request.focus_group_id
    # Here we simulate fetching 2 personas for the given focus group
    mock_personas_data = [
        {"name": f"Tech Founder 1_{job_id[:4]}", "occupation": "Software Engineer"},
        {"name": f"Tech Founder 2_{job_id[:4]}", "occupation": "Product Manager"}
    ]

    background_tasks.add_task(
        tinytroupe_manager.run_simulation_async,
        job_id,
        request.content_payload,
        mock_personas_data,
        request.content_type,
        request.parameters or {},
        job_registry
    )

    return SimulationResponse(job_id=job_id, status="PENDING", message="Simulation job queued.")

@router.get("/simulations/{job_id}", response_model=SimulationResponse)
async def get_simulation_status(job_id: str):
    job_data = job_registry.get_job(job_id)
    if job_data.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Simulation job not found")

    return SimulationResponse(
        job_id=job_id,
        status=job_data.get("status", "UNKNOWN"),
        progress_percentage=job_data.get("progress_percentage", 0),
        message=job_data.get("message"),
        results=job_data.get("results")
    )

@router.post("/simulations/bulk", response_model=List[SimulationResponse])
async def bulk_start_simulations(bulk_request: BulkSimulationRequest, background_tasks: BackgroundTasks):
    responses = []
    for req in bulk_request.requests:
        resp = await start_simulation(req, background_tasks)
        responses.append(resp)
    return responses

@router.get("/personas", response_model=Dict[str, List[Persona]])
async def get_personas():
    return {
        "focus_groups": [
            Persona(id="tech_founders_eu", name="Tech Founders EU", agent_count=5),
            Persona(id="marketing_pros_us", name="Marketing Professionals US", agent_count=3)
        ]
    }

@router.post("/personas/generate", response_model=SimulationResponse)
async def generate_personas(request: GeneratePersonasRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job_registry.create_job(job_id, {"request": request.model_dump()})

    background_tasks.add_task(
        tinytroupe_manager.generate_personas_async,
        request.business_description,
        request.customer_profile,
        request.num_personas,
        job_id,
        job_registry
    )

    return SimulationResponse(job_id=job_id, status="PENDING", message="Persona generation job queued.")
