"""
Utilities for normalizing MCP-Bench LLM judge scores.

The judge prompt asks for 0-10 scores. Benchmark result JSON stores these
scores on a 0-1 scale so they are comparable with the other rate metrics.
"""

from numbers import Real
from typing import Any, Dict, Iterable


LLM_JUDGE_SUBDIMENSION_SCORE_FIELDS = (
    "task_fulfillment",
    "grounding",
    "tool_appropriateness",
    "parameter_accuracy",
    "dependency_awareness",
    "parallelism_and_efficiency",
)


def normalize_raw_llm_judge_score(value: Any) -> Any:
    """Convert a raw 0-10 LLM judge score to the benchmark's 0-1 scale."""
    if isinstance(value, bool) or not isinstance(value, Real):
        return value
    return value / 10


def normalize_raw_llm_judge_scores(
    scores: Dict[str, Any],
    fields: Iterable[str] = LLM_JUDGE_SUBDIMENSION_SCORE_FIELDS,
) -> Dict[str, Any]:
    """Return a copy with raw LLM judge score fields normalized to 0-1."""
    normalized = dict(scores)
    for field in fields:
        if field in normalized:
            normalized[field] = normalize_raw_llm_judge_score(normalized[field])
    return normalized
