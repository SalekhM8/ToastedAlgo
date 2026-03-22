"""
Automated grading system for Toasted training plan generator.

Uses a second Claude API call to assess plan quality against the 115-point
grading rubric.  The deterministic validator (backend/generator/validator.py)
catches hard safety violations; this grader evaluates subjective quality —
exercise selection, programming sophistication, rehab quality, etc.

Usage::

    from backend.grading.grader import grade_plan, load_grading_rubric

    rubric = load_grading_rubric()
    result = grade_plan(plan, user_profile, rubric)
    print(result["scaled_score"])   # 1-10
    print(result["total"])          # 0-115
    print(result["passed"])         # bool
"""

from __future__ import annotations

import json
import os
import pathlib
from typing import Any

import anthropic

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_RUBRIC_PATH = (
    pathlib.Path(__file__).resolve().parent.parent / "data" / "grading_rubric.md"
)

_MODEL = "claude-opus-4-6"

_MAX_TOKENS = 8192

# Scoring scale: raw total -> 1-10 scaled score
_SCALE: list[tuple[int, int, int]] = [
    # (min_total, max_total, scaled_score)
    (104, 115, 10),
    (92, 103, 9),
    (81, 91, 8),
    (69, 80, 7),
    (58, 68, 6),
    (0, 57, 0),  # fail
]

# Mandatory fail conditions
_MANDATORY_FAIL_CRITERIA: list[dict[str, Any]] = [
    {
        "id": "1A",
        "label": "Banned movement compliance",
        "fail_threshold": 0,
        "fail_message": "Criterion 1A (banned movement compliance) scored 0 — automatic fail.",
    },
    {
        "id": "1D",
        "label": "Red flag respect",
        "fail_threshold": 0,
        "fail_message": "Criterion 1D (red flag respect) scored 0 — automatic fail.",
    },
    {
        "id": "1E",
        "label": "Clinician restriction respect",
        "fail_threshold": 0,
        "fail_message": "Criterion 1E (clinician restriction respect) scored 0 — automatic fail.",
    },
]

_MANDATORY_FAIL_AGGREGATES: list[dict[str, Any]] = [
    {
        "criterion": "safety",
        "criterion_number": 1,
        "threshold": 10,
        "max": 15,
        "fail_message": "Safety total below 10/15 — automatic fail.",
    },
    {
        "criterion": "programming_sophistication",
        "criterion_number": 8,
        "threshold": 12,
        "max": 20,
        "fail_message": "Programming Sophistication below 12/20 — automatic fail.",
    },
    {
        "criterion": "question_answer_alignment",
        "criterion_number": 9,
        "threshold": 6,
        "max": 10,
        "fail_message": "Question-Answer Alignment below 6/10 — automatic fail.",
    },
]

# ---------------------------------------------------------------------------
# Criterion definitions (for structured output)
# ---------------------------------------------------------------------------

