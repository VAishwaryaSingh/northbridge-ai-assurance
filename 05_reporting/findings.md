# Findings

**Subject:** Northbridge Ledger Agent, commit `9c4127ad65aa5a9e7d362c2d05f69ecfdbf7c5f9`. **Status:** findings as at pinned commit `9c4127a` (23 Sep 2026). Remediation was demonstrated on a copy and is not applied to the live project: see `remediation.md`. Ratings and conditions below describe the original.
**Nature:** self-assessment using audit methodology, not an independent audit. Testing challenged by a separate Claude session (model-based): `04_testing/challenge_review.md`.
**Basis of results:** the test set is a constructed mix designed by the reviewer after reading the rules. Metrics are properties of that mix, not estimates for real books, and samples are small (`01_planning/terms_of_reference.md`, Amendment 1).

## Rating scale
- **High:** a defect or gap that could cause a material error to go undetected or unevidenced in the reconciliation process, or that makes results unreliable.
- **Medium:** weakens reliability, control or transparency; would matter if the tool were used beyond a demo.
- **Low:** minor defect or hygiene point.

## Summary

| ID | Finding | Rating |
|---|---|---|
| F-01 | Duplicate supplier bills are not detected | High |
| F-02 | Reconciliation output depends on record order and mis-attributes recurring payments | High |
| F-03 | No run log or audit trail | High |
| F-04 | No human disposition of flags; no owner or intended-use statement | High |
| F-05 | Reported accuracy rests on circular validation and a static score | High |
| F-06 | No regression tests, version tags or pinned dependencies | Medium |
| F-07 | Variance explanations can point against the headline movement | Medium |
| F-08 | False positives on legitimate items exceed the criterion | Medium |
| F-09 | Excess QuickBooks permission and plaintext refresh tokens | Medium |
| F-10 | No intended-use or limitations statement for users | Medium |
| F-11 | Data completeness is not evidenced | Medium |
| F-12 | Hard-coded, unapproved thresholds and message defects | Low |
| F-13 | QuickBooks bank purchases all reported as unmatched | Low |

Criteria met on the full ToR list: 1 of 8 on point estimate (recall on other rules, with an interval spanning the threshold); 7 of 8 not met (`04_testing/results/criteria_assessment_full.csv`).

---

## F-01 Duplicate supplier bills are not detected (High)
- **Condition:** 0 of 3 duplicated supplier bills (AP-121 to AP-123) were flagged. Duplicate sales invoices: 5 of 5; duplicate payments and reconciliation breaks were also detected.
- **Criteria:** recall on duplicates and reconciliation breaks of at least 95%. Result 15/18 = 83.3%, not met. The shortfall is entirely this gap and is robust to relabelling (CH-04).
- **Cause:** rule A1 selects `invoice_type = 'ACCREC'` only (`src/anomaly/rules.py:35-58`). No other rule compares supplier bills with each other.
- **Effect:** a bill entered twice for the same supplier and amount is not reported. Duplicate payables are a principal cash-loss risk. The published 7/7 result does not reveal this.
- **Recommendation (High):** run A1 over both sales invoices and supplier bills (also compare non-adjacent entries); add cases to a regression suite. Retest with the same dataset.
- **Refs:** R04; C17; E-02.

## F-02 Reconciliation output depends on record order and mis-attributes recurring payments (High)
- **Condition:** loading the same 230 items in a different row order changed the result: reversed order gave 53 flags and lost a true duplicate payment (BT-044); 5 of 6 random orderings also differed. In the original order, two legitimate receipts (BT-023, BT-035) were attributed to an earlier, already paid invoice of the same amount and flagged as duplicate payments (A5).
- **Criteria:** identical output for the same data (determinism 100%), and matched documents attributed correctly.
- **Cause:** the matcher accepts the first candidate within tolerance (`src/reconciliation/matcher.py:78-91`), with no ordering, no preference for the closest date and no one-to-one allocation of bank lines to invoices.
- **Effect:** results vary with the order an ERP returns records. Detected errors can disappear and false ones appear without any change in the ledger. The demonstration is on constructed data, but the mechanism is in the code.
- **Recommendation (High):** order candidates deterministically (closest date, then id), exclude invoices already matched or paid, allocate one-to-one, and add a row-order invariance test.
- **Refs:** R08 (raised to High); C14, C19; E-02, E-06 (`results/order_sensitivity.txt`).

