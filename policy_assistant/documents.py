"""Read policy documents while preserving their original citation labels."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path
import re


_DATE_FORMATS = ("%d %B %Y",)
_MASTER_CLAUSE = re.compile(r"^(\d+\.\d+)\s+(.+)$")
_CIRCULAR_CLAUSE = re.compile(r"^([A-Z])\.\s+(.+)$")
_EFFECTIVE_DATE = re.compile(r"Effective\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})", re.IGNORECASE)


@dataclass(frozen=True)
class Clause:
    source_name: str
    reference: str | None
    section: str | None
    heading: str | None
    text: str
    effective_from: date | None

    @property
    def citation(self) -> str:
        if self.reference is not None:
            return f"{self.source_name}, clause {self.reference}"
        if self.heading is not None:
            return f"{self.source_name}, heading {self.heading!r}"
        return self.source_name


@dataclass(frozen=True)
class PolicyDocument:
    source_name: str
    title: str
    updated_on: date | None
    effective_from: date | None
    clauses: tuple[Clause, ...]


def _parse_date(value: str) -> date:
    for date_format in _DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported document date: {value}")


def _date_after(pattern: str, text: str) -> date | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return _parse_date(match.group(1)) if match else None


def parse_document(path: str | Path) -> PolicyDocument:
    """Parse clause-like entries without assigning numbers to unnumbered text."""
    document_path = Path(path)
    lines = document_path.read_text(encoding="utf-8").splitlines()
    title = next((line[2:].strip() for line in lines if line.startswith("# ")), document_path.stem)
    header = "\n".join(lines[:3])
    updated_on = _date_after(r"(?:Issued|last updated)\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})", header)
    effective_from = _date_after(r"Effective\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})", header)
    clauses: list[Clause] = []
    section: str | None = None
    faq_heading: str | None = None
    faq_answer: list[str] = []

    def add_faq_entry() -> None:
        if faq_heading is not None and faq_answer:
            clauses.append(
                Clause(
                    source_name=document_path.name,
                    reference=None,
                    section=section,
                    heading=faq_heading,
                    text=" ".join(part.strip() for part in faq_answer if part.strip()),
                    effective_from=None,
                )
            )

    for line in lines:
        if line.startswith("## "):
            add_faq_entry()
            faq_heading = None
            faq_answer = []
            section = line[3:].strip()
            continue

        master_match = _MASTER_CLAUSE.match(line)
        circular_match = _CIRCULAR_CLAUSE.match(line)
        if master_match or circular_match:
            add_faq_entry()
            faq_heading = None
            faq_answer = []
            match = master_match or circular_match
            assert match is not None
            reference, text = match.groups()
            clause_effective = _date_after(r"Effective\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})", text)
            clauses.append(
                Clause(
                    source_name=document_path.name,
                    reference=reference,
                    section=section,
                    heading=None,
                    text=text,
                    effective_from=clause_effective or effective_from,
                )
            )
            continue

        if (
            line.strip().startswith("(")
            and clauses
            and clauses[-1].section == section
            and clauses[-1].reference in set("ABCDEF")
        ):
            continuation = line.strip()
            clause_effective = _date_after(
                r"Effective\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})", continuation
            )
            clauses[-1] = replace(
                clauses[-1],
                text=f"{clauses[-1].text} {continuation}",
                effective_from=clause_effective or clauses[-1].effective_from,
            )
            continue

        faq_match = re.match(r"^\*\*(.+?)\*\*$", line)
        if faq_match:
            add_faq_entry()
            faq_heading = faq_match.group(1).strip()
            faq_answer = []
        elif faq_heading is not None and line.strip():
            faq_answer.append(line)

    add_faq_entry()
    return PolicyDocument(
        source_name=document_path.name,
        title=title,
        updated_on=updated_on,
        effective_from=effective_from,
        clauses=tuple(clauses),
    )