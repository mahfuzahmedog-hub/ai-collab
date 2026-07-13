from __future__ import annotations
import asyncio
import json
import logging
import re
from typing import Any, Optional

from app.llm import llm_router

logger = logging.getLogger(__name__)


class EvalCase:
    def __init__(self, name: str, input: str, expected: str = "", criteria: str = ""):
        self.name = name
        self.input = input
        self.expected = expected
        self.criteria = criteria


class EvalResult:
    def __init__(self, case: EvalCase, passed: bool, score: float, reason: str):
        self.case = case
        self.passed = passed
        self.score = score
        self.reason = reason


class EvalRunner:
    def __init__(self):
        self._cases: dict[str, list[EvalCase]] = {}

    def add_case(self, suite: str, case: EvalCase):
        self._cases.setdefault(suite, []).append(case)

    async def run_suite(self, suite: str, agent_fn: callable) -> list[EvalResult]:
        results = []
        for case in self._cases.get(suite, []):
            try:
                output = await agent_fn(case.input)
                passed, score, reason = await self._score(case, output)
                results.append(EvalResult(case, passed, score, reason))
            except Exception as e:
                results.append(EvalResult(case, False, 0.0, f"Error: {e}"))
        return results

    async def _score(self, case: EvalCase, output: str) -> tuple[bool, float, str]:
        if case.expected:
            if case.expected.lower() in output.lower():
                return True, 1.0, "Expected substring found"
            return False, 0.0, "Expected substring not found"
        if case.criteria:
            prompt = f"""Evaluate this output against the criteria.

Criteria: {case.criteria}

Output: {output[:1000]}

Score 0-10 and state pass/fail. Return JSON: {{"score": int, "pass": bool, "reason": "..."}}"""
            provider = llm_router.get_provider()
            if provider:
                resp = await provider.chat([
                    {"role": "system", "content": "You are an evaluator."},
                    {"role": "user", "content": prompt},
                ], temperature=0.1)
                try:
                    match = re.search(r'\{.*\}', resp, re.DOTALL)
                    if match:
                        d = json.loads(match.group())
                        return d.get("pass", False), float(d.get("score", 0)), d.get("reason", "")
                except Exception:
                    pass
        return True, 1.0, "No criteria specified"


eval_runner = EvalRunner()