CRITERIA = [
    {
        "number": 1,
        "name": "Safety",
        "max_points": 15,
        "key": "safety",
        "sub_criteria": [
            {"id": "1A", "name": "Banned movement compliance", "max": 5},
            {"id": "1B", "name": "Rehab block placement", "max": 3},
            {"id": "1C", "name": "Regional proportionality", "max": 3},
            {"id": "1D", "name": "Red flag respect", "max": 2},
            {"id": "1E", "name": "Clinician restriction respect", "max": 2},
        ],
    },
    {
        "number": 2,
        "name": "Exercise Selection",
        "max_points": 15,
        "key": "exercise_selection",
        "sub_criteria": [
            {"id": "2A", "name": "Goal appropriateness", "max": 5},
            {"id": "2B", "name": "Experience appropriateness", "max": 3},
            {"id": "2C", "name": "Equipment compliance", "max": 3},
            {"id": "2D", "name": "No duplicates within a day", "max": 2},
            {"id": "2E", "name": "Exercise variety", "max": 2},
        ],
    },
    {
        "number": 3,
        "name": "Plan Structure",
        "max_points": 15,
        "key": "plan_structure",
        "sub_criteria": [
            {"id": "3A", "name": "Session time budget", "max": 3},
            {"id": "3B", "name": "Exercise count per session", "max": 3},
            {"id": "3C", "name": "Sets and reps appropriateness", "max": 3},
            {"id": "3D", "name": "Day labelling honesty", "max": 3},
            {"id": "3E", "name": "Progressive structure", "max": 3},
        ],
    },
    {
        "number": 4,
        "name": "Rehab Quality",
        "max_points": 20,
        "key": "rehab_quality",
        "sub_criteria": [
            {"id": "4A", "name": "Right tissues targeted", "max": 5},
            {"id": "4B", "name": "Appropriate dosing", "max": 3},
            {"id": "4C", "name": "Warm-up content", "max": 3},
            {"id": "4D", "name": "Balance and proprioception", "max": 2},
            {"id": "4E", "name": "Rehab to gym transition", "max": 2},
            {"id": "4F", "name": "Rehab progression logic", "max": 3},
            {"id": "4G", "name": "Rehab exercise variety", "max": 2},
        ],
    },
    {
        "number": 5,
        "name": "Honesty & Communication",
        "max_points": 10,
        "key": "honesty_communication",
        "sub_criteria": [
            {"id": "5A", "name": "Honest about limitations", "max": 4},
            {"id": "5B", "name": "Explains modifications", "max": 3},
            {"id": "5C", "name": "Appropriate warnings", "max": 3},
        ],
    },
    {
        "number": 6,
        "name": "Frequency Handling",
        "max_points": 5,
        "key": "frequency_handling",
        "sub_criteria": [
            {"id": "6A", "name": "Day count structure", "max": 3},
            {"id": "6B", "name": "Rehab frequency", "max": 2},
        ],
    },
    {
        "number": 7,
        "name": "Multi-Injury Handling",
        "max_points": 5,
        "key": "multi_injury_handling",
        "sub_criteria": [
            {"id": "7A", "name": "All injuries addressed", "max": 3},
            {"id": "7B", "name": "Time budget managed", "max": 2},
        ],
    },
    {
        "number": 8,
        "name": "Programming Sophistication",
        "max_points": 20,
        "key": "programming_sophistication",
        "sub_criteria": [
            {"id": "8A", "name": "Exercise sequencing", "max": 4},
            {"id": "8B", "name": "Weekly fatigue management", "max": 4},
            {"id": "8C", "name": "Push/pull balance", "max": 3},
            {"id": "8D", "name": "Periodisation model", "max": 3},
            {"id": "8E", "name": "Rest period specificity", "max": 2},
            {"id": "8F", "name": "Tempo prescription", "max": 2},
            {"id": "8G", "name": "Context-appropriate programming", "max": 2},
        ],
    },
    {
        "number": 9,
        "name": "Question-Answer Alignment",
        "max_points": 10,
        "key": "question_answer_alignment",
        "sub_criteria": [
            {"id": "9A", "name": "Goal alignment", "max": 2},
            {"id": "9B", "name": "Day count respected", "max": 1},
            {"id": "9C", "name": "Session length respected", "max": 1},
            {"id": "9D", "name": "Experience level reflected", "max": 2},
            {"id": "9E", "name": "Equipment respected", "max": 1},
            {"id": "9F", "name": "Injury severity reflected", "max": 2},
            {"id": "9G", "name": "Priority slider reflected", "max": 1},
        ],
    },
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_grading_rubric(path: str | pathlib.Path | None = None) -> str:
    """Read the grading rubric markdown file and return its full text.

    Parameters
    ----------
    path : str or Path, optional
        Override the default rubric location
        (``backend/data/grading_rubric.md``).
    """
    rubric_path = pathlib.Path(path) if path else _RUBRIC_PATH
    if not rubric_path.exists():
        raise FileNotFoundError(
            f"Grading rubric not found at {rubric_path}. "
            "Ensure backend/data/grading_rubric.md exists."
        )
    return rubric_path.read_text(encoding="utf-8")


def grade_plan(
    plan: dict[str, Any],
    user_profile: dict[str, Any],
    rubric_text: str | None = None,
    *,
    model: str = _MODEL,
    api_key: str | None = None,
    max_tokens: int = _MAX_TOKENS,
) -> dict[str, Any]:
    """Grade a generated plan against the 115-point rubric via a Claude API call.

    Parameters
    ----------
    plan : dict
        The generated training plan (JSON-serialisable).
    user_profile : dict
        The user's onboarding profile (JSON-serialisable).
    rubric_text : str, optional
        Full text of the grading rubric.  If ``None``, it is loaded from disk.
    model : str
        Claude model to use.  Defaults to ``claude-opus-4-6``.
    api_key : str, optional
        Anthropic API key.  Falls back to ``ANTHROPIC_API_KEY`` env var.
    max_tokens : int
        Max response tokens.

    Returns
    -------
    dict with keys:
        - ``criteria``: dict mapping criterion key -> sub-criterion scores + total
        - ``sub_scores``: dict mapping sub-criterion id (e.g. "1A") -> score
        - ``total``: int (0-115)
        - ``scaled_score``: int (1-10, or 0 for fail)
        - ``passed``: bool
        - ``mandatory_fails``: list[str] — reasons for mandatory failure (empty if none)
        - ``assessment``: str — free-text summary from the grading AI
        - ``raw_response``: str — the raw JSON string from Claude (for debugging)
    """
    if rubric_text is None:
        rubric_text = load_grading_rubric()

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "No API key provided.  Set ANTHROPIC_API_KEY environment variable "
            "or pass api_key argument."
        )

    client = anthropic.Anthropic(api_key=key)

    prompt = _build_grading_prompt(plan, user_profile, rubric_text)

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text
    grading_result = _parse_grading_response(raw_text)
    return grading_result


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def _build_grading_prompt(
    plan: dict[str, Any],
    user_profile: dict[str, Any],
    rubric_text: str,
) -> str:
    """Build the grading prompt sent to Claude."""

    # Build the expected JSON output schema description
    sub_criteria_schema_lines: list[str] = []
    for criterion in CRITERIA:
        for sc in criterion["sub_criteria"]:
            sub_criteria_schema_lines.append(
                f'    "{sc["id"]}": {{"score": <int 0-{sc["max"]}>, '
                f'"reasoning": "<1-2 sentences>"}}'
            )

    criteria_schema_lines: list[str] = []
    for criterion in CRITERIA:
        sc_ids = ", ".join(f'"{sc["id"]}"' for sc in criterion["sub_criteria"])
        criteria_schema_lines.append(
            f'    "{criterion["key"]}": {{"total": <int 0-{criterion["max_points"]}>, '
            f'"sub_criteria_ids": [{sc_ids}]}}'
        )

    output_schema = f"""\
{{
  "sub_scores": {{
{chr(10).join(sub_criteria_schema_lines)}
  }},
  "criteria": {{
{chr(10).join(criteria_schema_lines)}
  }},
  "total": <int 0-115>,
  "assessment": "<2-4 sentence overall assessment>"
}}"""

    # Check if the user profile indicates rehab-only mode
    rehab_only_note = ""
    if user_profile.get("mode") == "rehab_only":
        rehab_only_note = (
            "\n\nIMPORTANT — REHAB ONLY PLAN: This is a REHAB ONLY plan — no gym "
            "component. Grade Criterion 4 (Rehab Quality) as the primary quality "
            "criterion. The entire plan IS rehab."
        )

    prompt = f"""\
You are an expert grader for the Toasted training plan generator. You have deep \
expertise in strength and conditioning programming, physiotherapy-led \
rehabilitation, and evidence-based exercise prescription.

Your task is to grade the training plan below against the grading rubric. \
Be strict — an 8/10 plan should be genuinely good. A 10/10 plan should be \
what a top-tier physiotherapist and S&C coach would write together.

Score EVERY criterion and sub-criterion. Provide brief reasoning for each \
sub-criterion score. Then calculate the totals.

---

## GRADING RUBRIC

{rubric_text}

---

## USER PROFILE

```json
{json.dumps(user_profile, indent=2, default=str)}
```

---

## GENERATED PLAN

```json
{json.dumps(plan, indent=2, default=str)}
```

---

## INSTRUCTIONS

1. Read the user profile carefully. Understand their goal, experience, \
equipment, injuries, phase, mode, days per week, and session length.

2. Read the generated plan carefully. Check every exercise, every set/rep \
prescription, every rest period, every block label, every day label.

3. Score each sub-criterion according to the rubric. Use the EXACT scoring \
anchors provided (e.g., 5 = ..., 3 = ..., 0 = ...). Do not invent \
intermediate scores unless the rubric allows them.

4. For Criterion 4 (Rehab Quality): if the user has no injuries and the mode \
is gym_only, auto-score 20/20 and note "N/A — no injuries".{rehab_only_note}

5. For Criterion 7 (Multi-Injury Handling): if the user has 0 or 1 injuries, \
auto-score 5/5 and note "N/A — single or no injury".

6. Calculate each criterion total (sum of its sub-criteria).

7. Calculate the overall total (sum of all criteria, max 115).

8. Provide a 2-4 sentence overall assessment.

## REQUIRED OUTPUT FORMAT

Respond with ONLY valid JSON matching this schema (no markdown, no extra text):

{output_schema}

Important: ensure every sub-criterion ID is present in sub_scores. Ensure \
every criterion key is present in criteria. The total must equal the sum of \
all criterion totals.
"""
    return prompt


