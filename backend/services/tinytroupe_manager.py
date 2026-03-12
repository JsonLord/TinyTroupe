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
                    factory = TinyPersonFactory(business_description)
                    for i in range(missing_count):
                        logger.info(f"Job {job_id}: Generating persona {i+1}/{missing_count}...")

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
                # Prompt the persona with the content
                try:
                    # Instruct the persona to reply strictly in a JSON block
                    prompt = (
                        f"Please read this {format_type}:\n\n'{content_text}'\n\n"
                        f"Based on your persona and interests, rate its impact, attention, and relevance from 0 to 100, "
                        f"and provide a short comment analyzing it.\n"
                        f"Respond strictly with a JSON block in the following format:\n"
                        f"{{\n"
                        f"  \"impact_score\": 85,\n"
                        f"  \"attention\": 90,\n"
                        f"  \"relevance\": 88,\n"
                        f"  \"comment\": \"Your detailed comment here.\"\n"
                        f"}}"
                    )

                    person.listen_and_act(prompt)
                    response_texts = person.pop_actions_and_get_contents_for("TALK", False)

                    # Ensure we have a string
                    full_text = " ".join(response_texts) if isinstance(response_texts, list) else str(response_texts)

                    # Fallback default
                    parsed_response = {
                        "name": person.name,
                        "impact_score": 50,
                        "attention": 50,
                        "relevance": 50,
                        "comment": full_text[:200] + "..." if len(full_text) > 200 else full_text
                    }

                    # Attempt to extract JSON block
                    json_match = re.search(r"\{.*\}", full_text, re.DOTALL)
                    if json_match:
                        try:
                            extracted_data = json.loads(json_match.group(0))
                            parsed_response.update({
                                "impact_score": extracted_data.get("impact_score", 50),
                                "attention": extracted_data.get("attention", 50),
                                "relevance": extracted_data.get("relevance", 50),
                                "comment": extracted_data.get("comment", parsed_response["comment"])
                            })
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode JSON from {person.name}'s response: {full_text}")

                    # Update progress
                    current_prog = job_registry.get_job(job_id).get("progress_percentage", 10)
                    progress_increment = 80 // len(persons)
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
