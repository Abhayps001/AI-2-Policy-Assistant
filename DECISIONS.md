# Decisions and ambiguities

- **Default date:** The assignment says to use 15 August 2026 when a question omits a date, so `ask` uses that default.
- **Amendment dates:** Circular clauses A, B, C, and E apply from 1 August 2026. Clause D's parenthetical sets its deletion of master clause 3.3 to 1 September 2026; the master exception therefore remains active through 31 August.
- **Source precedence:** A circular amendment controls only from its stated effective date. The FAQ is informational and dated March 2026; it does not override the master or later circular. Conflicts that change an answer are marked `CONFLICT_RESOLVED` and explained.
- **FAQ citation:** FAQ entries have headings but no clause numbers. The parser cites the file and exact question heading rather than inventing a clause number.
- **MDR cap and GST:** Apply the transaction MDR cap first, then calculate 18% GST on that capped MDR. GST is not included in the cap. Decimal arithmetic rounds currency to two decimal places.
- **Settlement timing:** T+1 means next working day, but no bank-holiday calendar was provided. The assistant gives the rule and abstains from computing an exact settlement date.
- **Customer limits:** A transaction limit is not a daily limit. The Capital Markets/Insurance exception requires enhanced KYC; it does not override the separately stated customer daily account limit.
- **Account closure:** “Within 10 working days” is not treated as 10 calendar days. Outstanding dues are deducted; no exact payout date is guessed.
- **Scope and unknowns:** Unsupported questions, missing transaction amounts, or missing merchant monthly-volume bands for MDR calculations return `CANNOT_ANSWER` rather than relying on unstated assumptions.
- **AI disclosure:** The assistant is hand-written deterministic Python logic. GitHub Copilot was used to help inspect the assignment and author code/tests/docs; no external LLM service is called at runtime.