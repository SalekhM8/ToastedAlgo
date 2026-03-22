"""
Prompt construction for Toasted plan generation.
Builds the system prompt (rules + output format, cached) and user prompt (research + profile).
"""

from __future__ import annotations

import os
from pathlib import Path


def load_rules_document() -> str:
    """Load the full rules document from data/rules.md."""
    rules_path = Path(__file__).parent.parent / "data" / "rules.md"
    with open(rules_path, "r") as f:
        return f.read()


SYSTEM_PROMPT_TEMPLATE = """You are the Toasted training plan engine. You generate personalised \
training plans based on research evidence and strict rules.

## YOUR RULES (NEVER VIOLATE THESE)

{rules_document}

## OUTPUT FORMAT

You MUST output the plan as valid JSON matching this exact schema:

{{
  "planHeader": {{
    "goal": "string",
    "mode": "gym_only | rehab_only | both",
    "daysPerWeek": number,
    "sessionMinutes": number,
    "experience": "beginner | intermediate | advanced",
    "equipment": "full_gym | basic_gym | home_db_bands | minimal",
    "injuries": [
      {{
        "condition": "string",
        "severity": "string",
        "phase": "string",
        "region": "string",
        "clinicianRestrictions": "string or null"
      }}
    ]
  }},
  "honestyVerdict": {{
    "goalViability": "genuine | partial | not_viable",
    "message": "string — honest assessment per Rule 21"
  }},
  "days": [
    {{
      "dayNumber": number,
      "title": "string — honest label per Rule 20",
      "dayType": "string — e.g. upper/hard, speed/moderate, rehab/easy",
      "intensityLevel": "hard | moderate | easy",
      "estimatedMinutes": number,
      "blocks": [
        {{
          "blockType": "rehab_warmup | general_warmup | main_gym | rehab_accessories | conditioning | core | rehab_mobility | rehab_activation | rehab_strengthening | rehab_proprioception | rehab_cooldown",
          "blockLabel": "string",
          "estimatedMinutes": number,
          "exercises": [
            {{
              "name": "string — clear, unambiguous exercise name",
              "sets": number,
              "reps": "string — e.g. '5', '30s', '10 each', '20m'",
              "rpe": number,
              "restSeconds": number,
              "tempo": "string or null — e.g. '3-0-1-0'",
              "doseNotes": "string or null — e.g. 'partial ROM to 70 degrees', 'linear only'",
              "purpose": "gym | rehab",
              "substitutionNote": "string or null — e.g. 'replaces back squat (deep flexion limited for MCL Phase 1)'"
            }}
          ]
        }}
      ]
    }}
  ],
  "homeSessions": {{
    "frequencyPerWeek": number,
    "durationMinutes": number,
    "exercises": [
      {{
        "name": "string",
        "sets": number,
        "reps": "string",
        "rpe": number,
        "purpose": "string"
      }}
    ]
  }} | null,
  "deloadInstructions": "string — what changes on deload weeks",
  "progressionGuidance": "string — how to progress across weeks",
  "warnings": ["string — any relevant cautions"]
}}

Output ONLY valid JSON. No markdown, no explanation, no preamble. Just the JSON object.
"""


def build_system_prompt() -> str:
    """Build the system prompt with rules document inserted."""
    rules = load_rules_document()
    return SYSTEM_PROMPT_TEMPLATE.format(rules_document=rules)


def build_user_prompt(user_profile: dict, retrieved_chunks: list[str]) -> str:
    """
    Build the user prompt with retrieved research and user profile.

    Args:
        user_profile: Dict with user's onboarding answers
        retrieved_chunks: List of research text chunks from RAG
    """
    if retrieved_chunks:
        research_text = "\n\n---\n\n".join(retrieved_chunks)
        research_section = f"""## RELEVANT RESEARCH FOR THIS USER

The following research excerpts are directly relevant to this user's \
conditions and goals. Use this research to inform your exercise selection, \
rehab protocols, progression criteria, and programming decisions.

{research_text}

---
"""
    else:
        research_section = """## RESEARCH CONTEXT

No research papers are currently loaded in the database. Generate the plan \
using the rules document and your training in exercise science, S&C programming, \
and rehabilitation principles. Follow all rules strictly.

---
"""

    # Build user profile section
    user_prompt = f"""{research_section}
## USER PROFILE

Goal: {user_profile.get('goal', 'general_fitness')}
Mode: {user_profile.get('mode', 'gym_only')}
Days per week: {user_profile.get('days_per_week', 4)}
Session length: {user_profile.get('session_minutes', 60)} minutes
Experience: {user_profile.get('experience', 'intermediate')}
Equipment: {user_profile.get('equipment', 'full_gym')}
"""

    # Both mode extras
    if user_profile.get('mode') == 'both':
        user_prompt += f"""
Dedicated rehab days: {user_profile.get('dedicated_rehab_days', 'No')}
Gym sessions per week: {user_profile.get('gym_sessions', user_profile.get('days_per_week', 4))}
Rehab sessions per week: {user_profile.get('rehab_sessions', 0)}
Priority balance: {user_profile.get('priority_slider', '50/50')}
"""

    # Rehab only extras
    if user_profile.get('mode') == 'rehab_only':
        user_prompt += f"""
Currently seeing physio: {user_profile.get('seeing_physio', 'Unknown')}
Previous rehab experience: {user_profile.get('previous_rehab', 'None')}

IMPORTANT: This is a REHAB ONLY plan — no gym component. The entire plan \
IS rehab. Follow the rehab-only session structure rules (Section 13). \
Each session should follow: warm-up → mobility → activation → progressive \
strengthening → proprioception/balance → cool-down. Use block types: \
"rehab_warmup", "rehab_mobility", "rehab_activation", "rehab_strengthening", \
"rehab_proprioception", "rehab_cooldown". All exercises have purpose "rehab". \
All RPE values should be 3-6 (this is rehab, not gym training). \
Vary sessions across the week (strength-focused vs mobility-focused days).
"""

    # Injuries
    for i, injury in enumerate(user_profile.get('injuries', [])):
        user_prompt += f"""

### Injury {i + 1}:
Diagnosed: {injury.get('diagnosed', False)}
"""
        if injury.get('diagnosed'):
            user_prompt += f"""Condition: {injury.get('condition', 'Unknown')}
Severity/Grade: {injury.get('severity', 'Not specified')}
Time since onset/surgery: {injury.get('timeline', 'Not specified')}
Current pain (0-10): {injury.get('pain_level', 'Not specified')}
Functional level: {injury.get('functional_level', 'Not specified')}
Clinician restrictions: {injury.get('clinician_restrictions', 'None')}
"""
        else:
            user_prompt += f"""Region: {injury.get('region', 'Unknown')}
Description: {injury.get('description', '')}
When it bothers: {injury.get('when_bothers', '')}
Duration: {injury.get('duration', '')}
Worst pain this week (0-10): {injury.get('pain_level', '')}
Daily life impact: {injury.get('daily_impact', '')}
Routed to: {injury.get('routed_protocol', 'generic management')}
"""

    user_prompt += """

---

## INSTRUCTION

Generate a complete training plan for this user following ALL rules in \
your system prompt. Use the research provided to inform your clinical \
and programming decisions. Output valid JSON only.
"""

    return user_prompt
