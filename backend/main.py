"""
Toasted — FastAPI server.
Serves the frontend and provides API endpoints for plan generation, validation, and grading.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv(Path(__file__).parent.parent / ".env")

from backend.generator.pipeline import generate_and_validate_plan, check_red_flags
from backend.grading.grader import grade_plan, load_grading_rubric

app = FastAPI(title="Toasted", description="Training plan generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# --- Pydantic Models ---


class InjuryProfile(BaseModel):
    diagnosed: bool = False
    condition: Optional[str] = None
    severity: Optional[str] = None
    timeline: Optional[str] = None
    pain_level: Optional[int] = None
    functional_level: Optional[str] = None
    clinician_restrictions: Optional[str] = None
    region: Optional[str] = None
    description: Optional[str] = None
    when_bothers: Optional[str] = None
    duration: Optional[str] = None
    daily_impact: Optional[str] = None
    routed_protocol: Optional[str] = None


class RedFlags(BaseModel):
    numbness_tingling: bool = False
    weakness: bool = False
    bladder_bowel: bool = False
    chest_pain: bool = False
    weight_loss: bool = False
    fever: bool = False
    fall_collision: bool = False
    osteoporosis: bool = False
    cancer: bool = False
    infection: bool = False
    heart_condition: bool = False


class UserProfile(BaseModel):
    goal: str = "general_fitness"
    mode: str = "gym_only"
    days_per_week: int = 4
    session_minutes: int = 60
    experience: str = "intermediate"
    equipment: str = "full_gym"
    injuries: List[InjuryProfile] = []
    red_flags: Optional[RedFlags] = None
    # Both mode
    dedicated_rehab_days: Optional[str] = None
    gym_sessions: Optional[int] = None
    rehab_sessions: Optional[int] = None
    priority_slider: Optional[str] = None
    # Rehab only
    seeing_physio: Optional[str] = None
    previous_rehab: Optional[str] = None


class GradeRequest(BaseModel):
    plan: dict
    user_profile: UserProfile


# --- Routes ---


@app.get("/")
async def serve_frontend():
    """Serve the main frontend page."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>Toasted</h1><p>Frontend not found. Check frontend/index.html.</p>")


@app.post("/api/generate-plan")
async def generate_plan_endpoint(user_profile: UserProfile):
    """
    Main endpoint: takes onboarding answers, returns a validated plan.
    Runs the full pipeline: red flag check → RAG retrieval → generation → validation.
    Retries up to 3 times if validation fails.
    """
    profile_dict = user_profile.model_dump(exclude_none=True)

    # Convert red_flags from model to dict
    if user_profile.red_flags:
        profile_dict["red_flags"] = user_profile.red_flags.model_dump()

    # Convert injuries from models to dicts
    profile_dict["injuries"] = [
        inj.model_dump(exclude_none=True) for inj in user_profile.injuries
    ]

    try:
        result = await asyncio.to_thread(
            generate_and_validate_plan, profile_dict, max_attempts=3, run_grader=False
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/grade-plan")
async def grade_plan_endpoint(request: GradeRequest):
    """
    Testing endpoint: grades an existing plan against the rubric.
    """
    try:
        rubric = load_grading_rubric()
        profile_dict = request.user_profile.model_dump(exclude_none=True)
        if request.user_profile.red_flags:
            profile_dict["red_flags"] = request.user_profile.red_flags.model_dump()
        profile_dict["injuries"] = [
            inj.model_dump(exclude_none=True) for inj in request.user_profile.injuries
        ]
        grade = grade_plan(request.plan, profile_dict, rubric)
        return grade
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/test-all")
async def run_all_tests():
    """
    Run all 22 test cases and return grades.
    WARNING: This makes many API calls and takes a while.
    """
    tests_path = Path(__file__).parent.parent / "tests" / "test_profiles.json"
    with open(tests_path) as f:
        test_cases = json.load(f)

    results = []
    for tc in test_cases:
        profile = tc["profile"]
        print(f"\n--- Test Case {tc['id']}: {tc['name']} ---")

        try:
            result = generate_and_validate_plan(profile, max_attempts=3, run_grader=True)
            results.append({
                "id": tc["id"],
                "name": tc["name"],
                "grade": result.get("grade"),
                "passed": (
                    (result.get("grade", {}).get("scaledScore") or result.get("grade", {}).get("scaled_score", 0)) >= 8
                    if result.get("grade") and not result.get("grade", {}).get("error")
                    else None
                ),
                "blocked": result.get("blocked", False),
                "failed": result.get("failed", False),
                "attempts": result.get("attempts", 0),
                "validation_errors": len(result.get("validation", {}).get("errors", [])) if result.get("validation") else 0,
            })
        except Exception as e:
            results.append({
                "id": tc["id"],
                "name": tc["name"],
                "error": str(e),
                "passed": False,
            })

    # Summary
    passed = sum(1 for r in results if r.get("passed"))
    blocked = sum(1 for r in results if r.get("blocked"))
    failed = sum(1 for r in results if r.get("failed"))

    return {
        "summary": {
            "total": len(results),
            "passed": passed,
            "blocked_by_red_flags": blocked,
            "failed": failed,
        },
        "results": results,
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    return {
        "status": "ok",
        "api_key_configured": bool(api_key and api_key.startswith("sk-ant-")),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
