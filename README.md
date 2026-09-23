# Northbridge Assurance Review

A structured assurance review of the **Northbridge Ledger Reconciliation & Anomaly Detection Agent**, applying audit methodology (risk assessment, control testing, evidence, 5-C findings) to a finance automation tool. It also produces a reusable toolkit for assessing other systems.

> **This is a self-assessment using audit methodology, not an independent audit or certification.** The reviewer is also the developer of the system under review. Testing was challenged by a separate Claude session, which is a model-based challenge and not an independent human review.

## Subject of this review

| | |
|---|---|
| System | Northbridge Ledger Agent |
| Repository | https://github.com/VAishwaryaSingh/Northbridge-Ledger-Agent |
| Live demo | https://northbridge-ledger-agent.streamlit.app/ |
| **Pinned version reviewed** | commit `9c4127ad65aa5a9e7d362c2d05f69ecfdbf7c5f9` (23 Sep 2026) |

All evidence refers to that commit. **The Northbridge project itself was not changed.** Remediation was demonstrated on a copy and delivered as a patch (`05_reporting/remediation.patch`) that the owner can apply or not.

## Why this exists

Northbridge's original validation planted seven errors and caught all seven. That is a useful first check but a limited one: the sample was small, it had no clean items (so false positives could not be measured), and it tested detection only, not oversight, logging, change control or security. This project replaces it with a structured review.

## Scoping note: Northbridge is rules-based

Northbridge is called an "Agent", and its README positions it as "a small-scale version of the kind of AI-native ledger automation product accounting firms are increasingly adopting", but it calls **no LLM**. It is deterministic rules plus a median/MAD statistical check. LLM-specific risks (prompt injection, hallucination, provider data handling) were recorded as not applicable rather than tested. The review treats it as a rules-based automated control.

## Headline results

Measured on a 230-item synthetic test set (31 real errors, 199 clean items of which 32 are hard cases), built by the reviewer after reading the rules. **These describe behaviour on a constructed mix, not accuracy on real books.**

**Conclusion:** as at the pinned commit, Northbridge should not be relied on as a control for month-end reconciliation. It works as a demonstration and a lead generator for the error types it targets. Of eight criteria set before testing, seven were not met.

| Criterion | Result | Threshold | |
|---|---|---|---|
| Recall, duplicates and reconciliation breaks | 83.3% (15/18) | ≥ 95% | Not met |
| Recall, other rules | 100% (13/13) | ≥ 85% | Met on point estimate; interval spans threshold |
| Precision | 56.0% per item (53.7% per flag) | ≥ 80% | Not met |
| F1 | 0.691 | ≥ 0.85 | Not met |
| False positive rate | 11.1% (22/199) | ≤ 10% | Not met (borderline, label-sensitive) |
| Determinism (same data, any row order) | Differs in 6 of 7 orderings | 100% | Not met |
| Audit trail completeness | 0% | 100% | Not met |
| Human disposition of flags | 0% | 100% | Not met |

**13 findings** (5 High, 6 Medium, 2 Low). The High ones:
- **F-01** Duplicate supplier bills are never detected (0 of 3): the duplicate check covers sales invoices only.
- **F-02** Reconciliation output depends on record order and mis-attributes recurring payments; a real duplicate payment can vanish.
- **F-03** No run log or audit trail.
- **F-04** No human sign-off, owner or intended-use statement.
- **F-05** The published 7/7 accuracy result is circular, and the public dashboard shows a hard-coded score.

**Remediation on a copy** (same frozen dataset): duplicate supplier bills 0/3 to 3/3; identical output across all 7 row orderings; variance sentences naming an opposing driver 17 of 52 to 0 of 59. **Costs:** one duplicate payment is no longer flagged as such, and the project's published synthetic precision falls from 0.778 to 0.712. The fixes were designed against the same dataset used to retest, so they do not show that real-world accuracy has improved.

## Read this first

