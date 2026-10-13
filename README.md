# Merchant Policy Assistant

A small offline Python assistant for the three Markdown documents in `ai-2-data/`. It uses explicit topic rules and the policy text; it does not call an LLM or need an API key.

## Run

Use Python 3.10 or newer:

```powershell
python -m policy_assistant "A large merchant above Rs.10 lakh receives a Rs.4,000 UPI payment. What MDR and GST do they pay?" --date 2026-08-15
python evaluate.py
python -m unittest discover -s tests -v
```

If no question argument is supplied, the CLI prompts for one. The default policy date is `2026-08-15`. Answers are JSON with `answer`, `citations`, and `status` (`ANSWERED`, `CONFLICT_RESOLVED`, or `CANNOT_ANSWER`).

## What works

- UPI and card settlement, UPI MDR/GST, refunds, customer limits, enhanced KYC, account-closure settlement timing, and chargeback deadline questions.
- The 1 August 2026 amendments and the 1 September refund-clause deletion are selected by `as_of_date`.
- MDR and GST are calculated using `Decimal`; source labels are kept from the Markdown.
- The stale FAQ is identified as stale when it disagrees with policy in effect.

## What does not

- This is a small rule-based prototype, not a general language understanding system. Rephrase outside the recognized policy topics and it may abstain.
- It does not calculate working days because no bank-holiday calendar is supplied.
- It does not calculate dates from relative phrases such as “yesterday,” access customer or merchant account data, or implement the missing Annexure C.
- Clause citations identify source labels; they are not a legal interpretation service.

See [DECISIONS.md](DECISIONS.md), [AI_USAGE.md](AI_USAGE.md), and [WHERE_IT_BREAKS.md](WHERE_IT_BREAKS.md) for assumptions, disclosure, and limitations. `eval.json` is checked with `evaluate.py`.