# ---------------------------------------------------------------------------
# Response parsing and post-processing
# ---------------------------------------------------------------------------


def _parse_grading_response(raw_text: str) -> dict[str, Any]:
    """Parse Claude's JSON response and compute derived fields.

    Returns the full grading result dict.
    """
    # Strip markdown code fences if the model wrapped the JSON
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (```json or ```)
        first_newline = cleaned.index("\n")
        cleaned = cleaned[first_newline + 1:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].rstrip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return {
            "criteria": {},
            "sub_scores": {},
            "total": 0,
            "scaled_score": 0,
            "passed": False,
            "mandatory_fails": [f"Failed to parse grading response: {exc}"],
            "assessment": "Grading response was not valid JSON.",
            "raw_response": raw_text,
        }

    sub_scores: dict[str, Any] = data.get("sub_scores", {})
    criteria: dict[str, Any] = data.get("criteria", {})
    total: int = data.get("total", 0)
    assessment: str = data.get("assessment", "")

    # Re-derive total from sub-scores for safety
    computed_total = 0
    for criterion in CRITERIA:
        criterion_sum = 0
        for sc in criterion["sub_criteria"]:
            sc_data = sub_scores.get(sc["id"], {})
            sc_score = sc_data.get("score", 0) if isinstance(sc_data, dict) else 0
            criterion_sum += sc_score
        # Update criteria totals to match sub-score sums
        if criterion["key"] in criteria:
            criteria[criterion["key"]]["total"] = criterion_sum
        else:
            criteria[criterion["key"]] = {"total": criterion_sum}
        computed_total += criterion_sum

    # Use computed total (more reliable than model's self-reported total)
    total = computed_total

    # Compute scaled score
    scaled_score = _compute_scaled_score(total)

    # Check mandatory fail conditions
    mandatory_fails: list[str] = []

    # Sub-criterion mandatory fails
    for mf in _MANDATORY_FAIL_CRITERIA:
        sc_data = sub_scores.get(mf["id"], {})
        sc_score = sc_data.get("score", 0) if isinstance(sc_data, dict) else 0
        if sc_score <= mf["fail_threshold"]:
            mandatory_fails.append(mf["fail_message"])

    # Aggregate mandatory fails
    for mf in _MANDATORY_FAIL_AGGREGATES:
        criterion_data = criteria.get(mf["criterion"], {})
        criterion_total = criterion_data.get("total", 0) if isinstance(criterion_data, dict) else 0
        if criterion_total < mf["threshold"]:
            mandatory_fails.append(mf["fail_message"])

    # Determine pass/fail
    passed = scaled_score >= 8 and len(mandatory_fails) == 0

    return {
        "criteria": criteria,
        "sub_scores": sub_scores,
        "total": total,
        "scaled_score": scaled_score,
        "passed": passed,
        "mandatory_fails": mandatory_fails,
        "assessment": assessment,
        "raw_response": raw_text,
    }


