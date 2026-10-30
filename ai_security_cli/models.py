"""Data models shared across the toolkit: a loaded TestCase and the
result of running one attempt of it against a model."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TestCase:
    id: str
    category: str
    prompt: str
    expect: str  # "refuse" | "contains_all" | "not_contains" — see scoring.py
    system_prompt: Optional[str] = None
    expect_value: Any = None
    notes: str = ""


@dataclass
class AttemptResult:
    test_id: str
    category: str
    model: str
    repetition: int
    prompt: str
    output: str
    classification: str  # "pass" | "fail" | "uncertain:pass" | "uncertain:fail" | "error"
    reason: str
    latency_ms: float
    timestamp: str
    error: Optional[str] = None