## F-03 No run log or audit trail (High)
- **Condition:** no logging, input hash, code version, timestamp or run record exists; the schema has no audit table.
- **Criteria:** 100% of runs traceable to input and code version; a reviewer must be able to re-perform a result.
- **Cause:** not designed in (`src/db/schema.sql`; no logging code found, E-04).
- **Effect:** a flag or a missed item cannot be tied to the data and code that produced it, so results cannot be evidenced or re-performed. This is a prerequisite for any reliance (ISA 315 IT controls).
- **Recommendation (High):** record per run the input hash, code version (git SHA), dependency versions, timestamp, user and output hash in an append-only table.
- **Refs:** R24; C26.

## F-04 No human disposition of flags; no owner or intended-use statement (High)
- **Condition:** the dashboard displays flags with no accept, reject or reason step. Owner, intended use, users of the output and escalation route are undocumented.
- **Criteria:** 100% of flags dispositioned before close; documented accountability.
- **Cause:** display-only design; governance documents not written.
- **Effect:** oversight cannot be evidenced, and there is no way to record that a flag was wrong or handled. The human review control, normally the key control, does not exist in the tool.
- **Recommendation (High):** add a disposition record per flag (accept, reject, reason, user, time), tie it to the run log, and document owner and intended use.
- **Refs:** R14, R25; C10, C21.

## F-05 Reported accuracy rests on circular validation and a static score (High)
- **Condition:** the published 7/7 and 84/84 results reproduce exactly, but the planted anomalies were written to fit the rules (README). The public dashboard shows a hard-coded score when the private answer key is absent (`dashboard/app.py:35-41, 173-178`) and does not say so.
- **Criteria:** accuracy claims evidenced on data the rules were not written to fit, with clean items so false positives are measured.
- **Cause:** validation designed to show mechanics; the fallback score is a constant.
- **Effect:** readers can take 7/7 as evidence of general accuracy. This review's own set (which is also not independent of the rules) shows precision 0.56 and 4 of 5 accuracy criteria not met on that mix, so the headline is misleading if read as accuracy.
- **Recommendation (High):** restate results as mechanics tests; label the fallback score as static; add clean and hard cases and an independently built test set before making any accuracy claim.
- **Refs:** R03, R15, R27; C09, C16, C28; E-02.

## F-06 No regression tests, version tags or pinned dependencies (Medium)
- **Condition:** no tests directory, 13 commits and 0 tags, unpinned `requirements.txt`, no lockfile.
- **Criteria:** changes retested before release; outputs tied to a version; dependencies controlled (PRA SS1/23 as a reference).
- **Cause:** portfolio build without release discipline.
- **Effect:** any edit can change detections unnoticed; the defects in F-01 and F-02 would have been caught by tests. A redeploy can change behaviour through library updates.
- **Recommendation (Medium; High if used beyond a demo):** add the review's dataset and harness as a regression suite, tag releases, pin dependencies with a lockfile, and print the version in output.
- **Refs:** R11, R20, R21, R23; C15, C24, C25.

## F-07 Variance explanations can point against the headline movement (Medium)
- **Condition:** 17 of 52 sentences on the test data (35 of 69 on the synthetic set, 4 of 14 on QuickBooks) name at least one driver that moved opposite to the headline, e.g. "Consulting Fees down 56%, driven by Fairway Foods (+£1,114)". Only contacts present in the later period are ever named.
- **Criteria:** explanations supported by the data and not misleading.
- **Cause:** the two largest absolute contact changes in the later period are named "driven by" regardless of sign (`src/variance/explainer.py:88-99`).
- **Effect:** the sentence reads as an explanation but can name an offsetting movement, and contacts that disappeared cannot be named. Figures themselves agree with source (15/15). No hallucination is involved; the text is templated.
- **Recommendation (Medium):** rank drivers by movement in the direction of the headline, include contacts present only in the earlier period, and state when drivers do not account for the change.
- **Refs:** R10; C20; E-05.

## F-08 False positives on legitimate items exceed the criterion (Medium)
- **Condition:** 22 false positives (11.1%; criterion 10%), precision 0.56 per item (0.537 per flag; criterion 80%). Standard clean items: 2 of 167 (1.2%). Hard clean items: 20 of 32. Causes: bank charges 6, fixed-price and boundary bills 5, legitimate weekend suppliers 4, supplier VAT registration change 3, large equipment 2, recurring receipts 2 (F-02).
- **Criteria:** precision at least 80%; false positive rate at most 10%.
- **Cause:** context-free rules (weekend date, £500 band, outlier vs account median, no bill for bank charges).
- **Effect:** reviewer time and desensitisation. Outcome is label-sensitive: FPR flips to 8.3% if the six bank charges are excluded (`results/sensitivity.csv`), so it is borderline; precision remains below 80% except when 15 hard cases are excluded together.
- **Recommendation (Medium):** allow-lists or rules for recurring fixed charges and known weekend suppliers, a bank-charge account, and a way to record accepted exceptions (ties to F-04).
- **Refs:** R02, R06, R09; C17; E-02.

