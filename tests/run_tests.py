"""
Run all 22 test cases: generate → validate → grade each one.
Usage: python tests/run_tests.py [--test-id N]
"""

import json
import sys
import os
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from backend.generator.pipeline import generate_and_validate_plan


def load_test_profiles() -> list[dict]:
    tests_path = Path(__file__).parent / "test_profiles.json"
    with open(tests_path) as f:
        return json.load(f)


def run_single_test(test_case: dict) -> dict:
    """Run a single test case and return the result."""
    profile = test_case["profile"]
    print(f"\n{'='*60}")
    print(f"Test Case {test_case['id']}: {test_case['name']}")
    print(f"{'='*60}")

    result = generate_and_validate_plan(profile, max_attempts=3, run_grader=True)

    if result.get("blocked"):
        print(f"\n  BLOCKED by red flags: {result['red_flag_block']['message'][:80]}...")
        return {"status": "blocked", "result": result}

    if result.get("failed"):
        print(f"\n  FAILED after {result['attempts']} attempts")
        errors = result.get("validation", {}).get("errors", [])
        for e in errors[:5]:
            print(f"    Error: {e.get('type')}: {e.get('reason', '')[:60]}")
        return {"status": "failed", "result": result}

    # Plan generated successfully
    plan = result["plan"]
    grade = result.get("grade", {})
    score = grade.get("scaledScore", "N/A") if grade and not grade.get("error") else "N/A"
    warnings = result.get("validation", {}).get("warnings", [])

    print(f"\n  Plan generated in {result['attempts']} attempt(s)")
    print(f"  Days: {len(plan.get('days', []))}")
    print(f"  Honesty: {plan.get('honestyVerdict', {}).get('goalViability', 'N/A')}")
    print(f"  Validation warnings: {len(warnings)}")
    print(f"  Grade: {score}/10")

    if grade and not grade.get("error"):
        print(f"  Total points: {grade.get('totalScore', 'N/A')}/{grade.get('maxScore', 110)}")
        mandatory = grade.get("mandatoryFails", [])
        if mandatory:
            print(f"  MANDATORY FAILS: {mandatory}")

    return {
        "status": "passed" if score != "N/A" and score >= 8 else "below_threshold",
        "score": score,
        "result": result,
    }


def main():
    parser = argparse.ArgumentParser(description="Run Toasted test cases")
    parser.add_argument("--test-id", type=int, help="Run a specific test case by ID")
    parser.add_argument("--easy", action="store_true", help="Run only easy cases (1-4)")
    parser.add_argument("--moderate", action="store_true", help="Run moderate cases (5-10)")
    parser.add_argument("--hard", action="store_true", help="Run hard cases (11-15)")
    parser.add_argument("--edge", action="store_true", help="Run edge cases (16-22)")
    args = parser.parse_args()

    test_cases = load_test_profiles()

    if args.test_id:
        test_cases = [tc for tc in test_cases if tc["id"] == args.test_id]
        if not test_cases:
            print(f"Test case {args.test_id} not found")
            sys.exit(1)
    elif args.easy:
        test_cases = [tc for tc in test_cases if tc["id"] <= 4]
    elif args.moderate:
        test_cases = [tc for tc in test_cases if 5 <= tc["id"] <= 10]
    elif args.hard:
        test_cases = [tc for tc in test_cases if 11 <= tc["id"] <= 15]
    elif args.edge:
        test_cases = [tc for tc in test_cases if tc["id"] >= 16]

    results = []
    for tc in test_cases:
        try:
            result = run_single_test(tc)
            results.append({"id": tc["id"], "name": tc["name"], **result})
        except Exception as e:
            print(f"\n  ERROR: {e}")
            results.append({"id": tc["id"], "name": tc["name"], "status": "error", "error": str(e)})

    # Summary
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for r in results if r["status"] == "passed")
    below = sum(1 for r in results if r["status"] == "below_threshold")
    blocked = sum(1 for r in results if r["status"] == "blocked")
    failed = sum(1 for r in results if r["status"] == "failed")
    errored = sum(1 for r in results if r["status"] == "error")

    print(f"Total:   {len(results)}")
    print(f"Passed (8+): {passed}")
    print(f"Below 8:     {below}")
    print(f"Blocked:     {blocked}")
    print(f"Failed:      {failed}")
    print(f"Errors:      {errored}")

    for r in results:
        icon = {"passed": "✅", "below_threshold": "⚠️", "blocked": "🛑", "failed": "❌", "error": "💥"}
        print(f"  {icon.get(r['status'], '?')} #{r['id']}: {r['name'][:50]} — {r['status']} {r.get('score', '')}")


if __name__ == "__main__":
    main()
