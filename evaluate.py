"""Run eval.json and print a small answer, citation, and status score table."""

import json
from pathlib import Path

from policy_assistant.assistant import ask


ROOT = Path(__file__).resolve().parent


def evaluate(path: str | Path = ROOT / "eval.json") -> tuple[int, int]:
    cases = json.loads(Path(path).read_text(encoding="utf-8"))
    passed = 0
    print(f"{'ID':<5} {'ANSWER':<8} {'CITATIONS':<10} {'STATUS':<8}")
    print("-" * 36)
    for case in cases:
        result = ask(case["question"], case["as_of_date"])
        answer_ok = case["expected_answer"].lower() in result.answer.lower()
        citations_ok = set(case["expected_citations"]).issubset(result.citations)
        status_ok = case["expected_status"] == result.status
        passed_case = answer_ok and citations_ok and status_ok
        passed += int(passed_case)
        print(
            f"{case['id']:<5} {('PASS' if answer_ok else 'FAIL'):<8} "
            f"{('PASS' if citations_ok else 'FAIL'):<10} "
            f"{('PASS' if status_ok else 'FAIL'):<8}"
        )
        if not passed_case:
            print(f"      expected: {case['expected_answer']} | {case['expected_citations']} | {case['expected_status']}")
            print(f"      actual:   {result.answer} | {list(result.citations)} | {result.status}")
    print(f"\nScore: {passed}/{len(cases)} cases passed")
    return passed, len(cases)


if __name__ == "__main__":
    evaluate()