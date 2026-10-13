"""Prompt for one question and print a JSON answer."""

import argparse
import json

from policy_assistant.assistant import DEFAULT_AS_OF_DATE, ask


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline merchant policy Q&A")
    parser.add_argument("question", nargs="*", help="question to ask")
    parser.add_argument("--date", default=DEFAULT_AS_OF_DATE.isoformat(), help="policy date (YYYY-MM-DD)")
    args = parser.parse_args()
    question = " ".join(args.question).strip() or input("Question: ")
    print(json.dumps(ask(question, args.date).to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()