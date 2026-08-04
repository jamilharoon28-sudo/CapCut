"""JSON Schemas for Claude decision outputs (runbook §7; test F8).

Claude may only *select/reorder* supplied ids and add commentary. It must not
change quoted speech, invent ids, paths, or UI controls. Every response is
validated against one of these schemas; unknown ids and invalid ranges are
rejected by the provider's semantic checks on top of these structural schemas.
"""

from __future__ import annotations

PROMPT_VERSION = "2026-08-04.1"

HOOK_RANKING_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["ranking"],
    "properties": {
        "ranking": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["candidate_id", "rank", "reason", "confidence"],
                "properties": {
                    "candidate_id": {"type": "string"},
                    "rank": {"type": "integer", "minimum": 1},
                    "reason": {"type": "string", "maxLength": 400},
                    "risks": {"type": "string", "maxLength": 400},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        }
    },
}

NARRATIVE_PLAN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["ordered_unit_ids", "target_duration_us", "confidence"],
    "properties": {
        "ordered_unit_ids": {"type": "array", "items": {"type": "string"}},
        "roles": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["unit_id", "role"],
                "properties": {
                    "unit_id": {"type": "string"},
                    "role": {"type": "string"},
                    "omission_reason": {"type": "string", "maxLength": 300},
                },
            },
        },
        "target_duration_us": {"type": "integer", "minimum": 1},
        "unresolved_questions": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
}

BEGINNER_EXPLANATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "action", "reason", "expected_result", "common_mistake"],
    "properties": {
        "title": {"type": "string", "maxLength": 80},
        "action": {"type": "string", "maxLength": 200},
        "reason": {"type": "string", "maxLength": 200},
        "expected_result": {"type": "string", "maxLength": 200},
        "common_mistake": {"type": "string", "maxLength": 200},
        "knowledge_base_step_id": {"type": "string"},
        "needs_human_mapping": {"type": "boolean"},
    },
}

EDITORIAL_QC_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings"],
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["timecode_us", "severity", "message"],
                "properties": {
                    "timecode_us": {"type": "integer", "minimum": 0},
                    "severity": {"enum": ["info", "minor", "major", "blocker"]},
                    "message": {"type": "string", "maxLength": 400},
                    "suggested_action": {"type": "string", "maxLength": 400},
                },
            },
        }
    },
}

SCHEMAS_BY_NAME = {
    "hook_ranking": HOOK_RANKING_SCHEMA,
    "narrative_plan": NARRATIVE_PLAN_SCHEMA,
    "beginner_explanation": BEGINNER_EXPLANATION_SCHEMA,
    "editorial_qc": EDITORIAL_QC_SCHEMA,
}
