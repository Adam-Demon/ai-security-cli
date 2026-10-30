"""Loads test case suites from YAML or JSON files into TestCase objects."""

import json
from pathlib import Path

import yaml

from .models import TestCase


def load_cases(path: str) -> list[TestCase]:
    """Load a list of TestCase from a .yaml/.yml or .json file.

    Accepts either a bare list of case dicts, or a dict with a top-level
    "cases" key (the format used by testcases/bankbot_cases.yaml).
    """
    p = Path(path)
    with open(p, "r") as f:
        if p.suffix.lower() in (".yaml", ".yml"):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    raw_cases = data["cases"] if isinstance(data, dict) and "cases" in data else data
    cases = []
    for c in raw_cases:
        cases.append(TestCase(
            id=c["id"],
            category=c.get("category", "general"),
            prompt=c["prompt"],
            expect=c["expect"],
            system_prompt=c.get("system_prompt"),
            expect_value=c.get("expect_value"),
            notes=c.get("notes", ""),
        ))
    return cases