def _compute_scaled_score(total: int) -> int:
    """Map a raw total (0-115) to the 1-10 scale."""
    for min_total, max_total, score in _SCALE:
        if min_total <= total <= max_total:
            return score
    # Below 58 = fail (score 0)
    return 0


# ---------------------------------------------------------------------------
# Convenience: combined validate-then-grade pipeline
# ---------------------------------------------------------------------------


def validate_and_grade(
    plan: dict[str, Any],
    user_profile: dict[str, Any],
    rubric_text: str | None = None,
    *,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Run deterministic validation first, then AI grading.

    Returns a combined result dict with both validator and grader outputs.

    If the deterministic validator finds errors, the plan is marked as failed
    WITHOUT calling the grading API (saves cost).
    """
    from backend.generator.validator import PlanValidator

    validator = PlanValidator()
    is_valid, val_errors, val_warnings = validator.validate(plan, user_profile)

    result: dict[str, Any] = {
        "validation": {
            "is_valid": is_valid,
            "errors": val_errors,
            "warnings": val_warnings,
        },
        "grading": None,
        "overall_passed": False,
    }

    if not is_valid:
        result["overall_passed"] = False
        return result

    # Deterministic checks passed — now grade with Claude
    grading_result = grade_plan(
        plan,
        user_profile,
        rubric_text,
        api_key=api_key,
    )

    result["grading"] = grading_result
    result["overall_passed"] = grading_result["passed"]

    return result
