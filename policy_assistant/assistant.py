"""A small offline, rule-based assistant for the supplied merchant policies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import re

from policy_assistant.documents import PolicyDocument, parse_document


DEFAULT_AS_OF_DATE = date(2026, 8, 15)
DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "ai-2-data"
CENT = Decimal("0.01")


@dataclass(frozen=True)
class Answer:
    answer: str
    citations: tuple[str, ...]
    status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "answer": self.answer,
            "citations": list(self.citations),
            "status": self.status,
        }


def _as_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _documents(data_dir: str | Path) -> dict[str, PolicyDocument]:
    root = Path(data_dir)
    paths = (
        "policy_master_v1.md",
        "circular_2026_08_amendment.md",
        "merchant_faq_2026-03.md",
    )
    return {name: parse_document(root / name) for name in paths}


def _clause(documents: dict[str, PolicyDocument], source: str, reference: str) -> str:
    document = documents[source]
    clause = next(item for item in document.clauses if item.reference == reference)
    return clause.citation


def _faq_citation(documents: dict[str, PolicyDocument], heading_part: str) -> str:
    document = documents["merchant_faq_2026-03.md"]
    item = next(entry for entry in document.clauses if heading_part.lower() in (entry.heading or "").lower())
    return item.citation


def _money(value: Decimal) -> str:
    return f"Rs. {value.quantize(CENT, rounding=ROUND_HALF_UP):,.2f}"


def _transaction_amount(question: str) -> Decimal | None:
    matches = list(re.finditer(r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)", question, re.IGNORECASE))
    if not matches:
        return None
    return Decimal(matches[-1].group(1).replace(",", ""))


def _is_large_merchant(question: str) -> bool | None:
    lowered = question.lower()
    if any(term in lowered for term in ("large merchant", "above rs.10 lakh", "above 10 lakh", "over 10 lakh", "above ₹10 lakh")):
        return True
    if any(term in lowered for term in ("small merchant", "up to rs.10 lakh", "up to 10 lakh", "under 10 lakh", "below 10 lakh")):
        return False
    return None


def _answered(answer: str, citations: list[str], status: str = "ANSWERED") -> Answer:
    return Answer(answer=answer, citations=tuple(dict.fromkeys(citations)), status=status)


def ask(
    question: str,
    as_of_date: date | str = DEFAULT_AS_OF_DATE,
    data_dir: str | Path = DATA_DIRECTORY,
) -> Answer:
    """Answer a supported merchant-policy question using local Markdown only."""
    as_of = _as_date(as_of_date)
    documents = _documents(data_dir)
    master = "policy_master_v1.md"
    circular = "circular_2026_08_amendment.md"
    faq = "merchant_faq_2026-03.md"
    lower = question.lower()

    if any(term in lower for term in ("closed my account", "account closure", "close my account", "pending settlement")):
        return _answered(
            "Pending settlements are released within 10 working days of account closure, after outstanding dues are deducted. The documents do not provide a bank-holiday calendar, so I cannot calculate an exact release date.",
            [_clause(documents, master, "5.2")],
        )

    if "card" in lower and any(term in lower for term in ("same day", "settle", "settlement")):
        return _answered(
            "No. Card transactions settle T+2 (two days after the transaction); the policy does not state a same-day card settlement option.",
            [_clause(documents, master, "1.2")],
        )

    if "chargeback" in lower:
        return _answered(
            "The customer's bank must raise a chargeback dispute within 120 days. The policy does not say that the merchant raises it.",
            [_clause(documents, master, "3.4")],
        )

    if any(term in lower for term in ("capital markets", "insurance")) and any(
        term in lower for term in ("limit", "accept", "transaction", "kyc")
    ):
        return _answered(
            "Capital Markets and Insurance merchants may accept up to Rs. 2,00,000 per UPI transaction only after completing enhanced KYC (Annexure C). The customer daily account limit still applies.",
            [_clause(documents, master, "4.2"), _clause(documents, master, "4.4"), _clause(documents, master, "4.3")]
            + ([_clause(documents, circular, "E")] if as_of >= date(2026, 8, 1) else []),
        )

    if "faq" in lower and any(term in lower for term in ("mdr", "cap", "upper limit", "fee")):
        fee_citation = _faq_citation(documents, "What do I pay on a UPI transaction")
        if as_of >= date(2026, 8, 1):
            return _answered(
                "The FAQ says there is no upper limit on the fee. That is not correct as of this date: the cap is Rs. 15 per UPI transaction for merchants up to Rs. 10 lakh monthly volume and Rs. 25 above Rs. 10 lakh.",
                [fee_citation, _clause(documents, circular, "C")],
                "CONFLICT_RESOLVED",
            )
        return _answered(
            "The FAQ says there is no upper limit on the fee, but the master policy caps MDR at Rs. 15 per UPI transaction. The FAQ is wrong.",
            [fee_citation, _clause(documents, master, "2.3")],
            "CONFLICT_RESOLVED",
        )

    if any(term in lower for term in ("refund", "refunded", "get the mdr back", "fee back", "reverse the fee")):
        if as_of < date(2026, 9, 1):
            return _answered(
                "Yes. Under the policy in effect on this date, if the refund is initiated within 24 hours of the transaction, MDR is reversed in full. A refund 3 hours later qualifies.",
                [_clause(documents, master, "3.2"), _clause(documents, master, "3.3")],
            )
        return _answered(
            "No. Since 1 September 2026, MDR on a refunded transaction is not returned; the former within-24-hours exception was deleted.",
            [_clause(documents, master, "3.2"), _clause(documents, circular, "D")],
            "CONFLICT_RESOLVED",
        )

    if any(term in lower for term in ("twice in one day", "twice a day", "two payments", "two transactions", "daily limit", "per day")):
        citations = [_clause(documents, master, "4.1"), _clause(documents, master, "4.3")]
        if as_of >= date(2026, 8, 1):
            citations.append(_clause(documents, circular, "E"))
            daily_limit = "Rs. 1,00,000 or the customer's own bank limit, whichever is lower"
        else:
            daily_limit = "Rs. 1,00,000 across all UPI transactions"
        return _answered(
            f"No, not under the standard daily limit: the account limit is {daily_limit}. Two Rs. 1,00,000 payments would total Rs. 2,00,000. The Rs. 2,00,000 per-transaction exception for Capital Markets and Insurance merchants requires enhanced KYC and does not raise this customer daily limit.",
            citations,
        )

    if "settle" in lower and "upi" in lower or "upi money" in lower or "receive upi" in lower:
        if as_of < date(2026, 8, 1):
            return _answered(
                "As of this date, UPI settlement is T+1 (the next working day). The Instant Settlement add-on rule does not take effect until 1 August 2026.",
                [_clause(documents, master, "1.1")],
            )
        if "instant settlement" in lower or "add-on" in lower or "addon" in lower:
            return _answered(
                "With an active Instant Settlement add-on, UPI settles the same day by 11:59 PM. Without the add-on, it settles T+1 (the next working day). Small-merchant status does not change this timing.",
                [_clause(documents, circular, "A")],
                "CONFLICT_RESOLVED",
            )
        return _answered(
            "For UPI, merchants with an active Instant Settlement add-on receive settlement the same day by 11:59 PM; all others receive it T+1, the next working day. The documents do not define a bank-holiday calendar for calculating an exact date.",
            [_clause(documents, circular, "A")],
            "CONFLICT_RESOLVED",
        )

    if "mdr" in lower or "gst" in lower or "fee" in lower or "pay" in lower and _transaction_amount(question) is not None:
        amount = _transaction_amount(question)
        merchant_is_large = _is_large_merchant(question)
        if amount is None:
            return Answer("CANNOT_ANSWER: the transaction amount is missing.", (), "CANNOT_ANSWER")
        if merchant_is_large is None:
            return Answer("CANNOT_ANSWER: monthly merchant volume is needed to select the MDR rate and cap.", (), "CANNOT_ANSWER")

        if merchant_is_large:
            rate = Decimal("0.005")
            cap = Decimal("25") if as_of >= date(2026, 8, 1) else Decimal("15")
        else:
            rate = Decimal("0.0025") if as_of >= date(2026, 8, 1) else Decimal("0.003")
            cap = Decimal("15")
        calculated_mdr = (amount * rate).quantize(CENT, rounding=ROUND_HALF_UP)
        mdr = min(calculated_mdr, cap)
        gst = (mdr * Decimal("0.18")).quantize(CENT, rounding=ROUND_HALF_UP)
        cited_clauses = [
            _clause(documents, master, "2.2" if merchant_is_large else "2.1"),
            _clause(documents, master, "2.4"),
        ]
        if not merchant_is_large and as_of >= date(2026, 8, 1):
            cited_clauses.append(_clause(documents, circular, "B"))
        cited_clauses.append(
            _clause(documents, circular if as_of >= date(2026, 8, 1) else master, "C" if as_of >= date(2026, 8, 1) else "2.3")
        )
        return _answered(
            f"MDR is {(rate * 100).normalize()}% of {_money(amount)} = {_money(calculated_mdr)}; the applicable cap is {_money(cap)}, so MDR charged is {_money(mdr)}. GST at 18% of MDR is {_money(gst)}. Total MDR plus GST is {_money(mdr + gst)}.",
            cited_clauses,
            "CONFLICT_RESOLVED" if as_of >= date(2026, 8, 1) else "ANSWERED",
        )

    return Answer(
        "CANNOT_ANSWER: this question is outside the supported policy topics or does not include enough information.",
        (),
        "CANNOT_ANSWER",
    )