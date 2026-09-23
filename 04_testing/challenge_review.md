# Independent Challenge Review: Outcome and Resolution (Plan 4.4)

**Reviewer:** a separate Claude session (fresh context) given only the evidence artefacts, not the reviewing session's reasoning. It was told to read `evidence_log.md` last. Raw report: `challenge_review_raw.md`. **This is a model-based challenge, not a human independent review**, and is described that way in the report.
**Reviewer's verdict:** sound enough to support findings about mechanics and specific defects; not sound enough to support accuracy claims about real books; wording and caveats to change.
**Metrics re-derived independently:** all headline figures reproduced exactly (TP 28, FN 3, FP 22, TN 177; recall 0.903; precision 0.560; F1 0.691; FPR 0.111). No arithmetic discrepancy.

| ID | Sev | Challenge | Disposition | Action taken |
|---|---|---|---|---|
| CH-01 | High | Determinism overstated: output depends on database row order | **Accepted; re-verified.** `test_scripts/order_sensitivity.py`: original order gives 54 flags; reversed order gives 53 and loses true duplicate payment BT-044; 5 of 6 random shuffles differ from base (6 of 7 orderings including reverse). Cause: matcher takes the first match with no ordering and no one-to-one allocation | Determinism criterion re-rated NOT MET; E-03 corrected in E-06; new finding; C14 and R08 updated |
| CH-02 | High | Test set built inside the rules' envelope; "not written to fit the rules" untrue | **Accepted.** ToR wording was wrong for a set designed after reading the rules | ToR amended (Amendment 1); results reported as properties of a constructed mix, stratified; not accuracy estimates |
| CH-03 | High | Weekend, threshold, outlier labels rest on narrative the data cannot show | **Accepted.** Labels for these types are judgement; a different labelling changes precision and FPR | `results/sensitivity.csv` scenario S1; report presents these as review indicators with the alternative labelling shown |
| CH-04 | Med | Criterion outcomes flip under relabelling | **Accepted** | `sensitivity.csv` (S0 to S4); FPR reported as "not met, borderline, label-sensitive" |
| CH-05 | Med | Wilson intervals assume independent items; FPs cluster in about 6 root causes; 13/13 lower bound about 0.77 | **Accepted** | Caveat added; recall on other rules reported "met on point estimate; interval spans threshold". Cluster count: bank charges 6, fixed-price/boundary 5, weekend supplier 4, VAT registration 3, large equipment 2, recurring receipts 2 |
| CH-06 | Med | Only 5 of 8 ToR criteria scored; precision per item not per flag; | **Accepted** | `results/criteria_assessment_full.csv`: 7 of 8 criteria not met; per-flag precision 0.537 (29/54) reported alongside 0.560 per item. C17 result reworded |
| CH-07 | Med | C22 test skipped A6 and passed a null contact; "Bank line for None" | **Accepted; verified** (BT-050 reason text) | C22 rated Partly effective; minor finding on reason text |
| CH-08 | Med | C19 "12/12" tautological; QuickBooks 0/40 is sandbox data, not matcher failure | **Accepted** | C19 reworded; R08 reworded; QuickBooks cause stated as sandbox data (reviewer checked: no same-contact, same-amount pairs) |
| CH-09 | Med | C06, C07, C11, C23 results overstated | **Accepted** | Wording corrected in the control matrix; C23 evidence now logged in `results/git_state.txt` |
| CH-10 | Med | "Likely on real data" is extrapolation; dataset creates the condition | **Accepted** | Reworded to "demonstrated on constructed data"; root cause broadened (order dependence, no one-to-one allocation) |
| CH-11 | Med | Untested coverage: ingestion, multi-line bills, voided/null data, more rule variants | **Accepted as a scope limit**, not tested in this review | Listed as limitations in the report and as recommended follow-up tests |
| CH-12 | Low | Frozen-before-run is self-attested; C16 Xero score used an answer key from the original tree | **Accepted** | Both labelled as such in the report |

## Evidence log wording (Section F of the raw report)
Corrections recorded in E-06: E-01 (labels), E-02 notes 2 and 3, E-03, E-04 (C22, C06, C07, C19, C23), E-05 ("17 of 52" counts sentences with at least one opposing driver; also only contacts present in the later period are ever named, so contacts that disappeared cannot be named).

## Unresolved
Population accuracy on real books remains unmeasured. A human independent review has not been done.
