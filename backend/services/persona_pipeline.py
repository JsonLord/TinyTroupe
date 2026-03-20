import json
import os
import re
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import tinytroupe
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.validation import TinyPersonValidator
from tinytroupe.agent import TinyPerson
from openai import OpenAI

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Blablador client
# ─────────────────────────────────────────────────────────────────────────────

def get_blablador_client() -> OpenAI:
    # Use google if fallback is needed, but for now we follow the script rules:
    api_key = os.environ.get("GOOGLE_API_KEY", os.environ.get("OPENAI_API_KEY", "dummy_key"))
    return OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/" if "generative" in os.environ.get("OPENAI_API_BASE", "") or "GOOGLE_API_KEY" in os.environ else "https://generativelanguage.googleapis.com/v1beta/openai/"
    )

# ─────────────────────────────────────────────────────────────────────────────
# Input schemas
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CompanyProfile:
    name: str
    industry: str
    description: str
    market: str
    size: str
    challenges: list[str] = field(default_factory=list)

    def to_context_string(self) -> str:
        challenges_text = (
            "\n".join(f"- {c}" for c in self.challenges)
            if self.challenges else "None specified."
        )
        return f"""
Company: {self.name}
Industry: {self.industry}
Size: {self.size}
Market: {self.market}

Description:
{self.description}

Key challenges:
{challenges_text}
""".strip()

@dataclass
class CustomerSegment:
    name: str
    description: str
    typical_needs: list[str] = field(default_factory=list)
    typical_fears: list[str] = field(default_factory=list)
    size_hint: int = 1

    def to_role_brief(self, index: int, total: int) -> str:
        needs_text = "\n".join(f"- {n}" for n in self.typical_needs) or "Not specified."
        fears_text = "\n".join(f"- {f}" for f in self.typical_fears) or "Not specified."
        variation_hint = _variation_hint(index, total)

        return f"""
Customer segment: {self.name}

Segment description:
{self.description}

Typical needs from the company:
{needs_text}

Typical fears or blockers:
{fears_text}

{variation_hint}
Generate a single, specific individual who plausibly belongs to this segment.
Give them a realistic name, age, occupation, background, and personality.
Make them feel like a real person, not a stereotype.
""".strip()

def _variation_hint(index: int, total: int) -> str:
    if total <= 1:
        return ""
    hints = [
        "This persona should be on the younger end of the segment's age range.",
        "This persona should be on the older end of the segment's age range.",
        "This persona should be more digitally savvy than average for this segment.",
        "This persona should be more traditional and skeptical of technology.",
        "This persona should have a higher income than typical for this segment.",
        "This persona should have a tighter budget than typical for this segment.",
        "This persona should be particularly vocal and opinionated.",
        "This persona should be more passive and conflict-averse.",
    ]
    return f"Variation note: {hints[index % len(hints)]}"

# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Generate validation expectations
# ─────────────────────────────────────────────────────────────────────────────

def generate_validation_expectations(company: CompanyProfile, segment: CustomerSegment, client: OpenAI) -> str:
    prompt = f"""
You are a persona design expert helping validate AI-generated customer personas.

Given the company profile and customer segment below, write realistic and grounded
validation expectations describing what a persona from this segment SHOULD look like.

These expectations will be used to automatically score a generated persona.
Be specific. Be realistic. Include likely flaws, contradictions, and tensions
that a real person in this situation would have. Do not over-idealise.

Use these sections:
- Demographics (plausible age range, location, education, household situation)
- Professional traits (occupation, income level, career pressures)
- Personal traits (personality tendencies, stress points, blind spots)
- Relationship with {company.name} (why they use it, what frustrates them, loyalty level)
- Tastes and lifestyle (spending habits, hobbies, media, channels)
- Mindset and values (beliefs, fears, motivations)

---
COMPANY PROFILE:
{company.to_context_string()}

CUSTOMER SEGMENT:
Name: {segment.name}
Description: {segment.description}
Typical needs: {", ".join(segment.typical_needs) or "not specified"}
Typical fears: {", ".join(segment.typical_fears) or "not specified"}
---

Return only the expectations text. No preamble, no commentary, no markdown.
""".strip()

    try:
        response = client.chat.completions.create(
            model="gemini-3-flash-preview",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating expectations: {e}")
        return "Must be a realistic persona matching the segment."

# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Generate + validate a single persona
# ─────────────────────────────────────────────────────────────────────────────

def generate_single_persona(
    company: CompanyProfile,
    segment: CustomerSegment,
    expectations: str,
    index: int,
    total: int,
    min_score: float = 0.7,
    max_attempts: int = 3,
) -> tuple[TinyPerson, float, str]:

    factory = TinyPersonFactory(company.to_context_string())
    role_brief = segment.to_role_brief(index, total)

    person, score, justification = None, 0.0, ""

    for attempt in range(1, max_attempts + 1):
        logger.info(f"    Attempt {attempt}/{max_attempts}...")

        # Adding a sleep delay before generation to prevent 429
        time.sleep(10)

        person = factory.generate_person(role_brief)
        if person is None:
            logger.warning("Generation returned None, retrying...")
            continue

        logger.info(f"→ {person.minibio()[:80]}...")

        # Add delay before validation
        time.sleep(10)

        try:
            score, justification = TinyPersonValidator.validate_person(
                person,
                expectations=expectations,
                include_agent_spec=True,
                max_content_length=None,
            )
            # Safe unpack
            if score is None: score = 0.0
        except Exception as e:
            logger.warning(f"Validation failed: {e}")
            score = 0.0

        logger.info(f"    Score: {score:.2f}")

        if score >= min_score:
            logger.info(f"    ✓ Accepted")
            break
        if attempt < max_attempts:
            logger.info(f"    ✗ Below {min_score}, retrying...")

    return person, score, justification
