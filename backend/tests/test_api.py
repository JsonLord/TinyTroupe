from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to UserSync API"}

def test_start_simulation():
    response = client.post(
        "/api/v1/simulations",
        json={
            "focus_group_id": "tech_founders_eu",
            "content_type": "article",
            "content_payload": "We just secured $5.3M to build AI-native tools...",
            "parameters": {"creativity": 0.7, "duration": "short"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"

def test_get_personas():
    response = client.get("/api/v1/personas")
    assert response.status_code == 200
    data = response.json()
    assert "focus_groups" in data
    assert len(data["focus_groups"]) > 0

def test_job_registry_crud():
    from backend.core.job_registry import JobRegistry
    registry = JobRegistry()
    registry.create_job("test-job", {"test": "data"})

    job = registry.get_job("test-job")
    assert job["status"] == "PENDING"
    assert job["test"] == "data"

    registry.update_job("test-job", status="RUNNING")
    job = registry.get_job("test-job")
    assert job["status"] == "RUNNING"

    registry.delete_job("test-job")
    job = registry.get_job("test-job")
    assert job["status"] == "NOT_FOUND"

def test_tinytroupe_parallel_execution():
    from backend.services.tinytroupe_manager import TinyTroupeSimulationManager
    from backend.core.job_registry import JobRegistry
    import time

    manager = TinyTroupeSimulationManager()
    registry = JobRegistry()
    job_id = "test-job"
    registry.create_job(job_id)

    # Use mock personas for parallel testing
    mock_personas = [{"name": f"Mock {i}"} for i in range(5)]

    manager.run_simulation_async(
        job_id=job_id,
        content_text="test content",
        personas_data=mock_personas,
        format_type="article",
        parameters={},
        job_registry=registry
    )

    # Since it runs in an executor, we wait slightly for completion
    time.sleep(2)
    job = registry.get_job(job_id)
    assert job["status"] == "COMPLETED"
    assert "results" in job
    assert "impact_score" in job["results"]
