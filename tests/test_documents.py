from datetime import date
from pathlib import Path
import unittest

from policy_assistant.documents import parse_document


DATA = Path(__file__).resolve().parents[1] / "ai-2-data"


class ParseDocumentTests(unittest.TestCase):
    def test_master_clauses_keep_their_original_numbers(self) -> None:
        document = parse_document(DATA / "policy_master_v1.md")

        self.assertEqual(len(document.clauses), 17)
        self.assertEqual(document.clauses[0].reference, "1.1")
        self.assertEqual(document.clauses[0].citation, "policy_master_v1.md, clause 1.1")
        self.assertEqual(document.effective_from, date(2026, 1, 1))

    def test_circular_amendments_keep_letter_labels_and_override_date(self) -> None:
        document = parse_document(DATA / "circular_2026_08_amendment.md")

        self.assertEqual([clause.reference for clause in document.clauses], list("ABCDEF"))
        self.assertEqual(document.clauses[0].effective_from, date(2026, 8, 1))
        self.assertEqual(document.clauses[3].effective_from, date(2026, 9, 1))

    def test_faq_entries_do_not_receive_invented_clause_numbers(self) -> None:
        document = parse_document(DATA / "merchant_faq_2026-03.md")

        self.assertEqual(len(document.clauses), 5)
        self.assertIsNone(document.clauses[0].reference)
        self.assertIn("heading", document.clauses[0].citation)
        self.assertEqual(document.updated_on, date(2026, 3, 12))


if __name__ == "__main__":
    unittest.main()