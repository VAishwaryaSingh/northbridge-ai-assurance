# Terms of Reference

**Review:** Assurance review of the Northbridge Ledger Agent
**Version:** 1.0, 23 September 2026 (criteria fixed before testing)
**Subject version:** Northbridge commit `9c4127ad65aa5a9e7d362c2d05f69ecfdbf7c5f9`

## 1. Independence disclosure

The reviewer is also the developer of the system. This is a **self-assessment using audit methodology, not an independent audit**, and is described that way throughout. The detection rules were also written with AI coding tools (Claude Code), which is noted as a provenance fact, not a control.

Partial mitigations: criteria are fixed in this document before testing; a separate challenge review of the testing is performed in Phase 4; gaps are recorded as findings and not quietly fixed before testing.

## 2. Objective

Assess whether Northbridge is governed, controlled, and performs reliably enough to support month-end reconciliation and anomaly review, treating it as an automated control within an IT application.

## 3. What the system is (scoping decision)

Northbridge is titled an "Agent" and its README positions it as a small-scale version of "AI-native" ledger products (see Amendment 1, item 5). Inspection at the pinned commit shows it calls **no LLM**. It is deterministic rules (A1 to A6), a median/MAD statistical outlier check (A7), fuzzy bank-to-invoice matching and templated variance text. This review therefore:

- assesses it as a **rules-based automated control**;
- uses NIST AI RMF and ISO/IEC 42001 as governance lenses, applying only the parts that are relevant;
- records the "AI-native / agent" positioning as a **transparency matter** to be evaluated as a finding.

## 4. Scope

**In scope**
- Xero and QuickBooks connectors, data loading, reconciliation matcher, anomaly rules A1 to A7, variance explanations, the Streamlit dashboard.
- Accuracy of detection on a new test set that was not written to fit the rules.
- Human oversight, logging and audit trail, change control and version pinning, access and permissions, secrets handling, documentation and transparency.
- Implications for how an external auditor would rely on the output (ISA 315, 330, 500, 265).

**Out of scope**
- Sage or any other connector; production or real client data.
- LLM-specific testing (prompt injection, hallucination, explanation faithfulness, provider privacy). Not applicable because no LLM is called. Reassessed if an LLM layer is added.
- Penetration testing of Xero or Intuit infrastructure; Streamlit Cloud platform security.
- The auditor's own use of AI tools.

## 5. Frameworks and criteria sources

| Source | Use |
|---|---|
| NIST AI RMF 1.0 (Govern, Map, Measure, Manage) | Structure for governance and risk mapping |
| ISO/IEC 42001:2023 Annex A | Control reference, applicable areas only |
| ISO/IEC 23894, 42005 | Risk and impact guidance |
| PRA SS1/23 | Model inventory, validation, change control |
| UK AI principles (five) | Transparency, accountability, robustness lens |
| OWASP Top 10 for LLM Applications | Considered: not applicable (no LLM). Non-LLM items such as excessive permissions and secrets handled under security |
| ISA 315 (Revised 2019), 330, 500, 265 | Financial statement audit implications |

Regulatory status (including EU AI Act dates) will be re-checked before citing in the report.

## 6. Criteria (fixed before testing)

These are the criteria adopted for this review. They are not an industry standard. In a client engagement they would be agreed with the system owner based on risk appetite.

| Metric | Calculation | Threshold |
|---|---|---|
| Recall, duplicates (A1, A5) and reconciliation breaks (A6) | detected ÷ all real errors | ≥ 95% |
| Recall, other rules (A2, A3, A4, A7) | detected ÷ all real errors | ≥ 85% |
| Precision | correct flags ÷ all flags | ≥ 80% |
| F1 | 2PR ÷ (P + R) | ≥ 0.85 |
| False positive rate | wrong flags ÷ clean items | ≤ 10% |
| Determinism | identical output on rerun over unchanged data | 100% |
| Audit trail completeness | runs traceable to input and code version ÷ total runs | 100% |
| Human disposition | flags with a recorded accept/reject before close ÷ flags | 100% |

Recall is weighted above precision because a missed error typically costs more than a false alarm. The test set is small, so metrics are reported as indicative with the sampling caveat.

**Baseline for context (not a criterion):** the original validation reported 7 of 7 planted anomalies caught, precision 0.70 (Xero) and 0.778 (synthetic). The README states the planted patterns were written to fit the rules, so those results do not measure accuracy on unseen data.

## 7. Approach

Phase 1 planning; Phase 2 risk register and classification; Phase 3 control matrix (gaps recorded, not fixed before testing); Phase 4 test dataset, evaluation harness, control testing, challenge review; Phase 5 findings in Condition, Criteria, Cause, Effect, Recommendation form, remediation and retest, report. The Northbridge code is **not modified** during testing.

## 8. Limitations

- Synthetic and sandbox data only; no real client data.
- Single reviewer, point-in-time assessment of one commit.
- Small samples; results are indicative.
- The live Xero trial organisation is time-limited, so live re-pulls may not be repeatable.
- QuickBooks has no answer key, so no accuracy claim can be made from it.

## 9. Ground rules

Synthetic data only. No secrets in this repository. No overclaiming: the report uses the word "conclusion", not "audit opinion", and claims no assurance or certification. Evidence is logged as testing occurs.

## Amendment 1 (23 Sep 2026, after independent challenge review)
Criteria in section 6 are unchanged. Corrections to statements made before testing:
1. Section 4 said accuracy would be tested on a set "not written to fit the rules". The set was designed by the reviewer after reading the rules, so it is **not** independent of them. Results are reported as properties of a constructed test mix and are not estimates of accuracy on real books.
2. Determinism is defined as identical output on rerun over unchanged data. It is tested both with fixed row order and with reordered rows, because the order in which an ERP API returns records is not under the reviewer's control.
3. All eight criteria are assessed and reported, including audit trail completeness and human disposition.
4. Additional limitation: connector ingestion, multi-line bills, voided or null data and several rule variations were not tested (see challenge_review.md, CH-11).
5. The statement in section 3 that the README "describes" the product as "AI-native" was too strong. The README says the project is "a small-scale version of the kind of AI-native ledger automation product accounting firms are increasingly adopting", i.e. it names the product category it imitates. The title also calls the tool an "Agent". The concern stands (a reader can assume AI, and the README never says no model is used) but it is ambiguous positioning, not a false claim. Corrected 23 Sep 2026 after the owner asked why the wording was used.
