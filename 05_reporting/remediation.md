# Remediation and Retest (Plan 5.2)

**Approach:** the Northbridge project was **not changed**. Fixes were made in a scratch copy of the pinned commit (`04_testing/_subject_remediated`, not committed to any repository) and delivered as a patch, `05_reporting/remediation.patch` (606 lines). The patch applies cleanly to a fresh checkout of `9c4127a` and its 10 unit tests pass there. The original working tree was verified unchanged (same HEAD, no modified files) after the work.

**To apply it (owner's decision):** `git apply remediation.patch` in a Northbridge checkout at `9c4127a`, review the diff, run `python -m unittest discover -s tests -t .`, then commit and tag a release.

**Limits of the retest:** the fixes were designed while looking at this review's dataset, and the retest uses the same frozen dataset and harness (hashes in `evidence_log.md` E-01, unchanged). An improvement shows the fixes work on those cases, not that accuracy on real books has improved. Nothing here means the live project is fixed.

## What was changed in the copy

| Finding | Change | Status in copy |
|---|---|---|
| F-01 | Duplicate check (A1) covers supplier bills as well as sales invoices, and flags every later copy in a group | Remediated, verified |
| F-02 | Matcher is deterministic: bank lines processed in (date, id) order; candidates ranked by (already settled, closest date, id); an invoice matched by an earlier line or already paid counts as settled | Remediated, with one trade-off (below) |
| F-03 | Append-only run log (`src/run_log.py`): run id, UTC time, tool version, git commit, input hash (row-order independent), output hash, dependency versions, user. **Off by default**; enabled by `log_path` or the `NORTHBRIDGE_RUN_LOG` environment variable | Partly remediated (capability added; not enabled by default; not wired into the dashboard) |
| F-05 | README now states intended use and known limitations, including that the published scores test mechanics, not accuracy | Partly (dashboard fallback score label not changed) |
| F-06 | 10 regression tests (`tests/`), dependencies pinned (`requirements.txt`, `requirements.lock`), `src/version.py` | Remediated in copy (no release tag created: that is the owner's action) |
| F-07 | Variance sentences name only the largest contributors moving in the headline's direction, include contacts that disappeared, state the share explained, or say no single contact explains the change | Remediated, verified |
| F-10 | README describes the tool as rules-based with no LLM; adds intended use and limitations | Remediated in copy (dashboard title still says "Agent") |
| F-12 | Parameters moved to `src/config.py` with an empty `PARAMETER_APPROVAL` record; "Bank line for None" and the weekend message corrected | Remediated in copy (parameters remain unapproved until the owner completes the record) |
| F-04, F-08, F-09, F-11, F-13 | Not changed: they need design or process decisions, vendor scope options, live credentials or an allow-list design | Open: recommendations stand |

## Before and after (same frozen dataset and harness)

| Measure | Before (`9c4127a`) | After (copy) | Criterion |
|---|---|---|---|
| Recall, item level | 0.903 (28/31) | 0.968 (30/31) | n/a |
| Duplicate supplier bills detected | 0/3 | 3/3 | |
| Recall, duplicates and breaks | 0.833 (15/18) | 0.944 (17/18) | ≥ 0.95, still not met by one item |
| Recall, other rules | 1.000 (13/13) | 1.000 (13/13) | ≥ 0.85 (interval spans threshold) |
| Precision (per item) | 0.560 | 0.600 | ≥ 0.80, not met |
| F1 | 0.691 | 0.741 | ≥ 0.85, not met |
| False positive rate | 0.111 (22/199) | 0.101 (20/199) | ≤ 0.10, not met (borderline; 10.05%) |
| False positives on standard clean items | 2/167 | 0/167 | |
| Identical output across 7 row orderings | No (6 of 7 differ from the base) | **Yes (7 of 7)** | 100% |
| Identical output across 5 fresh processes | Yes | Yes | |
| Variance sentences naming a driver against the headline (test data) | 17 of 52 | 0 of 59 | |
| Same check, Northbridge synthetic / QuickBooks demo data | 35 of 69 / 4 of 14 | 0 of 70 / 0 of 19 | |
| Published Xero score (answer key) | 7/7, 3 FP, precision 0.70 | 7/7, 3 FP, precision 0.70 | unchanged |
| Published synthetic score | 84/84, 24 FP, precision 0.778 | 84/84, **34 FP, precision 0.712** | see below |
| Unit tests | none | 10 pass | |

Criteria on the full list of eight after remediation: 2 met (determinism, recall on other rules on point estimate), 6 not met. Audit trail completeness would be met only for runs made with logging enabled; the human disposition criterion is unchanged at 0%.

## Effects to note (not hidden)
1. **One detection was traded away.** The true duplicate payment BT-044 is no longer flagged as a duplicate payment. Its bank line now attaches to an unpaid bill of the same supplier and amount (AP-123). In this dataset that bill is the deliberately planted duplicate of the paid bill AP-048, so the ledger genuinely has two candidate bills, and the tool now flags AP-123 as a duplicate bill (A1) instead. The dataset's case collision and the tool's ambiguity both contribute; the ground-truth label was not changed after seeing the result. Recall on duplicates and breaks misses the 95% criterion by this one item.
2. **Published synthetic precision falls from 0.778 to 0.712.** The synthetic dataset plants no supplier-bill duplicates, so the 10 new A1 flags (same supplier, same amount, 3 to 8 days apart) count as false positives against its planted list. They are genuine same-supplier, same-amount repeats in that dataset; whether they are generator artefacts was not investigated.
3. Behaviour of the first-come allocation on real data with several equal-amount unpaid invoices is not tested.

## Evidence
`04_testing/results_remediated/` (metrics, criteria, item results, order sensitivity, `retest_after.txt`, `retest_before.txt`, `unit_tests.txt`); evidence log E-07.
