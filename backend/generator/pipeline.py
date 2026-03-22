"""
Full generation pipeline: retrieve → generate → validate → (retry) → grade.
"""

from __future__ import annotations

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.rag.retrieve import retrieve_research_for_user
from backend.generator.generate import generate_plan, generate_plan_with_retry
from backend.generator.validator import PlanValidator
from backend.grading.grader import grade_plan, load_grading_rubric


def check_red_flags(user_profile: dict) -> dict | None:
    """
    Check if the user profile has red flags that block plan generation.
    Returns a block message dict if blocked, None if clear.
    """
    red_flags = user_profile.get("red_flags", {})
    injuries = user_profile.get("injuries", [])

    # Get injury regions
    injury_regions = [inj.get("region", "") for inj in injuries]

    # Bladder/bowel → URGENT
    if red_flags.get("bladder_bowel"):
        return {
            "blocked": True,
            "severity": "urgent",
            "message": (
                "URGENT: Please seek immediate medical attention (A&E). "
                "Problems with bladder or bowel control require urgent assessment. "
                "Do not start any exercise program before being seen."
            ),
        }

    # Numbness/tingling/weakness + spine region
    if (red_flags.get("numbness_tingling") or red_flags.get("weakness")) and "spine" in injury_regions:
        return {
            "blocked": True,
            "severity": "serious",
            "message": (
                "STOP: These symptoms (numbness, tingling, or weakness combined with spinal pain) "
                "could indicate a serious spinal condition. Please see a doctor or go to A&E "
                "before starting any exercise program."
            ),
        }

    # Chest pain/dizziness
    if red_flags.get("chest_pain"):
        return {
            "blocked": True,
            "severity": "medical",
            "message": (
                "Please see your GP before starting an exercise program. "
                "They can assess whether exercise is safe for your heart."
            ),
        }

    # Weight loss + fever + pain
    if red_flags.get("weight_loss") and red_flags.get("fever"):
        any_pain = any(inj.get("pain_level", 0) > 0 for inj in injuries)
        if any_pain:
            return {
                "blocked": True,
                "severity": "medical",
                "message": (
                    "These symptoms together (unexplained weight loss, fever, and pain) "
                    "may indicate something that needs medical investigation. "
                    "Please see your GP before starting."
                ),
            }

    # Cancer or infection
    if red_flags.get("cancer") or red_flags.get("infection"):
        return {
            "blocked": True,
            "severity": "medical",
            "message": (
                "Please get clearance from your medical team before starting "
                "any exercise program."
            ),
        }

    # Heart condition
    if red_flags.get("heart_condition"):
        return {
            "blocked": True,
            "severity": "medical",
            "message": (
                "Please get clearance from your GP before starting any exercise program. "
                "A heart condition that limits exercise needs to be assessed first."
            ),
        }

    # Osteoporosis — flag but DON'T block
    if red_flags.get("osteoporosis"):
        return {
            "blocked": False,
            "severity": "flag",
            "message": (
                "Note: Osteoporosis flagged. Plan will avoid high-impact exercises "
                "and prioritise weight-bearing strength work."
            ),
        }

    # Check if any injury was routed to red_flag_block
    for injury in injuries:
        if injury.get("routed_protocol") == "red_flag_block":
            return {
                "blocked": True,
                "severity": "serious",
                "message": (
                    "Based on your symptoms, we strongly recommend seeing a healthcare "
                    "professional before starting any exercise program. "
                    "Your profile has been saved — you can return after getting clearance."
                ),
            }

    return None


def generate_and_validate_plan(
    user_profile: dict,
    max_attempts: int = 3,
    run_grader: bool = False,
) -> dict:
    """
    Full pipeline: check red flags → retrieve → generate → validate → (retry) → optionally grade.

    Args:
        user_profile: User's onboarding answers
        max_attempts: Maximum generation attempts before failing
        run_grader: Whether to run the grader (for testing)

    Returns:
        Dict with plan, validation results, grade (if run), and metadata
    """
    # Step 0: Check red flags
    red_flag_result = check_red_flags(user_profile)
    if red_flag_result and red_flag_result.get("blocked"):
        return {
            "plan": None,
            "red_flag_block": red_flag_result,
            "validation": None,
            "grade": None,
            "attempts": 0,
            "failed": False,
            "blocked": True,
        }

    # Step 1: Retrieve relevant research
    research_chunks = retrieve_research_for_user(user_profile)
    print(f"Retrieved {len(research_chunks)} research chunks")

    validator = PlanValidator()
    errors = None

    for attempt in range(max_attempts):
        try:
            # Step 2: Generate plan
            if attempt == 0:
                plan = generate_plan(user_profile, research_chunks)
            else:
                plan = generate_plan_with_retry(user_profile, research_chunks, errors)

            num_days = len(plan.get("days", []))
            print(f"Attempt {attempt + 1}: Plan generated with {num_days} days")

            # Step 3: Validate
            is_valid, errors, warnings = validator.validate(plan, user_profile)

            if is_valid:
                print(f"Plan passed validation (warnings: {len(warnings)})")

                result = {
                    "plan": plan,
                    "validation": {"errors": errors, "warnings": warnings},
                    "grade": None,
                    "attempts": attempt + 1,
                    "failed": False,
                    "blocked": False,
                }

                # Step 4: Grade (optional, for testing)
                if run_grader:
                    try:
                        rubric = load_grading_rubric()
                        grade = grade_plan(plan, user_profile, rubric)
                        result["grade"] = grade
                        scaled = grade.get("scaledScore") or grade.get("scaled_score", "N/A")
                        print(f"Grade: {scaled}/10")
                    except Exception as e:
                        print(f"Grading failed: {e}")
                        result["grade"] = {"error": str(e)}

                # Add red flag warnings (non-blocking)
                if red_flag_result and not red_flag_result.get("blocked"):
                    result["red_flag_warning"] = red_flag_result

                return result
            else:
                print(f"Validation failed: {len(errors)} errors")
                for error in errors:
                    if isinstance(error, dict):
                        print(f"  - {error['type']}: {error.get('reason', error.get('exercise', ''))}")
                    else:
                        print(f"  - {error}")

        except json.JSONDecodeError as e:
            print(f"Attempt {attempt + 1}: Failed to parse plan JSON: {e}")
            errors = [{"type": "JSON_PARSE_ERROR", "reason": str(e), "severity": "critical"}]
        except Exception as e:
            print(f"Attempt {attempt + 1}: Generation error: {e}")
            errors = [{"type": "GENERATION_ERROR", "reason": str(e), "severity": "critical"}]

    # All attempts failed
    print(f"Plan failed validation after {max_attempts} attempts")
    return {
        "plan": None,
        "validation": {"errors": errors or [], "warnings": []},
        "grade": None,
        "attempts": max_attempts,
        "failed": True,
        "blocked": False,
    }
