# Test dataset

Synthetic ledger in the same schema as Northbridge (`ledger_test.db`) plus ground-truth labels (`labels.csv`). Built by `../test_scripts/build_dataset.py` (seeded, reproducible). No real data.

**Frozen before the first run** (hashes in `../evidence_log.md` E-01). Do not edit; regenerate and re-hash if changed.

| Item type | Meaning |
|---|---|
| bill | Supplier bill (ACCPAY) |
| invoice | Sales invoice (ACCREC) |
| bank_txn | Standalone bank line |

230 items: 31 errors, 167 standard clean, 32 hard clean (legitimate items that look like errors).

## Labelling principle
Labels reflect the accounting meaning (is the record really wrong?), not what the rules can see. Legitimate items that resemble errors are labelled clean, so the false positives they cause are counted.

## Error types (31)
| Type | n | Construction |
|---|---|---|
| DUP_AR | 5 | Sales invoice repeated for the same customer and amount within days (3 pairs, 1 triple) |
| DUP_AP | 3 | Supplier bill repeated for the same supplier and amount within days |
| DUP_PAY | 4 | Bill already paid via a recorded payment, paid again by a bank line |
| BREAK | 6 | 3 payments to unknown payees, 2 short payments beyond tolerance, 1 bank line with no contact |
| VAT_MISCODE | 4 | One bill from a normally VAT-registered supplier coded with no VAT |
| THRESHOLD | 3 | Bills just under the £500 approval limit (a split job and a single bill) |
| WEEKEND | 3 | Bills dated on a weekend for suppliers that do not trade at weekends |
| OUTLIER | 3 | Amounts about 9x the norm for the account, no explanation |

## Hard clean cases (32)
Fixed recurring subscription; legitimate fixed-price bills at £489 plus boundary values £474.99 and £500.00; weekend bills from suppliers that trade at weekends (4); supplier VAT-registered part way through the year (3 bills before registration); legitimate large equipment purchases (2); bi-weekly billing at the same amount (4); same amount on the same day for different customers (2); an invoice with its reversing credit note (2); bank lines differing from the bill by a few pence or pounds (4); monthly bank charges with no bill (6).

## Limits
Reviewer wrote both system and dataset and had read the rules first. Small samples per error type. Only error types Northbridge is designed to detect are included; "missing documentation" from the original plan is out (no such function).
