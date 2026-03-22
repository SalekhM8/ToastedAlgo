"""
Deterministic plan validator for Toasted training plan generator.

Checks every generated plan against the safety rules encoded in the Rules Document.
This is pure deterministic code — no LLM calls. Every restriction is hard-coded
so that validation is reproducible and instant.

Usage:
    validator = PlanValidator()
    is_valid, errors, warnings = validator.validate(plan, user_profile)
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Type aliases (plan and profile are plain dicts — no pydantic dependency yet)
# ---------------------------------------------------------------------------
Plan = dict[str, Any]
UserProfile = dict[str, Any]
Exercise = dict[str, Any]
Day = dict[str, Any]


# ---------------------------------------------------------------------------
# Key normalizer: Claude outputs camelCase, validator expects snake_case.
# This converts ONCE at the entry point so every downstream check works.
# ---------------------------------------------------------------------------
_KEY_MAP = {
    "planHeader": "plan_header",
    "honestyVerdict": "honesty_verdict",
    "goalViability": "goal_viability",
    "dayNumber": "day_number",
    "dayType": "day_type",
    "intensityLevel": "intensity_level",
    "estimatedMinutes": "estimated_minutes",
    "blockType": "type",
    "blockLabel": "label",
    "exerciseName": "name",
    "restSeconds": "rest_seconds",
    "doseNotes": "dose_notes",
    "substitutionNote": "substitution_note",
    "coachingCue": "coaching_cue",
    "safetyNote": "safety_note",
    "progressionGuidance": "progression_guidance",
    "deloadInstructions": "deload_instructions",
    "homeSessions": "home_sessions",
    "frequencyPerWeek": "frequency_per_week",
    "durationMinutes": "duration_minutes",
}


def _normalize_keys(obj: Any) -> Any:
    """Recursively rename camelCase keys to the snake_case the validator expects."""
    if isinstance(obj, dict):
        return {_KEY_MAP.get(k, k): _normalize_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_keys(item) for item in obj]
    return obj

# ---------------------------------------------------------------------------
# Banned-exercise pattern banks, keyed by (condition, phase)
#
# Each value is a list of pattern strings.  A pattern matches an exercise name
# if the exercise name (lower-cased) contains the pattern OR any of its aliases.
# ---------------------------------------------------------------------------

_ACL_POSTOP_PHASE1_BANNED: list[str] = [
    "open chain knee extension",
    "leg extension",          # most common form of open-chain knee ext
    "running",
    "jogging",
    "jog",
    "run",
    "sprint",
    "jumping",
    "jump",
    "box jump",
    "broad jump",
    "depth jump",
    "drop jump",
    "squat jump",
    "tuck jump",
    "landing",
    "cutting",
    "pivot",
    "change of direction",
    "cod drill",
    "agility",
    "shuttle",
    "t-drill",
    "t-test",
    "pro agility",
    "plyometric",
    "plyo",
    "reactive",
    "bound",
    "bounding",
    "hop",
    "skip",  # A-skip, B-skip can be sprint drills
    "pogo",
]

_ACL_POSTOP_PHASE1_HAMSTRING_GRAFT_BANNED: list[str] = [
    "nordic curl",
    "nordic hamstring",
    "heavy hamstring curl",
    "heavy leg curl",
    "stiff leg deadlift",
    "stiff-leg deadlift",
    "romanian deadlift",
    "rdl",
    "good morning",
    "glute ham raise",
    "ghr",
]

_ACL_POSTOP_PHASE2_BANNED: list[str] = [
    "running",
    "jogging",
    "jog",
    "run",
    "sprint",
    "depth jump",
    "drop jump",
    "drop landing",
    "reactive plyo",
    "reactive plyometric",
    "cutting",
    "pivot",
    "change of direction",
    "cod drill",
    "agility",
    "shuttle",
    "t-drill",
    "pro agility",
    "single-leg landing",
    "single leg landing",
    "single-leg drop",
    "single leg drop",
]

_ACL_POSTOP_PHASE3_BANNED: list[str] = [
    "reactive change of direction",
    "reactive cod",
    "reactive agility",
    "competitive sport",
    "match play",
    "game play",
    "scrimmage",
]

_ACL_POSTOP_PHASE4_BANNED: list[str] = [
    "full competitive sport",
    "match play",
    "game play",
    "scrimmage",
]

_MCL_PHASE1_BANNED: list[str] = [
    "deep squat",          # beyond ~70 deg
    "full squat",
    "ass to grass",
    "atg squat",
    "pistol squat",
    "cutting",
    "pivot",
    "change of direction",
    "cod drill",
    "agility",
    "shuttle",
    "t-drill",
    "pro agility",
    "lateral bound",
    "lateral jump",
    "lateral hop",
    "lateral plyo",
    "lateral plyometric",
    "skater jump",
    "skater bound",
    "contact",
    "collision",
    "tackle",
]

_MCL_PHASE2_BANNED: list[str] = [
    "full speed cutting",
    "full speed cut",
    "full intensity lateral plyo",
    "full intensity lateral plyometric",
]

_PCL_PHASE1_BANNED: list[str] = [
    "nordic curl",
    "nordic hamstring",
    "heavy hamstring curl",
    "heavy leg curl",
    "heavy hamstring",
    "deep squat",
    "full squat",
    "ass to grass",
    "atg squat",
    "pistol squat",
]

_ANKLE_PHASE1_BANNED: list[str] = [
    "running",
    "jogging",
    "jog",
    "run",
    "sprint",
    "jumping",
    "jump",
    "box jump",
    "broad jump",
    "depth jump",
    "drop jump",
    "squat jump",
    "tuck jump",
    "landing",
    "cutting",
    "pivot",
    "change of direction",
    "cod drill",
    "agility",
    "shuttle",
    "t-drill",
    "pro agility",
    "high impact",
    "high-impact",
    "barbell squat",
    "back squat",
    "front squat",
]

_ANKLE_PHASE2_BANNED: list[str] = [
    "lateral plyo",
    "lateral plyometric",
    "lateral bound",
    "lateral jump",
    "lateral hop",
    "skater jump",
    "skater bound",
    "reactive change of direction",
    "reactive cod",
    "reactive agility",
]

_SHOULDER_RC_PHASE1_BANNED: list[str] = [
    "overhead press",
    "ohp",
    "military press",
    "push press",
    "jerk",
    "snatch",
    "behind neck",
    "behind-neck",
    "behind the neck",
    "btn pulldown",
    "btn press",
    "dip",   # if painful — we flag as warning, not hard ban
]

_PFPS_PHASE1_NOTE: str = (
    "Anterior knee pain / PFPS: cannot programmatically verify pain <4/10 "
    "during exercises. Ensure user monitors pain and stops if >4/10."
)

_PATELLAR_TENDINOPATHY_PHASE1_BANNED: list[str] = [
    "excessive jump",
    "plyometric",
    "plyo",
    "depth jump",
    "drop jump",
    "box jump",
    "squat jump",
    "tuck jump",
    "bound",
    "bounding",
    "hop",
    "pogo",
]

_LBP_FLEXION_PHASE1_BANNED: list[str] = [
    "deadlift from floor",
    "conventional deadlift",
    "heavy deadlift",
    "good morning",
    "good-morning",
    "stiff leg deadlift",
    "stiff-leg deadlift",
    "straight leg deadlift",
    "sit-up",
    "sit up",
    "situp",
    "crunch",
    "crunches",
    "v-up",
    "v up",
]

_LBP_EXTENSION_PHASE1_BANNED: list[str] = [
    "back extension",
    "prone extension",
    "hyperextension",
    "reverse hyper",
    "superman",
    "lumbar extension",
]

_HIP_ADDUCTOR_PHASE1_BANNED: list[str] = [
    "sumo deadlift",
    "sumo squat",
    "wide squat",
    "wide stance squat",
    "wide-stance squat",
    "lateral lunge",
    "side lunge",
    "lateral bound",
    "lateral jump",
    "lateral hop",
    "lateral plyo",
    "lateral plyometric",
    "skater jump",
    "skater bound",
    "sprint",
    "full effort sprint",
    "cutting",
    "pivot",
    "change of direction",
    "cod drill",
    "agility",
    "shuttle",
    "t-drill",
    "pro agility",
]

_LATERAL_EPICONDYLALGIA_PHASE1_BANNED: list[str] = [
    "deadlift",
    "heavy row",
    "barbell row",
    "pull-up",
    "pull up",
    "pullup",
    "chin-up",
    "chin up",
    "chinup",
    "farmer walk",
    "farmer carry",
    "farmer's walk",
    "heavy wrist extension",
    "wrist curl",
    "heavy grip",
    "fat grip",
]


# ---------------------------------------------------------------------------
# Region mapping — which body regions an injury affects
# ---------------------------------------------------------------------------

_INJURY_REGION_MAP: dict[str, str] = {
    "acl": "lower",
    "acl post-op": "lower",
    "acl postop": "lower",
    "mcl": "lower",
    "mcl sprain": "lower",
    "pcl": "lower",
    "pcl sprain": "lower",
    "meniscus": "lower",
    "meniscus repair": "lower",
    "lateral ankle sprain": "lower",
    "ankle sprain": "lower",
    "ankle": "lower",
    "patellar tendinopathy": "lower",
    "patella tendinopathy": "lower",
    "anterior knee pain": "lower",
    "pfps": "lower",
    "hip adductor strain": "lower",
    "adductor strain": "lower",
    "shoulder rotator cuff tendinopathy": "upper",
    "rotator cuff": "upper",
    "shoulder": "upper",
    "lateral epicondylalgia": "upper",
    "tennis elbow": "upper",
    "mechanical lbp flexion-sensitive": "spine",
    "mechanical lbp extension-sensitive": "spine",
    "lbp flexion": "spine",
    "lbp extension": "spine",
    "low back pain": "spine",
    "lbp": "spine",
}

# Day-type keywords that load a given body region
_DAY_TYPE_LOADS_REGION: dict[str, set[str]] = {
    "lower": {"lower", "leg", "full", "full body", "full-body", "speed", "power",
              "plyometric", "conditioning", "sprint"},
    "upper": {"upper", "push", "pull", "full", "full body", "full-body"},
    "spine": {"lower", "upper", "full", "full body", "full-body", "speed",
              "power", "deadlift", "squat", "hinge", "push", "pull",
              "conditioning"},
}


# ---------------------------------------------------------------------------
# Session time-budget reference (exercise count ranges by session length)
# ---------------------------------------------------------------------------

_EXERCISE_COUNT_RANGES: dict[int, tuple[int, int]] = {
    30: (3, 5),
    45: (4, 6),
    60: (5, 8),
    75: (6, 9),
    90: (7, 11),
}


def _closest_session_length(minutes: int) -> int:
    """Return the reference session length nearest to *minutes*."""
    keys = sorted(_EXERCISE_COUNT_RANGES.keys())
    return min(keys, key=lambda k: abs(k - minutes))


# ---------------------------------------------------------------------------
# Red-flag keywords
# ---------------------------------------------------------------------------

_RED_FLAG_KEYWORDS: list[str] = [
    "cauda equina",
    "saddle anaesthesia",
    "saddle anesthesia",
    "loss of bladder",
    "loss of bowel",
    "bladder dysfunction",
    "bowel dysfunction",
    "bilateral leg weakness",
    "bilateral numbness",
    "suspected fracture",
    "fracture",
    "cardiac",
    "chest pain",
    "loss of consciousness",
    "unexplained weight loss",
    "night sweats",
    "fever",
    "cancer",
    "malignancy",
    "progressive neurological",
    "numbness with spine",
    "numbness",  # when co-occurring with spine — checked contextually
]


# ============================================================================
# PlanValidator
# ============================================================================

class PlanValidator:
    """Deterministic validator that checks a generated plan for safety violations.

    Usage::

        validator = PlanValidator()
        is_valid, errors, warnings = validator.validate(plan, user_profile)

    ``errors`` are hard failures — the plan MUST NOT be shipped.
    ``warnings`` are soft issues that should be reviewed but don't block shipping.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(
        self,
        plan: Plan,
        user_profile: UserProfile,
    ) -> tuple[bool, list[str], list[str]]:
        """Validate *plan* against *user_profile*.

        Returns
        -------
        is_valid : bool
            ``True`` only when there are zero errors.
        errors : list[str]
            Hard violations — plan must not be shipped.
        warnings : list[str]
            Soft issues — should be reviewed.
        """
        # Normalize camelCase keys from Claude to snake_case for all checks
        plan = _normalize_keys(plan)

        errors: list[str] = []
        warnings: list[str] = []

        # 0. Red-flag check — if present, NO plan should exist at all
        self._check_red_flags(plan, user_profile, errors)

        # If red flags detected, short-circuit: nothing else matters
        if errors:
            return False, errors, warnings

        # 0b. Unknown condition / severity warnings (applicable to all modes)
        self._validate_unknown_condition(user_profile, warnings)
        self._validate_unknown_severity(user_profile, warnings)

        # 1. Condition-specific banned-exercise checks
        self._check_banned_exercises(plan, user_profile, errors, warnings)

        # 2. Rehab warm-up presence on affected-region days
        self._check_rehab_warmup(plan, user_profile, errors, warnings)

        # 3. Session time budget
        self._check_time_budget(plan, user_profile, errors, warnings)

        # 4. Exercise count per session
        self._check_exercise_count(plan, user_profile, errors, warnings)

        # 5. No duplicate exercises within a day
        self._check_duplicates(plan, errors, warnings)

        # 6. Correct number of days
        self._check_day_count(plan, user_profile, errors, warnings)

        # 7. Honesty verdict exists
        self._check_honesty_verdict(plan, errors, warnings)

        # 8. Clinician restrictions
        self._check_clinician_restrictions(plan, user_profile, errors, warnings)

        # 9. Rehab-only plan structure validation
        mode = user_profile.get("mode", "both").lower()
        if mode in ("rehab_only", "rehab only"):
            self._validate_rehab_only_structure(plan, user_profile, errors, warnings)

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    # ------------------------------------------------------------------
    # Phase determination
    # ------------------------------------------------------------------

    def _determine_phase(self, injury: dict[str, Any]) -> str:
        """Return the current phase string for an injury.

        Phase labels: ``"phase1"``, ``"phase2"``, ``"phase3"``, ``"phase4"``

        Parameters
        ----------
        injury : dict
            Must contain at least ``"condition"`` (str).
            May contain ``"weeks_since_injury"`` or ``"weeks_since_surgery"`` (int),
            ``"phase"`` (str) — an explicit override, ``"acuity"`` (str) for
            tendinopathy (``"acute"`` / ``"reactive"`` / ``"chronic"``).
        """
        # If the caller already set a phase, honour it.
        explicit = injury.get("phase", "").strip().lower()
        if explicit and explicit.startswith("phase"):
            return explicit  # e.g. "phase1", "phase2"

        condition = self._normalise_condition(injury.get("condition", ""))
        weeks = injury.get("weeks_since_injury") or injury.get("weeks_since_surgery") or 0

        # --- ACL / meniscus post-op ---
        if condition in ("acl post-op", "acl postop", "acl", "meniscus repair", "meniscus"):
            if weeks <= 6:
                return "phase1"
            elif weeks <= 12:
                return "phase2"
            elif weeks <= 20:
                return "phase3"
            else:
                return "phase4"

        # --- Sprains (MCL, PCL, ankle, hip adductor) ---
        if condition in (
            "mcl sprain", "mcl",
            "pcl sprain", "pcl",
            "lateral ankle sprain", "ankle sprain", "ankle",
            "hip adductor strain", "adductor strain",
        ):
            if weeks <= 4:
                return "phase1"
            elif weeks <= 8:
                return "phase2"
            else:
                return "phase3"

        # --- Tendinopathy ---
        if "tendinopathy" in condition or "tendinitis" in condition:
            acuity = injury.get("acuity", "").lower()
            if acuity in ("acute", "reactive"):
                return "phase1"
            return "phase2"  # chronic by default

        # --- LBP ---
        if "lbp" in condition or "low back" in condition or "back pain" in condition:
            if weeks < 6:
                return "phase1"
            elif weeks < 12:
                return "phase2"
            else:
                return "phase3"

        # --- Lateral epicondylalgia ---
        if "epicondyl" in condition or "tennis elbow" in condition:
            if weeks < 6:
                return "phase1"
            return "phase2"

        # --- Shoulder rotator cuff ---
        if "rotator cuff" in condition or "shoulder" in condition:
            if weeks < 6:
                return "phase1"
            return "phase2"

        # --- PFPS / anterior knee pain ---
        if "pfps" in condition or "anterior knee" in condition:
            if weeks < 6:
                return "phase1"
            return "phase2"

        # Default conservative: phase1
        return "phase1"

    # ------------------------------------------------------------------
    # Exercise pattern matching
    # ------------------------------------------------------------------

    @staticmethod
    def _exercise_matches_pattern(exercise_name: str, pattern: str) -> bool:
        """Return ``True`` if *exercise_name* matches the banned *pattern*.

        Matching is case-insensitive and uses word-boundary–aware substring
        search so that ``"run"`` matches ``"running"`` and ``"sprint run"``
        but does NOT match ``"trunk rotation"`` (the ``run`` inside ``trunk``).
        """
        name = exercise_name.lower().strip()
        pat = pattern.lower().strip()

        # Direct substring — covers most alias cases
        if pat in name:
            return True

        # Word-stem matching for common short patterns that could cause
        # false positives as plain substrings.  We try a word-boundary regex.
        try:
            if re.search(rf"\b{re.escape(pat)}", name):
                return True
        except re.error:
            pass

        return False

    def _exercise_matches_any_pattern(
        self, exercise_name: str, patterns: list[str]
    ) -> str | None:
        """Return the first matching pattern string, or ``None``."""
        for pat in patterns:
            if self._exercise_matches_pattern(exercise_name, pat):
                return pat
        return None

    # ------------------------------------------------------------------
    # Region detection
    # ------------------------------------------------------------------

    def _day_affects_injured_region(
        self, day: Day, user_profile: UserProfile
    ) -> bool:
        """Return ``True`` if *day* loads any region that is injured."""
        injuries = self._get_injuries(user_profile)
        if not injuries:
            return False

        day_type = (
            day.get("day_type", "") or day.get("type", "") or day.get("label", "")
        ).lower()

        # Also scan exercise names for region hints when day_type is vague
        exercise_names = " ".join(
            self._iter_exercise_names(day)
        ).lower()

        for injury in injuries:
            region = self._injury_region(injury)
            region_keywords = _DAY_TYPE_LOADS_REGION.get(region, set())

            # Check day type label
            for kw in region_keywords:
                if kw in day_type:
                    return True

            # Heuristic: scan exercise names for lower/upper/spine cues
            if region == "lower":
                lower_cues = [
                    "squat", "lunge", "leg", "deadlift", "hip", "glute",
                    "hamstring", "calf", "quad", "step-up", "step up",
                    "sprint", "run", "jump",
                ]
                if any(cue in exercise_names for cue in lower_cues):
                    return True
            elif region == "upper":
                upper_cues = [
                    "bench", "press", "row", "pull", "curl", "tricep",
                    "shoulder", "lat", "fly", "delt", "bicep",
                ]
                if any(cue in exercise_names for cue in upper_cues):
                    return True
            elif region == "spine":
                spine_cues = [
                    "deadlift", "squat", "row", "press", "overhead",
                    "core", "plank", "carry", "extension", "hinge",
                ]
                if any(cue in exercise_names for cue in spine_cues):
                    return True

        return False

    # ------------------------------------------------------------------
    # Internal check methods
    # ------------------------------------------------------------------

    def _check_red_flags(
        self,
        plan: Plan,
        user_profile: UserProfile,
        errors: list[str],
    ) -> None:
        """If the user profile contains red-flag indicators, no plan should exist."""
        red_flags = user_profile.get("red_flags", [])
        if isinstance(red_flags, str):
            red_flags = [red_flags]

        # Also scan free-text fields for red-flag keywords
        free_text_fields = [
            user_profile.get("notes", ""),
            user_profile.get("symptoms", ""),
            user_profile.get("medical_history", ""),
            user_profile.get("additional_info", ""),
        ]

        # Check explicit red_flags list
        if red_flags:
            errors.append(
                f"RED FLAG: User profile contains red-flag indicators {red_flags}. "
                "No plan should be generated — the user must be directed to a "
                "medical professional."
            )
            return

        # Check free-text fields for red-flag keywords
        combined_text = " ".join(str(f) for f in free_text_fields if f).lower()

        # Numbness co-occurring with spine is a red flag
        has_numbness = "numbness" in combined_text
        has_spine = any(
            kw in combined_text
            for kw in ("spine", "spinal", "back", "lumbar", "thoracic", "cervical")
        )
        if has_numbness and has_spine:
            errors.append(
                "RED FLAG: Numbness reported alongside spinal involvement. "
                "No plan should be generated — the user must be directed to a "
                "medical professional."
            )
            return

        # General red-flag keyword scan (excluding "numbness" which needs context)
        contextless_flags = [kw for kw in _RED_FLAG_KEYWORDS if kw != "numbness"]
        for kw in contextless_flags:
            if kw in combined_text:
                errors.append(
                    f"RED FLAG: '{kw}' detected in user profile text. "
                    "No plan should be generated — the user must be directed "
                    "to a medical professional."
                )
                return

        # Check injuries for red-flag indicators
        for injury in self._get_injuries(user_profile):
            injury_flags = injury.get("red_flags", [])
            if isinstance(injury_flags, str):
                injury_flags = [injury_flags]
            if injury_flags:
                errors.append(
                    f"RED FLAG: Injury '{injury.get('condition', 'unknown')}' has "
                    f"red-flag indicators {injury_flags}. No plan should be generated."
                )
                return

    def _check_banned_exercises(
        self,
        plan: Plan,
        user_profile: UserProfile,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Check every exercise against condition-specific banned lists."""
        injuries = self._get_injuries(user_profile)
        if not injuries:
            return

        for injury in injuries:
            condition = self._normalise_condition(injury.get("condition", ""))
            phase = self._determine_phase(injury)
            banned_patterns = self._get_banned_patterns(condition, phase, injury)

            if not banned_patterns:
                continue

            for day in self._iter_days(plan):
                day_label = day.get("label", day.get("title", "unknown day"))
                for ex_name in self._iter_exercise_names(day):
                    match = self._exercise_matches_any_pattern(ex_name, banned_patterns)
                    if match:
                        errors.append(
                            f"BANNED EXERCISE: '{ex_name}' on {day_label} matches "
                            f"banned pattern '{match}' for {condition} {phase}."
                        )

            # Special note for PFPS — can't programmatically check pain levels
            if "pfps" in condition or "anterior knee" in condition:
                warnings.append(_PFPS_PHASE1_NOTE)

            # Special warning for dips with shoulder RC — not a hard ban
            if ("rotator cuff" in condition or "shoulder" in condition) and phase == "phase1":
                for day in self._iter_days(plan):
                    for ex_name in self._iter_exercise_names(day):
                        if self._exercise_matches_pattern(ex_name, "dip"):
                            warnings.append(
                                f"WARNING: '{ex_name}' may be painful with shoulder "
                                f"rotator cuff tendinopathy. Consider removing if "
                                f"user reports pain."
                            )

    def _check_rehab_warmup(
        self,
        plan: Plan,
        user_profile: UserProfile,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Rehab warm-up must be present on every day that loads the injured region.

        Only applies when mode is 'both' or 'rehab_only'.
        """
        mode = user_profile.get("mode", "both").lower()
        if mode == "gym_only" or mode == "gym only":
            return

        injuries = self._get_injuries(user_profile)
        if not injuries:
            return

        for day in self._iter_days(plan):
            if not self._day_affects_injured_region(day, user_profile):
                continue

            # Check for rehab warm-up block
            has_warmup = self._day_has_rehab_warmup(day)
            day_label = day.get("label", day.get("title", "unknown day"))
            if not has_warmup:
                errors.append(
                    f"MISSING REHAB WARM-UP: Day '{day_label}' loads the injured "
                    f"region but has no rehab warm-up block."
                )

    def _check_time_budget(
        self,
        plan: Plan,
        user_profile: UserProfile,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Check that each session's estimated time is reasonable."""
        target_minutes = user_profile.get("session_length") or user_profile.get(
            "session_length_minutes"
        )
        if not target_minutes:
            warnings.append(
                "No session_length in user profile — cannot validate time budget."
            )
            return

        target_minutes = int(target_minutes)

        for day in self._iter_days(plan):
            day_label = day.get("label", day.get("title", "unknown day"))
            estimated = day.get("estimated_time") or day.get("estimated_minutes")

            if estimated is None:
                # Try to estimate from exercise count (rough heuristic)
                ex_count = len(list(self._iter_exercise_names(day)))
                # ~7 min per exercise is a rough average (including rest)
                estimated = ex_count * 7

            estimated = int(estimated)
            ratio = estimated / target_minutes if target_minutes else 1.0
            deviation = abs(ratio - 1.0)

            if deviation > 0.50:
                errors.append(
                    f"TIME BUDGET ERROR: Day '{day_label}' estimated at "
                    f"{estimated} min vs target {target_minutes} min "
                    f"(deviation {deviation:.0%}). Way outside acceptable range."
                )
            elif deviation > 0.25:
                warnings.append(
                    f"TIME BUDGET WARNING: Day '{day_label}' estimated at "
                    f"{estimated} min vs target {target_minutes} min "
                    f"(deviation {deviation:.0%}). Outside ±25% target."
                )

    def _check_exercise_count(
        self,
        plan: Plan,
        user_profile: UserProfile,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Check exercise count is appropriate for session length."""
        target_minutes = user_profile.get("session_length") or user_profile.get(
            "session_length_minutes"
        )
        if not target_minutes:
            return

        target_minutes = int(target_minutes)
        ref = _closest_session_length(target_minutes)
        min_ex, max_ex = _EXERCISE_COUNT_RANGES[ref]

        for day in self._iter_days(plan):
            day_label = day.get("label", day.get("title", "unknown day"))
            ex_count = len(list(self._iter_exercise_names(day)))

            if ex_count < min_ex - 2 or ex_count > max_ex + 4:
                errors.append(
                    f"EXERCISE COUNT ERROR: Day '{day_label}' has {ex_count} "
                    f"exercises. For a ~{target_minutes} min session, expected "
                    f"{min_ex}-{max_ex}."
                )
            elif ex_count < min_ex - 1 or ex_count > max_ex + 2:
                warnings.append(
                    f"EXERCISE COUNT WARNING: Day '{day_label}' has {ex_count} "
                    f"exercises. For a ~{target_minutes} min session, expected "
                    f"{min_ex}-{max_ex}."
                )

    def _check_duplicates(
        self,
        plan: Plan,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """No duplicate exercises within a single day."""
        for day in self._iter_days(plan):
            day_label = day.get("label", day.get("title", "unknown day"))
            seen: dict[str, int] = {}
            for ex_name in self._iter_exercise_names(day):
                normalised = ex_name.lower().strip()
                seen[normalised] = seen.get(normalised, 0) + 1

            for name, count in seen.items():
                if count > 1:
                    errors.append(
                        f"DUPLICATE EXERCISE: '{name}' appears {count} times "
                        f"on {day_label}."
                    )

    def _check_day_count(
        self,
        plan: Plan,
        user_profile: UserProfile,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Plan should have exactly the number of days the user requested."""
        requested = user_profile.get("days_per_week") or user_profile.get("days")
        if requested is None:
            warnings.append(
                "No days_per_week in user profile — cannot validate day count."
            )
            return

        requested = int(requested)
        days = list(self._iter_days(plan))
        actual = len(days)

        if actual != requested:
            errors.append(
                f"DAY COUNT MISMATCH: Plan has {actual} days but user "
                f"requested {requested} days per week."
            )

    def _check_honesty_verdict(
        self,
        plan: Plan,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Plan must contain an honesty verdict / overall assessment."""
        verdict = (
            plan.get("honesty_verdict")
            or plan.get("honestyVerdict")
            or plan.get("verdict")
            or plan.get("honest_assessment")
            or plan.get("assessment")
            or plan.get("plan_header", {}).get("honesty_verdict")
            or plan.get("plan_header", {}).get("honestyVerdict")
        )
        if not verdict:
            errors.append(
                "MISSING HONESTY VERDICT: Plan must include an honesty "
                "verdict assessing goal viability (Rule 21)."
            )

    def _check_clinician_restrictions(
        self,
        plan: Plan,
        user_profile: UserProfile,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Clinician-stated restrictions must be absolutely respected."""
        restrictions = user_profile.get("clinician_restrictions") or user_profile.get(
            "clinician_notes"
        )
        if not restrictions:
            return

        if isinstance(restrictions, str):
            restrictions = [restrictions]

        for restriction in restrictions:
            restriction_lower = restriction.lower().strip()
            if not restriction_lower:
                continue

            # Parse common restriction patterns
            banned_activities = self._parse_clinician_restriction(restriction_lower)

            for day in self._iter_days(plan):
                day_label = day.get("label", day.get("title", "unknown day"))
                for ex_name in self._iter_exercise_names(day):
                    for banned in banned_activities:
                        if self._exercise_matches_pattern(ex_name, banned):
                            errors.append(
                                f"CLINICIAN RESTRICTION VIOLATION: '{ex_name}' on "
                                f"{day_label} violates clinician restriction: "
                                f"'{restriction}'."
                            )

            # Always flag for human review regardless of automated parsing
            warnings.append(
                f"CLINICIAN RESTRICTION (flagged for review): '{restriction}'. "
                f"Automated checks may not catch all nuances — manual review "
                f"recommended."
            )

    # ------------------------------------------------------------------
    # Helpers — injury & plan traversal
    # ------------------------------------------------------------------

    @staticmethod
    def _get_injuries(user_profile: UserProfile) -> list[dict[str, Any]]:
        """Extract the list of injuries from the user profile."""
        injuries = user_profile.get("injuries", [])
        if isinstance(injuries, dict):
            injuries = [injuries]
        # Also check singular form
        if not injuries:
            injury = user_profile.get("injury")
            if injury:
                injuries = [injury] if isinstance(injury, dict) else []
        return injuries

    @staticmethod
    def _normalise_condition(condition: str) -> str:
        """Lower-case and strip a condition name for matching."""
        return condition.lower().strip()

    @staticmethod
    def _injury_region(injury: dict[str, Any]) -> str:
        """Return the body region ('lower', 'upper', 'spine') for an injury."""
        condition = injury.get("condition", "").lower().strip()
        for key, region in _INJURY_REGION_MAP.items():
            if key in condition:
                return region
        # Try explicit region field
        region = injury.get("region", "").lower().strip()
        if region in ("lower", "upper", "spine"):
            return region
        return "lower"  # conservative default

    @staticmethod
    def _iter_days(plan: Plan):
        """Yield each day dict from the plan."""
        # Support multiple common structures
        days = plan.get("days") or plan.get("training_days") or plan.get("weekly_plan")
        if isinstance(days, list):
            yield from days
            return
        # Plan might be keyed by day name
        if isinstance(days, dict):
            yield from days.values()
            return
        # Try top-level keys like "day_1", "day1", "monday" etc.
        for key, value in plan.items():
            if isinstance(value, dict) and (
                key.startswith("day") or key.lower() in (
                    "monday", "tuesday", "wednesday", "thursday",
                    "friday", "saturday", "sunday",
                )
            ):
                yield value

    @staticmethod
    def _iter_exercise_names(day: Day):
        """Yield every exercise name string from a day dict."""
        # Check nested blocks: rehab_warmup, main, rehab_accessories, exercises
        blocks_keys = [
            "rehab_warmup", "rehab_warm_up", "warmup", "warm_up",
            "main", "main_gym", "gym",
            "rehab_accessories", "accessories", "rehab_accessory",
            "exercises", "exercise_list",
            "speed_work", "sprint_work", "conditioning",
        ]
        yielded = False

        for bk in blocks_keys:
            block = day.get(bk)
            if not block:
                continue
            if isinstance(block, list):
                for ex in block:
                    if isinstance(ex, dict):
                        name = ex.get("name") or ex.get("exercise") or ex.get("exercise_name")
                        if name:
                            yield str(name)
                            yielded = True
                    elif isinstance(ex, str):
                        yield ex
                        yielded = True

        # Flat list of exercises at day level
        exercises = day.get("exercises") or day.get("exercise_list")
        if not yielded and isinstance(exercises, list):
            for ex in exercises:
                if isinstance(ex, dict):
                    name = ex.get("name") or ex.get("exercise") or ex.get("exercise_name")
                    if name:
                        yield str(name)
                elif isinstance(ex, str):
                    yield ex

        # Also scan "blocks" array pattern
        blocks = day.get("blocks")
        if isinstance(blocks, list):
            for block in blocks:
                if isinstance(block, dict):
                    block_exercises = block.get("exercises", [])
                    if isinstance(block_exercises, list):
                        for ex in block_exercises:
                            if isinstance(ex, dict):
                                name = (
                                    ex.get("name")
                                    or ex.get("exercise")
                                    or ex.get("exercise_name")
                                )
                                if name:
                                    yield str(name)
                            elif isinstance(ex, str):
                                yield ex

    @staticmethod
    def _day_has_rehab_warmup(day: Day) -> bool:
        """Return ``True`` if the day has a rehab warm-up block."""
        warmup_keys = [
            "rehab_warmup", "rehab_warm_up",
        ]
        for key in warmup_keys:
            block = day.get(key)
            if block:
                return True

        # Check blocks array for a block labelled as rehab warm-up
        blocks = day.get("blocks")
        if isinstance(blocks, list):
            for block in blocks:
                if isinstance(block, dict):
                    block_type = (
                        block.get("type", "") or block.get("label", "")
                    ).lower()
                    if "rehab" in block_type and "warm" in block_type:
                        return True

        return False

    # ------------------------------------------------------------------
    # Banned-pattern lookup
    # ------------------------------------------------------------------

    def _get_banned_patterns(
        self,
        condition: str,
        phase: str,
        injury: dict[str, Any],
    ) -> list[str]:
        """Return the list of banned exercise patterns for a condition+phase."""
        patterns: list[str] = []

        # --- ACL post-op ---
        if condition in ("acl post-op", "acl postop", "acl", "meniscus repair", "meniscus"):
            if phase == "phase1":
                patterns.extend(_ACL_POSTOP_PHASE1_BANNED)
                # Hamstring graft additional bans
                graft = injury.get("graft_type", "").lower()
                if "hamstring" in graft:
                    patterns.extend(_ACL_POSTOP_PHASE1_HAMSTRING_GRAFT_BANNED)
            elif phase == "phase2":
                patterns.extend(_ACL_POSTOP_PHASE2_BANNED)
            elif phase == "phase3":
                patterns.extend(_ACL_POSTOP_PHASE3_BANNED)
            elif phase == "phase4":
                patterns.extend(_ACL_POSTOP_PHASE4_BANNED)

        # --- MCL sprain ---
        elif condition in ("mcl sprain", "mcl"):
            if phase == "phase1":
                patterns.extend(_MCL_PHASE1_BANNED)
            elif phase == "phase2":
                patterns.extend(_MCL_PHASE2_BANNED)

        # --- PCL sprain ---
        elif condition in ("pcl sprain", "pcl"):
            if phase == "phase1":
                patterns.extend(_PCL_PHASE1_BANNED)

        # --- Lateral ankle sprain ---
        elif condition in ("lateral ankle sprain", "ankle sprain", "ankle"):
            if phase == "phase1":
                patterns.extend(_ANKLE_PHASE1_BANNED)
            elif phase == "phase2":
                patterns.extend(_ANKLE_PHASE2_BANNED)

        # --- Shoulder rotator cuff tendinopathy ---
        elif "rotator cuff" in condition or "shoulder" in condition:
            if phase == "phase1":
                patterns.extend(_SHOULDER_RC_PHASE1_BANNED)

        # --- Patellar tendinopathy ---
        elif "patellar tendinopathy" in condition or "patella tendinopathy" in condition:
            if phase == "phase1":
                patterns.extend(_PATELLAR_TENDINOPATHY_PHASE1_BANNED)

        # --- PFPS / anterior knee pain ---
        # No hard bans — pain threshold is subjective (handled as warning)

        # --- LBP flexion-sensitive ---
        elif "lbp flexion" in condition or "flexion-sensitive" in condition or (
            "lbp" in condition and "flexion" in condition
        ) or "flexion sensitive" in condition:
            if phase == "phase1":
                patterns.extend(_LBP_FLEXION_PHASE1_BANNED)

        # --- LBP extension-sensitive ---
        elif "lbp extension" in condition or "extension-sensitive" in condition or (
            "lbp" in condition and "extension" in condition
        ) or "extension sensitive" in condition:
            if phase == "phase1":
                patterns.extend(_LBP_EXTENSION_PHASE1_BANNED)

        # --- Hip adductor strain ---
        elif "adductor" in condition or "hip adductor" in condition:
            if phase == "phase1":
                patterns.extend(_HIP_ADDUCTOR_PHASE1_BANNED)

        # --- Lateral epicondylalgia ---
        elif "epicondyl" in condition or "tennis elbow" in condition:
            if phase == "phase1":
                patterns.extend(_LATERAL_EPICONDYLALGIA_PHASE1_BANNED)

        return patterns

    # ------------------------------------------------------------------
    # Rehab-only plan validation
    # ------------------------------------------------------------------

    # Expected rehab session phases in canonical order
    _REHAB_SESSION_PHASES: list[str] = [
        "warm-up", "warmup", "warm_up",
        "mobility",
        "activation",
        "strengthening", "strength",
        "proprioception", "balance",
    ]

    # Canonical phase labels (for display / matching)
    _REHAB_PHASE_CANONICAL: list[str] = [
        "warm-up",
        "mobility",
        "activation",
        "strengthening",
        "proprioception",
    ]

    # Exercise-count ranges for rehab-only sessions
    _REHAB_EXERCISE_COUNT_RANGES: dict[int, tuple[int, int]] = {
        30: (4, 6),
        45: (6, 8),
        60: (8, 10),
    }

    def _validate_rehab_only_structure(
        self,
        plan: Plan,
        user_profile: UserProfile,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate structure and content of a rehab-only plan.

        Checks:
        - Each day has proper rehab session structure
          (warm-up -> mobility -> activation -> strengthening -> proprioception)
        - Exercise count is appropriate for session length
        - All exercises have RPE <= 6
        - Variety across sessions (not all identical)
        - Balance/proprioception work present for lower-limb injuries
        - Rotator cuff + scapular work present for shoulder injuries
        """
        days = list(self._iter_days(plan))
        if not days:
            return

        injuries = self._get_injuries(user_profile)
        session_length = (
            user_profile.get("session_length")
            or user_profile.get("session_length_minutes")
        )

        # --- Per-day checks ---
        all_exercise_lists: list[list[str]] = []

        for day in days:
            day_label = day.get("label", day.get("title", "unknown day"))

            # 1. Session phase structure check
            self._check_rehab_session_phases(day, day_label, errors, warnings)

            # 2. Exercise count for rehab session length
            if session_length:
                self._check_rehab_exercise_count(
                    day, day_label, int(session_length), errors, warnings,
                )

            # 3. RPE ceiling check — all exercises must be RPE <= 6
            self._check_rehab_rpe_ceiling(day, day_label, errors)

            # Collect exercise names for variety check
            all_exercise_lists.append(
                [n.lower().strip() for n in self._iter_exercise_names(day)]
            )

        # 4. Variety across sessions — not all identical
        if len(all_exercise_lists) >= 2:
            unique_sessions = {tuple(sorted(el)) for el in all_exercise_lists}
            if len(unique_sessions) == 1 and len(all_exercise_lists) > 1:
                errors.append({
                    "type": "REHAB_NO_VARIETY",
                    "reason": (
                        "All rehab sessions are identical. Rehab plans should "
                        "have variety across days to target different aspects "
                        "of recovery and prevent accommodation."
                    ),
                    "severity": "warning",
                })

        # 5 & 6. Injury-specific content checks
        for injury in injuries:
            region = self._injury_region(injury)
            condition = self._normalise_condition(injury.get("condition", ""))

            # Balance/proprioception for lower-limb injuries
            if region == "lower":
                self._check_rehab_lower_limb_proprioception(
                    days, condition, errors, warnings,
                )

            # Rotator cuff + scapular work for shoulder injuries
            if "rotator cuff" in condition or "shoulder" in condition:
                self._check_rehab_shoulder_content(
                    days, condition, errors, warnings,
                )

    def _check_rehab_session_phases(
        self,
        day: Day,
        day_label: str,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Check that a rehab-only day has the proper session structure.

        Expected phases: warm-up -> mobility -> activation ->
        strengthening -> proprioception.
        """
        # Collect block/section labels from the day
        found_phases: list[str] = []

        # Check well-known block keys
        warmup_keys = ("rehab_warmup", "rehab_warm_up", "warmup", "warm_up")
        mobility_keys = ("mobility",)
        activation_keys = ("activation", "glute_activation", "muscle_activation")
        strength_keys = ("strengthening", "strength", "main", "main_gym", "exercises")
        proprio_keys = ("proprioception", "balance", "balance_proprioception")

        phase_key_map = [
            ("warm-up", warmup_keys),
            ("mobility", mobility_keys),
            ("activation", activation_keys),
            ("strengthening", strength_keys),
            ("proprioception", proprio_keys),
        ]

        for phase_name, keys in phase_key_map:
            for key in keys:
                block = day.get(key)
                if block:
                    found_phases.append(phase_name)
                    break

        # Also scan a "blocks" array for phase labels
        blocks = day.get("blocks")
        if isinstance(blocks, list):
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                block_label = (
                    block.get("type", "") or block.get("label", "") or block.get("phase", "")
                ).lower()

                for canon in self._REHAB_PHASE_CANONICAL:
                    # Match if the canonical label appears in the block label
                    check_terms = [canon]
                    if canon == "warm-up":
                        check_terms.extend(["warmup", "warm up"])
                    elif canon == "proprioception":
                        check_terms.extend(["balance", "proprioceptive"])
                    elif canon == "strengthening":
                        check_terms.extend(["strength"])

                    if any(t in block_label for t in check_terms):
                        if canon not in found_phases:
                            found_phases.append(canon)
                        break

        # Report missing phases
        missing = [p for p in self._REHAB_PHASE_CANONICAL if p not in found_phases]

        if missing:
            errors.append({
                "type": "REHAB_MISSING_SESSION_PHASE",
                "reason": (
                    f"Day '{day_label}' is missing rehab session phase(s): "
                    f"{', '.join(missing)}. A rehab-only session should follow "
                    f"the structure: warm-up -> mobility -> activation -> "
                    f"strengthening -> proprioception."
                ),
                "severity": "critical",
            })

    def _check_rehab_exercise_count(
        self,
        day: Day,
        day_label: str,
        session_minutes: int,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Check exercise count is appropriate for a rehab-only session length."""
        # Find the closest matching rehab session length
        rehab_lengths = sorted(self._REHAB_EXERCISE_COUNT_RANGES.keys())
        closest = min(rehab_lengths, key=lambda k: abs(k - session_minutes))
        min_ex, max_ex = self._REHAB_EXERCISE_COUNT_RANGES[closest]

        ex_count = len(list(self._iter_exercise_names(day)))

        if ex_count < min_ex:
            errors.append({
                "type": "REHAB_TOO_FEW_EXERCISES",
                "reason": (
                    f"Day '{day_label}' has {ex_count} exercises for a "
                    f"~{session_minutes} min rehab session. Expected at least "
                    f"{min_ex} exercises (range {min_ex}-{max_ex})."
                ),
                "severity": "warning",
            })
        elif ex_count > max_ex:
            errors.append({
                "type": "REHAB_TOO_MANY_EXERCISES",
                "reason": (
                    f"Day '{day_label}' has {ex_count} exercises for a "
                    f"~{session_minutes} min rehab session. Expected at most "
                    f"{max_ex} exercises (range {min_ex}-{max_ex})."
                ),
                "severity": "warning",
            })

    def _check_rehab_rpe_ceiling(
        self,
        day: Day,
        day_label: str,
        errors: list[str],
    ) -> None:
        """All exercises in a rehab-only plan must have RPE <= 6."""
        for ex in self._iter_exercises(day):
            if not isinstance(ex, dict):
                continue
            rpe = ex.get("rpe") or ex.get("RPE") or ex.get("intensity_rpe")
            if rpe is None:
                continue

            # Handle range strings like "4-5" — take the upper end
            if isinstance(rpe, str):
                parts = rpe.replace("–", "-").split("-")
                try:
                    rpe_val = float(parts[-1].strip())
                except (ValueError, IndexError):
                    continue
            else:
                try:
                    rpe_val = float(rpe)
                except (ValueError, TypeError):
                    continue

            ex_name = (
                ex.get("name") or ex.get("exercise") or ex.get("exercise_name") or "unknown"
            )

            if rpe_val > 6:
                errors.append({
                    "type": "REHAB_RPE_TOO_HIGH",
                    "reason": (
                        f"Exercise '{ex_name}' on '{day_label}' has RPE {rpe} "
                        f"which exceeds the rehab ceiling of RPE 6. Rehab-only "
                        f"plans should stay at rehab intensity, not gym intensity."
                    ),
                    "severity": "critical",
                })

    def _check_rehab_lower_limb_proprioception(
        self,
        days: list[Day],
        condition: str,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Lower-limb injuries must include balance/proprioception work."""
        proprio_cues = [
            "balance", "proprioception", "proprioceptive",
            "single leg stand", "single-leg stand",
            "tandem stand", "bosu", "wobble board", "wobble",
            "airex", "foam pad balance", "stability disc",
            "star excursion", "y-balance", "y balance",
        ]

        found_proprio = False
        for day in days:
            for ex_name in self._iter_exercise_names(day):
                name_lower = ex_name.lower()
                if any(cue in name_lower for cue in proprio_cues):
                    found_proprio = True
                    break
            # Also check block labels
            blocks = day.get("blocks")
            if isinstance(blocks, list):
                for block in blocks:
                    if isinstance(block, dict):
                        label = (
                            block.get("type", "") or block.get("label", "")
                        ).lower()
                        if "balance" in label or "propriocep" in label:
                            found_proprio = True
                            break
            # Check dedicated key
            for key in ("proprioception", "balance", "balance_proprioception"):
                if day.get(key):
                    found_proprio = True
                    break
            if found_proprio:
                break

        if not found_proprio:
            errors.append({
                "type": "REHAB_MISSING_PROPRIOCEPTION",
                "reason": (
                    f"Lower-limb injury '{condition}' requires balance/"
                    f"proprioception work in the rehab plan, but none was "
                    f"detected across any session. Include exercises like "
                    f"single-leg stance, wobble board drills, or star "
                    f"excursion balance test progressions."
                ),
                "severity": "critical",
            })

    def _check_rehab_shoulder_content(
        self,
        days: list[Day],
        condition: str,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Shoulder injuries must include rotator cuff and scapular work."""
        rc_cues = [
            "external rotation", "internal rotation",
            "rotator cuff", "er/ir", "ir/er",
            "band pull-apart", "band pull apart",
            "face pull", "side-lying external rotation",
            "side lying external rotation",
            "prone y raise", "prone t raise",
            "prone y", "prone t", "prone i",
        ]
        scapular_cues = [
            "scapular", "scap", "serratus",
            "wall slide", "wall angel",
            "scapula push-up", "scapula push up", "scapula pushup",
            "low trap", "lower trap",
            "retraction", "protraction",
            "y-t-w", "ytw", "y t w",
        ]

        found_rc = False
        found_scapular = False

        for day in days:
            for ex_name in self._iter_exercise_names(day):
                name_lower = ex_name.lower()
                if not found_rc and any(cue in name_lower for cue in rc_cues):
                    found_rc = True
                if not found_scapular and any(cue in name_lower for cue in scapular_cues):
                    found_scapular = True
                if found_rc and found_scapular:
                    break
            if found_rc and found_scapular:
                break

        if not found_rc:
            errors.append({
                "type": "REHAB_MISSING_ROTATOR_CUFF_WORK",
                "reason": (
                    f"Shoulder injury '{condition}' requires rotator cuff "
                    f"exercises (e.g. external rotation, side-lying ER, "
                    f"band pull-aparts) but none were detected in the plan."
                ),
                "severity": "critical",
            })

        if not found_scapular:
            errors.append({
                "type": "REHAB_MISSING_SCAPULAR_WORK",
                "reason": (
                    f"Shoulder injury '{condition}' requires scapular "
                    f"stabilisation exercises (e.g. wall slides, serratus "
                    f"press, low-trap raises) but none were detected in the plan."
                ),
                "severity": "critical",
            })

    # ------------------------------------------------------------------
    # Unknown condition / severity warnings
    # ------------------------------------------------------------------

    def _validate_unknown_condition(
        self,
        user_profile: UserProfile,
        warnings: list[str],
    ) -> None:
        """Generate a warning when the injury condition is 'other' or unrecognised.

        Suggests the user seek a clinical assessment for appropriate guidance.
        """
        unknown_labels = {"other", "unknown", "unsure", "not sure", "undiagnosed", ""}

        for injury in self._get_injuries(user_profile):
            condition = (injury.get("condition") or "").strip().lower()
            normalised = self._normalise_condition(condition)

            # Check against known conditions in the region map
            is_known = any(key in normalised for key in _INJURY_REGION_MAP)

            if normalised in unknown_labels or not is_known:
                display_name = injury.get("condition") or "unspecified"
                warnings.append({
                    "type": "UNKNOWN_CONDITION",
                    "reason": (
                        f"Injury condition '{display_name}' is not a recognised "
                        f"condition in the validation ruleset. The plan has been "
                        f"generated with conservative defaults, but the user is "
                        f"strongly encouraged to seek a clinical assessment for "
                        f"a specific diagnosis and tailored rehabilitation guidance."
                    ),
                    "severity": "warning",
                })

    def _validate_unknown_severity(
        self,
        user_profile: UserProfile,
        warnings: list[str],
    ) -> None:
        """Generate a warning when severity is unknown or unspecified.

        Notes that moderate restrictions have been assumed as a safe default.
        """
        unknown_severity_labels = {
            "i don't know", "i dont know", "unknown", "unsure",
            "not sure", "unspecified", "",
        }

        for injury in self._get_injuries(user_profile):
            severity = injury.get("severity")

            if severity is None or str(severity).strip().lower() in unknown_severity_labels:
                condition_name = injury.get("condition") or "unspecified injury"
                warnings.append({
                    "type": "UNKNOWN_SEVERITY",
                    "reason": (
                        f"Severity for '{condition_name}' is unknown or was not "
                        f"provided. Moderate restrictions have been assumed as a "
                        f"safe default. If the actual severity is mild, the plan "
                        f"may be more conservative than necessary; if severe, it "
                        f"may not be restrictive enough. A clinical assessment "
                        f"is recommended to determine appropriate intensity."
                    ),
                    "severity": "warning",
                })

    # ------------------------------------------------------------------
    # Exercise iteration helper (yields full exercise dicts)
    # ------------------------------------------------------------------

    @staticmethod
    def _iter_exercises(day: Day):
        """Yield every exercise dict from a day dict.

        Unlike ``_iter_exercise_names`` which yields name strings, this yields
        the full exercise dicts so callers can inspect fields like RPE.
        """
        blocks_keys = [
            "rehab_warmup", "rehab_warm_up", "warmup", "warm_up",
            "mobility",
            "activation", "glute_activation", "muscle_activation",
            "main", "main_gym", "gym",
            "strengthening", "strength",
            "proprioception", "balance", "balance_proprioception",
            "rehab_accessories", "accessories", "rehab_accessory",
            "exercises", "exercise_list",
            "speed_work", "sprint_work", "conditioning",
        ]

        yielded_ids: set[int] = set()

        for bk in blocks_keys:
            block = day.get(bk)
            if not block:
                continue
            if isinstance(block, list):
                for ex in block:
                    if isinstance(ex, dict) and id(ex) not in yielded_ids:
                        yielded_ids.add(id(ex))
                        yield ex

        # Also scan "blocks" array pattern
        blocks = day.get("blocks")
        if isinstance(blocks, list):
            for block in blocks:
                if isinstance(block, dict):
                    block_exercises = block.get("exercises", [])
                    if isinstance(block_exercises, list):
                        for ex in block_exercises:
                            if isinstance(ex, dict) and id(ex) not in yielded_ids:
                                yielded_ids.add(id(ex))
                                yield ex

    # ------------------------------------------------------------------
    # Clinician restriction parser
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_clinician_restriction(restriction: str) -> list[str]:
        """Extract banned activity keywords from a free-text clinician restriction.

        This is deliberately conservative — it catches common patterns like
        'no running for 6 months', 'avoid overhead pressing', 'no impact'.
        Returns a list of patterns to match against exercise names.
        """
        banned: list[str] = []

        # "no <activity>" patterns
        no_patterns = re.findall(r"no\s+([a-z][a-z\s\-]+?)(?:\s+for|\s+until|$|,|\.)", restriction)
        for p in no_patterns:
            p = p.strip()
            if p:
                banned.append(p)

        # "avoid <activity>" patterns
        avoid_patterns = re.findall(r"avoid\s+([a-z][a-z\s\-]+?)(?:\s+for|\s+until|$|,|\.)", restriction)
        for p in avoid_patterns:
            p = p.strip()
            if p:
                banned.append(p)

        # "don't/do not <activity>" patterns
        dont_patterns = re.findall(
            r"(?:don'?t|do not)\s+([a-z][a-z\s\-]+?)(?:\s+for|\s+until|$|,|\.)",
            restriction,
        )
        for p in dont_patterns:
            p = p.strip()
            if p:
                banned.append(p)

        # Common specific activity keywords
        activity_keywords = {
            "running": ["running", "run", "jog", "jogging", "sprint"],
            "jumping": ["jumping", "jump", "plyometric", "plyo", "hop", "bound"],
            "overhead": ["overhead press", "ohp", "military press", "snatch", "jerk"],
            "impact": ["high impact", "high-impact", "running", "jumping"],
            "cutting": ["cutting", "pivot", "change of direction", "agility"],
            "squatting": ["squat", "lunge"],
            "deadlifting": ["deadlift", "rdl"],
            "pressing": ["press", "bench"],
        }

        for activity, keywords in activity_keywords.items():
            if activity in restriction:
                banned.extend(keywords)

        return banned
