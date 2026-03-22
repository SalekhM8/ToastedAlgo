"""
Toasted RAG Pipeline — Research Retrieval

Given a user profile (from onboarding), retrieves the most relevant research
chunks from the ChromaDB vector store and returns them as a list of strings
ready to be injected into the LLM prompt context window.

Usage:
    from backend.rag.retrieve import retrieve_research_for_user
    chunks = retrieve_research_for_user(user_profile)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import chromadb
    from chromadb.utils import embedding_functions
    _HAS_CHROMADB = True
except ImportError:
    _HAS_CHROMADB = False


# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_CHROMA_DB_PATH = str(_THIS_DIR / "toasted_rag_db")

COLLECTION_NAME = "toasted_papers"

# Budget: approximate max tokens we want to inject into the prompt.
# 30 000 tokens ~ 22 500 words (1 token ~ 0.75 words).  We use word count
# as a cheap proxy.
MAX_TOKEN_BUDGET = 30_000
_APPROX_WORDS_PER_TOKEN = 0.75
MAX_WORD_BUDGET = int(MAX_TOKEN_BUDGET * _APPROX_WORDS_PER_TOKEN)

# How many results to request per sub-query from ChromaDB
_N_RESULTS_PER_QUERY = 12


# ---------------------------------------------------------------------------
# Goal -> topic mapping
# ---------------------------------------------------------------------------
GOAL_TOPIC_MAP: dict[str, list[str]] = {
    "strength": [
        "strength_programming", "periodisation", "exercise_selection",
        "general_principles",
    ],
    "hypertrophy": [
        "hypertrophy_programming", "strength_programming", "exercise_selection",
        "periodisation",
    ],
    "speed": [
        "speed_programming", "sprint_mechanics", "power_programming",
        "plyometrics", "strength_programming",
    ],
    "power": [
        "power_programming", "plyometrics", "strength_programming",
        "speed_programming",
    ],
    "conditioning": [
        "conditioning_programming", "load_management",
    ],
    "general_fitness": [
        "general_principles", "strength_programming", "conditioning_programming",
        "exercise_selection",
    ],
    "athleticism": [
        "speed_programming", "power_programming", "strength_programming",
        "conditioning_programming", "periodisation",
    ],
    "rehab_only": [
        "rehab_protocol", "general_principles", "tissue_healing",
        "pain_monitoring", "load_management", "mobility",
    ],
    "mobility": [
        "mobility", "flexibility", "movement_screening", "general_principles",
    ],
    "both": [
        "rehab_protocol", "tissue_healing", "pain_monitoring", "gate_criteria",
        "strength_programming", "exercise_selection", "general_principles",
    ],
}

# ---------------------------------------------------------------------------
# Condition -> (conditions filter list, body_regions list)
# ---------------------------------------------------------------------------
CONDITION_MAP: dict[str, dict[str, list[str]]] = {
    # Knee
    "acl":                {"conditions": ["acl"],              "regions": ["knee"]},
    "acl_post_op":        {"conditions": ["acl"],              "regions": ["knee"]},
    "acl_postop":         {"conditions": ["acl"],              "regions": ["knee"]},
    "acl_conservative":   {"conditions": ["acl"],              "regions": ["knee"]},
    "mcl":                {"conditions": ["mcl"],              "regions": ["knee"]},
    "mcl_sprain":         {"conditions": ["mcl"],              "regions": ["knee"]},
    "lcl_sprain":         {"conditions": ["mcl"],              "regions": ["knee"]},
    "pcl":                {"conditions": ["pcl"],              "regions": ["knee"]},
    "pcl_sprain":         {"conditions": ["pcl"],              "regions": ["knee"]},
    "meniscus":           {"conditions": ["meniscus"],          "regions": ["knee"]},
    "meniscus_repair":    {"conditions": ["acl"],              "regions": ["knee"]},
    "meniscus_trim":      {"conditions": ["acl"],              "regions": ["knee"]},
    "anterior_knee":      {"conditions": ["anterior_knee"],    "regions": ["knee"]},
    "anterior_knee_pain": {"conditions": ["anterior_knee"],    "regions": ["knee"]},
    "pfps":               {"conditions": ["anterior_knee"],    "regions": ["knee"]},
    "patellar_tendon":    {"conditions": ["patellar_tendon", "general_tendinopathy"], "regions": ["knee"]},
    "patellar_tendinopathy": {"conditions": ["patellar_tendon", "general_tendinopathy"], "regions": ["knee"]},

    # Ankle
    "ankle_lateral":      {"conditions": ["ankle_lateral"],    "regions": ["ankle"]},
    "ankle_sprain":       {"conditions": ["ankle_lateral"],    "regions": ["ankle"]},
    "ankle_high":         {"conditions": ["ankle_lateral"],    "regions": ["ankle"]},
    "achilles":           {"conditions": ["achilles", "general_tendinopathy"], "regions": ["ankle"]},
    "achilles_tendinopathy": {"conditions": ["achilles", "general_tendinopathy"], "regions": ["ankle"]},

    # Shoulder
    "shoulder_cuff":      {"conditions": ["shoulder_cuff"],    "regions": ["shoulder"]},
    "rotator_cuff":       {"conditions": ["shoulder_cuff"],    "regions": ["shoulder"]},
    "shoulder_surgery":   {"conditions": ["shoulder_cuff"],    "regions": ["shoulder"]},
    "shoulder_instability": {"conditions": ["shoulder_instability"], "regions": ["shoulder"]},

    # Hip
    "hip_adductor":       {"conditions": ["hip_adductor"],     "regions": ["hip"]},
    "adductor_strain":    {"conditions": ["hip_adductor"],     "regions": ["hip"]},
    "hip_labral":         {"conditions": ["hip_labral"],       "regions": ["hip"]},
    "hip_impingement":    {"conditions": ["hip_labral"],       "regions": ["hip"]},
    "fai":                {"conditions": ["hip_labral"],       "regions": ["hip"]},

    # Elbow
    "elbow_lateral":      {"conditions": ["elbow_lateral"],    "regions": ["elbow"]},
    "tennis_elbow":       {"conditions": ["elbow_lateral"],    "regions": ["elbow"]},
    "lateral_epicondylalgia": {"conditions": ["elbow_lateral"], "regions": ["elbow"]},
    "medial_epicondylalgia":  {"conditions": ["elbow_lateral"], "regions": ["elbow"]},

    # Spine
    "lbp_flexion":        {"conditions": ["lbp_flexion"],      "regions": ["spine"]},
    "lbp_extension":      {"conditions": ["lbp_extension"],    "regions": ["spine"]},
    "lbp":                {"conditions": ["lbp_flexion", "lbp_extension"], "regions": ["spine"]},
    "low_back_pain":      {"conditions": ["lbp_flexion", "lbp_extension"], "regions": ["spine"]},
    "mechanical_lbp_flexion":   {"conditions": ["lbp_flexion"],  "regions": ["spine"]},
    "mechanical_lbp_extension": {"conditions": ["lbp_extension"], "regions": ["spine"]},
    "mechanical_lbp_general":   {"conditions": ["lbp_flexion"],  "regions": ["spine"]},
}

# Tendinopathy conditions that benefit from general tendinopathy research
TENDINOPATHY_CONDITIONS = {
    "patellar_tendon", "achilles", "shoulder_cuff", "elbow_lateral",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_collection():
    """
    Return the ChromaDB collection, or None if the database does not exist
    or the collection is empty.
    """
    if not _HAS_CHROMADB:
        return None

    if not Path(_CHROMA_DB_PATH).exists():
        return None

    try:
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        client = chromadb.PersistentClient(path=_CHROMA_DB_PATH)
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
        )
        if collection.count() == 0:
            return None
        return collection
    except Exception:
        return None


def _query_collection(
    collection: chromadb.Collection,
    query_text: str,
    where_filter: dict[str, Any] | None = None,
    n_results: int = _N_RESULTS_PER_QUERY,
) -> list[dict[str, Any]]:
    """
    Run a single semantic query against the collection.

    Returns a list of dicts, each with keys: id, document, metadata, distance.
    """
    kwargs: dict[str, Any] = {
        "query_texts": [query_text],
        "n_results": n_results,
    }
    if where_filter is not None:
        kwargs["where"] = where_filter

    try:
        results = collection.query(**kwargs)
    except Exception:
        return []

    items: list[dict[str, Any]] = []
    if not results or not results.get("ids") or not results["ids"][0]:
        return items

    for i, doc_id in enumerate(results["ids"][0]):
        items.append({
            "id": doc_id,
            "document": results["documents"][0][i] if results.get("documents") else "",
            "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
            "distance": results["distances"][0][i] if results.get("distances") else 1.0,
        })

    return items


def _estimate_word_count(text: str) -> int:
    """Fast word count estimate."""
    return len(text.split())


def _deduplicate_and_budget(
    all_results: list[dict[str, Any]],
    max_words: int = MAX_WORD_BUDGET,
) -> list[str]:
    """
    Deduplicate results by chunk id, sort by relevance (lowest distance first,
    with priority boost), and trim to fit the token budget.

    Returns a list of chunk text strings.
    """
    # Deduplicate -- keep the entry with the smallest distance for each id
    seen: dict[str, dict[str, Any]] = {}
    for item in all_results:
        doc_id = item["id"]
        if doc_id not in seen or item["distance"] < seen[doc_id]["distance"]:
            seen[doc_id] = item

    # Sort: high-priority papers get a distance discount so they float up
    priority_discount = {"high": -0.15, "medium": 0.0, "low": 0.10}

    def sort_key(item: dict[str, Any]) -> float:
        p = item.get("metadata", {}).get("priority", "medium")
        discount = priority_discount.get(p, 0.0)
        return item["distance"] + discount

    sorted_items = sorted(seen.values(), key=sort_key)

    # Build output list within word budget
    chunks: list[str] = []
    total_words = 0
    for item in sorted_items:
        doc = item.get("document", "")
        if not doc:
            continue
        wc = _estimate_word_count(doc)
        if total_words + wc > max_words:
            break
        # Prepend a source header so the LLM knows where the chunk is from
        meta = item.get("metadata", {})
        header = (
            f"[Source: {meta.get('title', 'Unknown')} "
            f"({meta.get('authors', 'Unknown')}, {meta.get('year', '?')}) "
            f"| Type: {meta.get('content_type', '?')} "
            f"| Priority: {meta.get('priority', '?')}]"
        )
        formatted = f"{header}\n{doc}"
        chunks.append(formatted)
        total_words += wc

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def retrieve_research_for_user(user_profile: dict[str, Any]) -> list[str]:
    """
    Main retrieval function.  Accepts a user profile dict and returns a list
    of research chunk strings to inject into the LLM context.

    Expected user_profile keys (all optional, with sensible defaults):
        - goal: str              e.g. "strength", "speed", "hypertrophy", ...
        - mode: str              "gym_only", "rehab_only", "both"
        - injuries: list         e.g. ["acl_post_op", "achilles"]
                                 OR list of dicts with "condition" / "region" keys
        - injury_phases: dict    e.g. {"acl_post_op": 2, "achilles": 1}
        - experience: str        "beginner", "intermediate", "advanced"
        - days_per_week: int

    Returns:
        list[str] -- research chunks (with source headers), empty if DB
        is unavailable or empty.
    """

    collection = _get_collection()
    if collection is None:
        # Database empty or not yet created -- return gracefully
        return []

    goal = (user_profile.get("goal") or "general_fitness").lower().strip()
    mode = (user_profile.get("mode") or "gym_only").lower().strip()

    # Normalise injuries: accept list[str] or list[dict]
    raw_injuries = user_profile.get("injuries") or []
    injuries: list[str] = []
    for inj in raw_injuries:
        if isinstance(inj, str):
            injuries.append(inj.lower().strip())
        elif isinstance(inj, dict):
            cond = inj.get("condition", "")
            if cond:
                injuries.append(cond.lower().strip())

    # Gather all results across the four query strategies
    all_results: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Query 1: Condition-specific retrieval (per injury)
    # ------------------------------------------------------------------
    all_condition_tags: list[str] = []

    for injury in injuries:
        mapping = CONDITION_MAP.get(injury)
        if mapping is None:
            continue

        condition_labels = mapping["conditions"]
        region_labels = mapping["regions"]
        all_condition_tags.extend(condition_labels)

        query_text = (
            f"Rehabilitation protocol and exercise selection for "
            f"{injury.replace('_', ' ')} injury affecting the "
            f"{', '.join(region_labels)} region"
        )

        # Filter: any chunk whose conditions field contains at least one
        # of the mapped conditions.  ChromaDB where filters on string
        # fields use $contains for substring match.
        for cond in condition_labels:
            where_filter = {"conditions": {"$contains": cond}}
            results = _query_collection(collection, query_text,
                                        where_filter=where_filter,
                                        n_results=_N_RESULTS_PER_QUERY)
            all_results.extend(results)

    # If any tendinopathy conditions present, also pull general tendinopathy
    if any(c in TENDINOPATHY_CONDITIONS for c in all_condition_tags):
        query_text = (
            "Tendinopathy continuum model loading protocols pain monitoring "
            "isometric eccentric heavy slow resistance"
        )
        where_filter = {"conditions": {"$contains": "general_tendinopathy"}}
        results = _query_collection(collection, query_text,
                                    where_filter=where_filter,
                                    n_results=8)
        all_results.extend(results)

    # ------------------------------------------------------------------
    # Query 2: Goal-specific retrieval
    # ------------------------------------------------------------------
    # Determine which topic list to use.  If mode is rehab_only or both,
    # we blend goal and mode topics.
    goal_topics = GOAL_TOPIC_MAP.get(goal, GOAL_TOPIC_MAP["general_fitness"])
    if mode in ("rehab_only", "both") and mode != goal:
        mode_topics = GOAL_TOPIC_MAP.get(mode, [])
        # Merge, preserving order (goal topics first)
        combined = list(dict.fromkeys(goal_topics + mode_topics))
        goal_topics = combined

    for topic in goal_topics:
        query_text = (
            f"Evidence-based guidelines for {topic.replace('_', ' ')} "
            f"in {goal.replace('_', ' ')} training"
        )
        where_filter = {"topics": {"$contains": topic}}
        results = _query_collection(collection, query_text,
                                    where_filter=where_filter,
                                    n_results=8)
        all_results.extend(results)

    # ------------------------------------------------------------------
    # Query 3: Gate criteria (for users with injuries in rehab/both modes)
    # ------------------------------------------------------------------
    if injuries and mode in ("rehab_only", "both"):
        query_text = (
            "Return to sport criteria and discharge gates for "
            "rehabilitation progression"
        )
        where_filter = {"topics": {"$contains": "gate_criteria"}}
        results = _query_collection(collection, query_text,
                                    where_filter=where_filter,
                                    n_results=8)
        all_results.extend(results)

        # Also grab return-to-sport material
        query_text_rts = (
            "Return to sport decision making after injury "
            "rehabilitation and readiness"
        )
        where_filter_rts = {"topics": {"$contains": "return_to_sport"}}
        results_rts = _query_collection(collection, query_text_rts,
                                        where_filter=where_filter_rts,
                                        n_results=6)
        all_results.extend(results_rts)

    # ------------------------------------------------------------------
    # Query 4: High-priority foundational papers
    # ------------------------------------------------------------------
    # Always include some high-priority general principles regardless of
    # specific goal/injury, so the LLM has broad evidence context.
    query_text_general = (
        "General rehabilitation principles optimal loading tissue healing "
        "pain monitoring and injury management"
    )
    where_filter_hp = {"priority": "high"}
    results_hp = _query_collection(collection, query_text_general,
                                   where_filter=where_filter_hp,
                                   n_results=10)
    all_results.extend(results_hp)

    # ------------------------------------------------------------------
    # Deduplicate, rank, and trim to budget
    # ------------------------------------------------------------------
    chunks = _deduplicate_and_budget(all_results)

    total_words = sum(_estimate_word_count(c) for c in chunks)
    approx_tokens = int(total_words / _APPROX_WORDS_PER_TOKEN)
    print(f"  [retrieve] {len(chunks)} chunks (~{total_words} words, ~{approx_tokens} tokens)")

    return chunks


# ---------------------------------------------------------------------------
# Quick test / CLI helper
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Example: retrieve research for a user with an ACL injury doing strength
    sample_profile: dict[str, Any] = {
        "goal": "strength",
        "mode": "both",
        "injuries": ["acl_post_op"],
        "injury_phases": {"acl_post_op": 2},
        "experience": "intermediate",
        "days_per_week": 4,
    }

    print("Retrieving research for sample profile...")
    print(f"  Goal:     {sample_profile['goal']}")
    print(f"  Mode:     {sample_profile['mode']}")
    print(f"  Injuries: {sample_profile['injuries']}")
    print()

    results = retrieve_research_for_user(sample_profile)

    if not results:
        print("No results returned (database may be empty or not yet ingested).")
    else:
        total_words = sum(len(c.split()) for c in results)
        print(f"Retrieved {len(results)} chunks (~{total_words} words, "
              f"~{int(total_words / _APPROX_WORDS_PER_TOKEN)} tokens)")
        print()
        # Print first chunk as preview
        print("--- First chunk preview ---")
        print(results[0][:500])
        print("...")