## F-09 Excess QuickBooks permission and plaintext refresh tokens (Medium)
- **Condition:** the QuickBooks scope requested is `com.intuit.quickbooks.accounting`, which permits writes, though the code only reads. Refresh tokens for both ERPs are written in plaintext to a local `.env` (`src/connectors/*_connector.py`, `set_key`). No credentials were found in git history by pattern search of code files.
- **Criteria:** least privilege; secrets protected at rest.
- **Cause:** the accounting scope is the only one available for reading; token persistence uses a plain file.
- **Effect:** if the tokens or code were misused, the ledger could be changed (QuickBooks) and long-lived access is exposed on the machine. Xero requests only `.read` scopes.
- **Recommendation (Medium):** use a read-only scope if the vendor offers one, otherwise document the constraint and add a test that no non-GET data call exists; store tokens in an OS keychain or secrets manager; rotate the tokens.
- **Refs:** R16, R17, R18; C02, C03, C05, C06.

## F-10 No intended-use or limitations statement for users (Medium)
- **Condition:** the README does not state intended use, what the tool cannot detect (for example false negatives on real books), that it is a demonstration on fictional data, or its production status. "Rule-based checks" are mentioned only in the accuracy section (line 108), and the README does not say that no LLM or model is used (a plain statement that it is rules-based, calls no LLM and is not production software was added to the README after the pinned commit).
- **Criteria:** users are told what the tool is, what it can and cannot detect, and that outputs need review (UK transparency principle; ISO/IEC 42001 information for users).
- **Cause:** no limitations section was written.
- **Effect:** users may rely on the tool for more than it can do, and may over-rely on a clean run.
- **Recommendation (Medium):** add intended use, known limitations (see F-01, F-02, F-08), that no LLM is used, and not-for-production wording.
- **Refs:** R25, R26; C09, C27.

## F-11 Data completeness is not evidenced (Medium)
- **Condition:** pagination was tested with mocks only and could not be re-run live (credentials and Xero trial unavailable). There is no validation gate for missing contacts, voided items or malformed rows, and the coverage table is not reconciled to source totals. Ingestion, multi-line bills and null data were not tested in this review.
- **Criteria:** the complete population is processed and reported.
- **Cause:** no completeness control at load time.
- **Effect:** an incomplete pull would produce confident results on a partial ledger with no warning.
- **Recommendation (Medium):** compare loaded counts and totals with the source system, fail or warn on differences, and test ingestion against live sandboxes.
- **Refs:** R12, R13; C11, C12, C13; challenge review CH-09, CH-11.

## F-12 Hard-coded, unapproved thresholds and message defects (Low)
- **Condition:** tolerances, windows and the £500 band are constants in code with no rationale or approval. One message reads "Bank line for None (£415.00)" when there is no contact. The weekend rule message states "Northbridge doesn't operate on weekends" as a fact.
- **Criteria:** parameters documented and approved; messages accurate.
- **Cause:** constants and message templates written for the demo data.
- **Effect:** fixed values can be avoided by small changes in amount or date; unclear messages slow review.
- **Recommendation (Low):** move parameters to documented configuration with an approver and date, and correct the messages.
- **Refs:** R06; C18, C22.

## F-13 QuickBooks bank purchases all reported as unmatched (Low)
- **Condition:** 0 of 40 QuickBooks bank lines auto-match. The challenge review found no bank line has a same-contact, same-amount invoice or bill in the sandbox, and 7 lines have no contact.
- **Criteria:** reconciliation behaviour appropriate to each ERP's data model.
- **Cause:** sandbox purchases are direct expenses with no bill; the matcher only looks for invoices and bills.
- **Effect:** every such line is reported as unmatched, which is noise rather than a missed match. It is not shown to be a matcher failure.
- **Recommendation (Low):** treat direct expenses as a separate class in the QuickBooks adapter, or state the limitation.
- **Refs:** R08; C19; E-04, CH-08.

---

## Areas working as intended (tested)
- Xero requests only read scopes, and no write calls exist in either connector.
- `.env` is ignored and was never committed; `.env.example` holds no secrets.
- The published accuracy figures reproduce exactly from the pinned code and data.
- The dashboard's data-quality counts agree with an independent recount on the same databases.
- Duplicate sales invoices, duplicate payments (in the original row order), VAT miscoding, outliers, threshold and weekend cases were detected on the constructed set. This shows the rules operate on constructed cases, not accuracy on real books.
- Every flag carries a reason string; the engine runs in milliseconds on 230 items.

## Not covered
Connector ingestion against live systems, multi-currency, multi-line bills, voided or null data, further rule variations, real-book accuracy, security of the public deployment.
