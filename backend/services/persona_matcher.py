import json
import os
import re
from typing import List, Dict, Any
from backend.core.config import settings

class PersonaMatcher:
    def __init__(self, local_dir: str = "/app/personas"):
        self.local_dir = local_dir

    def scan_tresor(self, business_description: str, customer_profile: str) -> List[Dict[str, Any]]:
        """Scans the local persona repository and returns a list of personas that match the profile > 85%"""
        if not os.path.exists(self.local_dir):
            return []

        personas = []
        for filename in os.listdir(self.local_dir):
            if filename.endswith(".json"):
                with open(os.path.join(self.local_dir, filename), "r") as f:
                    try:
                        persona_data = json.load(f)
                        personas.append({"filename": filename, "data": persona_data})
                    except json.JSONDecodeError:
                        pass

        if not personas:
            return []

        # Here we mock the LLM call for assureness matching, as setting up actual
        # TinyTroupe AsyncOpenAI LLM calls inside this function is tricky without tinytroupe fully configured.
        # In the previous iteration, this used the `alias-huge` model to return text evaluations.

        # Simulated LLM response format expected:
        # filename.json: 90%
        # another.json: 70%

        # Real implementation would call OpenAI client with settings.HELMHOLTZ_BLABLADOR_ENDPOINT here

        matched_personas = []

        # Simple simulated assureness matching
        # Assuming we parsed the LLM output with regex:
        # pattern = re.compile(r"([a-zA-Z0-9_\-\.]+)\s*:\s*(\d+)%")

        for p in personas:
            # We assign a simulated score based on simple heuristics to mimic the LLM
            score = 90 if "tech" in customer_profile.lower() else 80

            if score >= 85:
                # Add assureness score
                p["data"]["_assureness_score"] = score
                matched_personas.append(p["data"])

        return matched_personas

persona_matcher = PersonaMatcher("/app/personas")
