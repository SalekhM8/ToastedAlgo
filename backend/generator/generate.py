"""
Claude API integration for Toasted plan generation.
Uses prompt caching on the system prompt (rules document).
"""

from __future__ import annotations

import json
import os
import anthropic
from dotenv import load_dotenv

from .prompt import build_system_prompt, build_user_prompt

load_dotenv()


def get_client() -> anthropic.Anthropic:
    """Get an Anthropic client using the API key from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return anthropic.Anthropic(api_key=api_key)


def parse_plan_json(raw_text: str) -> dict:
    """Parse JSON from Claude's response, handling potential markdown wrapping."""
    text = raw_text.strip()

    # Remove markdown code block wrapping
    if text.startswith("```"):
        # Remove first line (```json or ```)
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        # Remove trailing ```
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    return json.loads(text)


def generate_plan(user_profile: dict, retrieved_chunks: list[str]) -> dict:
    """
    Generate a training plan using Claude Opus 4.6.

    Args:
        user_profile: User's onboarding answers
        retrieved_chunks: Research chunks from RAG retrieval

    Returns:
        Parsed plan as a dict
    """
    print("[generate] Building prompts...", flush=True)
    client = get_client()
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(user_profile, retrieved_chunks)
    print(f"[generate] Prompts built. System: {len(system_prompt)} chars, User: {len(user_prompt)} chars", flush=True)
    print(f"[generate] Calling Claude API (claude-sonnet-4-6, max_tokens=16000)...", flush=True)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        timeout=120.0,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    print(f"[generate] API responded. Stop reason: {response.stop_reason}, usage: {response.usage}", flush=True)
    plan_text = response.content[0].text
    plan = parse_plan_json(plan_text)
    print(f"[generate] Plan parsed. Keys: {list(plan.keys())}", flush=True)

    return plan


def generate_plan_with_retry(
    user_profile: dict,
    retrieved_chunks: list[str],
    errors: list[dict] | None = None,
) -> dict:
    """
    Generate a plan, optionally including error feedback from a previous failed attempt.

    Args:
        user_profile: User's onboarding answers
        retrieved_chunks: Research chunks from RAG retrieval
        errors: List of validation errors from a previous attempt

    Returns:
        Parsed plan as a dict
    """
    chunks = list(retrieved_chunks)

    if errors:
        error_feedback = "\n".join(
            f"ERROR: {e.get('reason', e.get('type', 'Unknown error'))}" if isinstance(e, dict) else f"ERROR: {e}"
            for e in errors
        )
        chunks.append(
            f"\n\nCRITICAL: Your previous attempt had these errors. FIX THEM:\n{error_feedback}"
        )

    return generate_plan(user_profile, chunks)
