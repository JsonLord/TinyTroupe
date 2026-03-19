import concurrent.futures
import time
import os
import json
import re
import logging
from typing import List, Dict, Any
import tinytroupe
from tinytroupe.agent import TinyPerson
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.extraction import ResultsExtractor
from backend.core.config import settings
from backend.services.persona_matcher import persona_matcher

logger = logging.getLogger(__name__)

class TinyTroupeSimulationManager:
    def __init__(self):
        self.max_concurrency = settings.MAX_CONCURRENCY
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrency)

    def generate_personas_async(self, business_description: str, customer_profile: str, num_personas: int, job_id: str, job_registry):
        try:
            # 1. First, check if there are any matching personas in the local /app/personas repo
            matched_personas = persona_matcher.scan_tresor(business_description, customer_profile)

            # Filter matches > 85% assureness score
            valid_personas = [p for p in matched_personas if p.get("_assureness_score", 0) >= 85]

            # Number of personas we still need to generate
            missing_count = max(0, num_personas - len(valid_personas))

            logger.info(f"Job {job_id}: Found {len(valid_personas)} matching personas. Generating {missing_count} new personas.")
            job_registry.update_job(job_id, progress_percentage=20)

            new_personas = []

            # 2. Generate missing personas via TinyTroupe LLM call
            if missing_count > 0:
                try:
                    # Utilize the TinyPersonFactory dynamic population pattern
                    # Utilize the TinyPersonFactory dynamic population pattern, but generate sequentially to avoid Google 429 rate limits
                    factory = TinyPersonFactory(business_description)

                    logger.info(f"Job {job_id}: Generating {missing_count} personas via TinyPersonFactory sequentially...")

                    for i in range(missing_count):
                        logger.info(f"Job {job_id}: Requesting persona {i+1}/{missing_count} from LLM...")
                        person = factory.generate_person(customer_profile)

                        if person:
                            persona_data = person._persona
                            persona_data["_assureness_score"] = 100 # New ones are perfectly matched to the description
                            new_personas.append(persona_data)

                            # Save to local file system for git sync
                            local_dir = "/app/personas"
                            os.makedirs(local_dir, exist_ok=True)
                            file_path = os.path.join(local_dir, f"{person.name.replace(' ', '_')}.json")
                            with open(file_path, "w") as f:
                                json.dump(persona_data, f, indent=4)

                        job_registry.update_job(job_id, progress_percentage=20 + int((i+1)/missing_count * 60))

                        # Throttle consecutive requests to respect Google Gemini free tier limits
                        if i < missing_count - 1:
                            time.sleep(10)

                except Exception as e:
                    logger.error(f"Error during persona generation: {e}")
                    job_registry.update_job(job_id, status="FAILED", message=f"LLM Error: {str(e)}")
                    return

            # Combine
            all_personas = valid_personas[:num_personas] + new_personas
            all_personas = all_personas[:num_personas] # Ensure we don't exceed the requested count

            # Push new personas
            if new_personas:
                from backend.services.git_sync import git_sync
                git_sync.background_push(commit_message=f"Added {len(new_personas)} new personas for job {job_id}")

            job_registry.update_job(
                job_id,
                status="COMPLETED",
                progress_percentage=100,
                results={"personas": all_personas}
            )

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            job_registry.update_job(job_id, status="FAILED", message=str(e))

    def run_simulation_async(self, job_id: str, content_text: str, personas_data: List[Dict[str, Any]], format_type: str, parameters: Dict[str, Any], job_registry):
        try:
            job_registry.update_job(job_id, progress_percentage=10, status="RUNNING")

            # Instantiate TinyPersons
            persons = []
            for p_data in personas_data:
                try:
                    p = TinyPerson(name=p_data.get("name", "Unknown"))
                    # Make sure TinyPerson uses the loaded dictionary for the _persona structure
                    p._persona = p_data
                    persons.append(p)
                except Exception as e:
                    logger.error(f"Failed to load person data: {e}")

            if not persons:
                job_registry.update_job(job_id, status="FAILED", message="No valid personas provided")
                return

            results = []

            # Run in parallel using the ThreadPoolExecutor
            def process_person(person: TinyPerson, index: int):
                try:
                    # Send prompt context
                    prompt = f"Please read this {format_type}:\n\n'{content_text}'"
                    person.listen_and_act(prompt)

                    # Use TinyTroupe native ResultsExtractor
                    extractor = ResultsExtractor()
                    objective = "Rate the impact, attention, and relevance of the content based on the agent's background. Ratings must be integer scores between 0 and 100. Also provide a detailed analytical comment."

                    extracted_data = extractor.extract_results_from_agent(
                        person,
                        extraction_objective=objective,
                        situation=f"Testing a new {format_type}",
                        fields=["impact_score", "attention", "relevance", "comment"],
                        fields_hints={
                            "impact_score": "Integer between 0 and 100",
                            "attention": "Integer between 0 and 100",
                            "relevance": "Integer between 0 and 100",
                            "comment": "A string containing a descriptive paragraph"
                        },
                        verbose=False
                    )

                    # Safe parsing fallback
                    if extracted_data is None or type(extracted_data) is not dict:
                        extracted_data = {}
                        extracted_data = {}

                    parsed_response = {
                        "name": person.name,
                        "impact_score": int(extracted_data.get("impact_score", 50)),
                        "attention": int(extracted_data.get("attention", 50)),
                        "relevance": int(extracted_data.get("relevance", 50)),
                        "comment": extracted_data.get("comment", "No comment provided.")
                    }

                    # Update progress
                    current_prog = job_registry.get_job(job_id).get("progress_percentage", 10)
                    progress_increment = max(1, 80 // len(persons))
                    job_registry.update_job(job_id, progress_percentage=current_prog + progress_increment)

                    return parsed_response

                except Exception as e:
                    logger.error(f"Person {person.name} failed to process: {e}")
                    return {"name": person.name, "error": str(e)}

            futures = [self._executor.submit(process_person, p, i) for i, p in enumerate(persons)]

            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

            # Aggregate results
            total_impact = sum(r.get("impact_score", 0) for r in results if "error" not in r)
            total_attention = sum(r.get("attention", 0) for r in results if "error" not in r)
            total_relevance = sum(r.get("relevance", 0) for r in results if "error" not in r)
            valid_count = len([r for r in results if "error" not in r])

            agg_results = {
                "impact_score": total_impact // valid_count if valid_count else 0,
                "attention": total_attention // valid_count if valid_count else 0,
                "relevance": total_relevance // valid_count if valid_count else 0,
                "key_insights": [r.get("comment") for r in results if "error" not in r][:3],
                "agent_dialogue": results
            }

            job_registry.update_job(
                job_id,
                status="COMPLETED",
                progress_percentage=100,
                results=agg_results
            )

        except Exception as e:
            logger.error(f"Simulation Job {job_id} failed: {e}")
            job_registry.update_job(job_id, status="FAILED", message=str(e))

tinytroupe_manager = TinyTroupeSimulationManager()
