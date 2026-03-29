import threading
import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class JobRegistry:
    def __init__(self, storage_file: str = "/tmp/job_registry.json"):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.storage_file = storage_file
        self._load()

    def _save(self):
        try:
            with open(self.storage_file, "w") as f:
                json.dump(self._jobs, f)
        except Exception as e:
            logger.error(f"Failed to save job registry to disk: {e}")

    def _load(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    self._jobs = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load job registry from disk: {e}")

    def create_job(self, job_id: str, initial_data: Dict[str, Any] = None):
        with self._lock:
            self._jobs[job_id] = {
                "status": "PENDING",
                "progress_percentage": 0,
                "results": None,
                **(initial_data or {})
            }
            self._save()

    def update_job(self, job_id: str, **kwargs):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(kwargs)
                self._save()

    def get_job(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            return self._jobs.get(job_id, {"status": "NOT_FOUND"})

    def delete_job(self, job_id: str):
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                self._save()

    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return dict(self._jobs)

job_registry = JobRegistry()
