import threading
from typing import Dict, Any

class JobRegistry:
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_job(self, job_id: str, initial_data: Dict[str, Any] = None):
        with self._lock:
            self._jobs[job_id] = {
                "status": "PENDING",
                "progress_percentage": 0,
                "results": None,
                **(initial_data or {})
            }

    def update_job(self, job_id: str, **kwargs):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(kwargs)

    def get_job(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            return self._jobs.get(job_id, {"status": "NOT_FOUND"})

    def delete_job(self, job_id: str):
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]

    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return dict(self._jobs)

job_registry = JobRegistry()