| If you want | Read |
|---|---|
| The conclusion and evidence in one document | `05_reporting/assurance_report.pdf` (12 pages) |
| Every finding in Condition, Criteria, Cause, Effect, Recommendation form | `05_reporting/findings.md` |
| What remediation was done and its costs | `05_reporting/remediation.md` and `remediation.patch` |
| How an external auditor would treat the tool | `05_reporting/fs_audit_implications.md` |
| Scope, criteria and independence | `01_planning/terms_of_reference.md` (with Amendment 1) |
| How the system works and where data flows | `01_planning/system_description.md` |
| The risks | `02_risk/risk_register.xlsx`, `02_risk/ai_act_classification.md` |
| The controls and their test results | `03_controls/control_matrix.xlsx` |
| Every test, with times and hashes | `04_testing/evidence_log.md` |
| How the testing was challenged | `04_testing/challenge_review.md` (raw report in `challenge_review_raw.md`) |
| A checklist for assessing any AI system | `toolkit/ai_audit_checklist.md` |
| A template for assessing a process for AI adoption | `toolkit/ai_readiness_review.md` |

## Repository structure

```
northbridge-assurance-review/
├── README.md
├── 01_planning/      terms of reference, system description
├── 02_risk/          risk register (28 risks), regulatory classification
├── 03_controls/      control matrix (29 controls, design and operating results)
├── 04_testing/       dataset, harness, results, evidence log, challenge review
├── 05_reporting/     findings, remediation, FS audit implications, report, patch
├── toolkit/          reusable checklist and readiness template
├── tools/            website builder
└── docs/             the static website (generated)
```

## Reproducing the results

The subject and any Python environment with Northbridge's dependencies (pandas, scikit-learn) are needed. The Northbridge working tree is only read.

```bash
# 1. Clone the subject at the pinned commit (defaults to the public GitHub repo; set NORTHBRIDGE_SRC to use a local copy)
04_testing/test_scripts/setup_subject.sh

# 2. Rebuild the test set (seeded; regenerates byte-identical files, hashes are in the evidence log)
python 04_testing/test_scripts/build_dataset.py 04_testing/_subject 04_testing/test_dataset

# 3. Run the evaluation and control tests
python 04_testing/test_scripts/run_evaluation.py 04_testing/_subject 04_testing/test_dataset 04_testing/results
python 04_testing/test_scripts/control_tests.py 04_testing/_subject 04_testing/test_dataset <northbridge working tree>
python 04_testing/test_scripts/order_sensitivity.py 04_testing/_subject 04_testing/test_dataset <scratch dir>
python 04_testing/test_scripts/sensitivity_and_full_criteria.py 04_testing/results

# 4. Retest the remediation: apply the patch to a copy of the subject and rerun step 3 against it
cp -r 04_testing/_subject 04_testing/_subject_remediated
git -C 04_testing/_subject_remediated apply ../../05_reporting/remediation.patch
```

The control tests read the project's private answer key from the Northbridge working tree if it is present (it is not published). `05_reporting/build_report.py` rebuilds the PDF and needs reportlab and openpyxl.

## Website

**Live site:** https://vaishwaryasingh.github.io/northbridge-ai-assurance/ (repository: https://github.com/VAishwaryaSingh/northbridge-ai-assurance)

The site lives in `docs/` (plain HTML, CSS and a little JavaScript; no external dependencies). Rebuild it with `python tools/build_site.py` (needs `markdown` and `openpyxl`). It is served by GitHub Pages from branch `main`, folder `/docs`. Preview locally with `python -m http.server --directory docs`.

## Limitations

- Synthetic and sandbox data only. One reviewer, one commit, point in time.
- The test set is not independent of the rules; 3 to 6 errors per type give wide uncertainty; false positives cluster in about six causes.
- Not tested: connector ingestion against live systems and pagination, portal-granted scopes, multi-line bills, voided or null data, multi-currency, further rule variations, real-book accuracy.
- The toolkit was built from this one review and has not been validated on another system.
- NIST and ISO references are at area level and need checking against the source documents. EU AI Act dates were not verified and are not relied on.
- A human independent review has not been done.

## Ground rules

Synthetic data only. No secrets in the repository (`.env` is excluded). No overclaiming: the report says "conclusion", never "audit opinion". Evidence is logged as testing is performed. Each phase's output was reviewed critically before the next.

## Status

- [x] Phase 1: Planning
- [x] Phase 2: Risk assessment
- [x] Phase 3: Controls
- [x] Phase 4: Testing and metrics, with challenge review
- [x] Phase 5: Findings, remediation on a copy with retest, assurance report
- [x] Phase 6: Toolkit and README
