from datetime import date
from pathlib import Path
import unittest

from policy_assistant import ask


ROOT = Path(__file__).resolve().parents[1]


class AssistantTests(unittest.TestCase):
    def test_upi_settlement_uses_active_addon_rule(self) -> None:
        result = ask("When does a small merchant receive UPI money?", "2026-08-15")

        self.assertEqual(result.status, "CONFLICT_RESOLVED")
        self.assertIn("same day by 11:59 PM", result.answer)
        self.assertIn("T+1", result.answer)
        self.assertIn("circular_2026_08_amendment.md, clause A", result.citations)

    def test_upi_settlement_before_amendment_is_t_plus_one(self) -> None:
        result = ask("When does a merchant receive UPI money with Instant Settlement?", "2026-07-20")

        self.assertEqual(result.status, "ANSWERED")
        self.assertIn("T+1", result.answer)
        self.assertIn("policy_master_v1.md, clause 1.1", result.citations)

    def test_large_merchant_mdr_and_gst_are_calculated(self) -> None:
        result = ask("A large merchant above Rs.10 lakh receives a Rs.4,000 UPI payment. What MDR and GST do they pay?")

        self.assertIn("Rs. 20.00", result.answer)
        self.assertIn("Rs. 3.60", result.answer)
        self.assertIn("Rs. 23.60", result.answer)

    def test_large_transaction_uses_amended_cap(self) -> None:
        result = ask("Same large merchant, a Rs.1,50,000 payment. What do they pay?", date(2026, 8, 15))

        self.assertIn("applicable cap is Rs. 25.00", result.answer)
        self.assertIn("MDR charged is Rs. 25.00", result.answer)
        self.assertIn("GST at 18% of MDR is Rs. 4.50", result.answer)

    def test_small_merchant_uses_amended_rate_and_cites_it(self) -> None:
        result = ask("A small merchant up to Rs.10 lakh gets a Rs.4,000 UPI transaction. What is MDR?", "2026-08-15")

        self.assertIn("MDR is 0.25%", result.answer)
        self.assertIn("Rs. 10.00", result.answer)
        self.assertIn("circular_2026_08_amendment.md, clause B", result.citations)

    def test_refund_exception_expires_from_september(self) -> None:
        august = ask("I refund the transaction 3 hours later. Do I get the MDR back?", "2026-08-20")
        september = ask("I refund the transaction 3 hours later. Do I get the MDR back?", "2026-09-05")

        self.assertIn("MDR is reversed in full", august.answer)
        self.assertIn("deleted", september.answer)
        self.assertEqual(september.status, "CONFLICT_RESOLVED")

    def test_faq_cap_claim_is_marked_wrong(self) -> None:
        result = ask("What does the FAQ say about the MDR cap, and is it right?")

        self.assertEqual(result.status, "CONFLICT_RESOLVED")
        self.assertIn("That is not correct", result.answer)
        self.assertTrue(any("merchant_faq_2026-03.md" in citation for citation in result.citations))

    def test_daily_limit_is_distinct_from_transaction_limit(self) -> None:
        result = ask("Can a customer pay Rs.1,00,000 twice in one day to a merchant?", "2026-08-15")

        self.assertIn("No, not under the standard daily limit", result.answer)
        self.assertIn("whichever is lower", result.answer)
        self.assertTrue(any("clause E" in citation for citation in result.citations))

    def test_closure_uses_working_days_and_does_not_guess_calendar(self) -> None:
        result = ask("I closed my account yesterday. When will I get my money?")

        self.assertIn("10 working days", result.answer)
        self.assertIn("cannot calculate an exact release date", result.answer)
        self.assertIn("policy_master_v1.md, clause 5.2", result.citations)

    def test_card_settlement_is_not_same_day(self) -> None:
        result = ask("Does the policy allow me to settle card payments same day?")

        self.assertIn("No", result.answer)
        self.assertIn("T+2", result.answer)
        self.assertIn("policy_master_v1.md, clause 1.2", result.citations)

    def test_missing_volume_and_unrelated_question_do_not_guess(self) -> None:
        missing = ask("What MDR and GST do I pay on a Rs.4,000 transaction?")
        unrelated = ask("What is the weather in Delhi?")

        self.assertEqual(missing.status, "CANNOT_ANSWER")
        self.assertEqual(unrelated.status, "CANNOT_ANSWER")


if __name__ == "__main__":
    unittest.main()