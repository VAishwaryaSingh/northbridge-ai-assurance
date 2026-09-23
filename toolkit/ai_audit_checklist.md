# AI System Assurance Checklist

A reusable checklist for assessing an AI or automated decision system used in a finance or control process. It generalises the control matrix from the Northbridge review and adds the lessons that review taught. It is a starting point for a self-assessment or a client engagement, **not a certification tool**.

**Provenance and limits.** Built from one review (a rules-based ledger tool) plus general practice. It has not been validated on other systems. LLM sections are included from framework guidance and have not been exercised in practice. Framework references are area-level and must be checked against the source texts. Thresholds are examples: agree them with the system owner before testing.

**How to use:** work top to bottom. For each item record: applies (Y/N/why not), in place (Y/Partial/N), design test, operating test, evidence reference, result. Keep an evidence log as you go. Record gaps as gaps; do not fix them before testing.

---

## 0. Before anything else: what is it really?

| # | Question | Why it matters | Evidence |
|---|---|---|---|
| 0.1 | Does the system call an LLM, a trained model, or only fixed rules and statistics? Read the code or vendor documentation; do not rely on the description. | Northbridge is titled an "Agent" and positioned as a small-scale version of AI-native products, yet calls no LLM. That changed which risks applied. | Code search, dependency list, network destinations |
| 0.2 | Is the description of the system accurate and consistent across README, marketing, dashboard and documents? | Misdescription misleads users about behaviour and reliability. | Documents compared |
| 0.3 | Who developed it, who is reviewing it, and were AI coding tools used? | Independence and provenance must be disclosed. | Independence statement |
| 0.4 | What version is under review (commit, release, model version)? Is it pinned for the review? | Evidence must refer to a fixed subject. | Commit hash or release id |

## 1. Governance and scope

| # | Control / check | Test of design | Test of operating effectiveness |
|---|---|---|---|
| 1.1 | Named owner, intended use, users of the output, known limitations, escalation route | Read the documentation | Ask a user; check the limitations are visible where output is shown |
| 1.2 | Inventory entry: system, purpose, model and provider with versions, data used, change dates | Inspect inventory | Compare with what is actually deployed |
| 1.3 | Regulatory classification reasoned and dated (for example EU AI Act tier, UK principles, data protection) | Read the reasoning | Re-check status against primary sources; note triggers for reassessment |
| 1.4 | Impact and risk assessment done before use | Inspect assessment | Check it was updated after material changes |
| 1.5 | Acceptance criteria (accuracy, false positives, consistency, oversight) agreed with the owner before testing | Inspect criteria | Confirm they pre-date the test results |

## 2. Data

| # | Control / check | Test of design | Test of operating effectiveness |
|---|---|---|---|
| 2.1 | Completeness of data pulled: counts and totals reconciled to the source system | Inspect the check | Re-perform against source totals; test pagination and limits live |
| 2.2 | Validation of malformed, missing, voided or duplicate records | Inspect rules | Feed known bad records |
| 2.3 | Personal and confidential data identified, minimised, and lawful basis recorded | Inspect data map | Sample records for personal data; check retention |
| 2.4 | Data not silently changed by upstream systems (schema, field meaning, tax mapping) | Inspect change notification | Compare field mapping to source documentation |
| 2.5 | Test and demo data clearly separated from real data | Inspect environments | Sample committed or shared datasets |

## 3. Performance and accuracy (all systems)

| # | Control / check | Test of design | Test of operating effectiveness |
|---|---|---|---|
| 3.1 | Independent test set with ground truth, built **without** reference to how the system works | Inspect how it was built and by whom | Re-derive metrics from labels and outputs yourself |
| 3.2 | Clean items at least 50% of the set, so false positives can be measured | Inspect composition | Recount |
| 3.3 | Hard cases: near misses, legitimate items that look like errors, reversals, rounding, boundary values | Inspect | Report results separately for standard and hard items |
| 3.4 | Metrics per error type, not just overall: recall, precision, F1, false positive rate, with sample sizes and uncertainty | Inspect | Recompute; note that small samples give wide intervals |
| 3.5 | Sensitivity of pass/fail outcomes to labelling choices | Inspect | Relabel disputed items and rerun; report which outcomes flip |
| 3.6 | Error types the system claims to cover are all tested; error types it does not cover are stated | Compare claims with tests | List what a real error could look like that the system cannot see |
| 3.7 | Reported accuracy figures reproduce from the code and data | Inspect how they are produced | Rerun; check published constants are labelled as static |

**Lessons from Northbridge:** the developer's own validation planted errors written to fit the rules, so 7/7 said nothing about accuracy. The reviewer's own test set, built after reading the rules, was also not independent. State this openly and have someone else challenge the labels.

## 4. Determinism and consistency

| # | Control / check | Test of design | Test of operating effectiveness |
|---|---|---|---|
| 4.1 | Same input gives the same output across runs and fresh processes | Inspect seeds and ordering | Repeat runs in fresh processes and compare hashes |
| 4.2 | **Output does not depend on input order** or other arbitrary factors | Inspect sort keys and tie-breaks | Reload the same data in reversed and shuffled row order and compare |
| 4.3 | For LLM systems: consistency across repeated runs at the configured temperature, and effect of prompt wording | Inspect configuration | Run N repeats; report agreement per item |
| 4.4 | Consistency across dependency versions | Inspect pinning | Rebuild in a clean environment |

**Lesson:** identical output for one fixed input order looked like determinism until rows were reordered. Test order and environment, not just repetition.

## 5. Explanations and outputs

| # | Control / check | Test of design | Test of operating effectiveness |
|---|---|---|---|
| 5.1 | Every output carries a reason naming the records relied on | Inspect | Sample outputs for each rule or output type, including null and edge values |
| 5.2 | Explanations are supported by the data and do not contradict the headline | Inspect logic | Re-perform a sample from source; check direction and completeness of named drivers |
| 5.3 | For LLM systems: explanations cite specific records; unsupported claims and invented records are counted | Inspect | Manual check of a sample; report supported claims ÷ claims checked |
| 5.4 | Messages state facts, not assumptions about the client | Read templates | Sample messages |

## 6. Human oversight

| # | Control / check | Test of design | Test of operating effectiveness |
|---|---|---|---|
| 6.1 | Every flag or recommendation is dispositioned (accept, reject, reason) by a competent person before it has effect | Inspect process and tool | Sample flags; confirm a recorded disposition exists and is timely |
| 6.2 | Reviewer competence, workload and authority to override | Inspect | Interview; check volume against capacity |
| 6.3 | Escalation and contestability: a way to challenge and correct an output | Inspect | Trace one challenged item end to end |
| 6.4 | False positive burden is manageable, so reviewers are not desensitised | Inspect metrics | Compare flag volume with review capacity |

## 7. Logging, traceability and monitoring

| # | Control / check | Test of design | Test of operating effectiveness |
|---|---|---|---|
| 7.1 | Every run logged: input hash, code and model version, prompt version, dependency versions, timestamp, user, output hash | Inspect schema | Re-perform a past result from its log entry; completeness = logged runs ÷ all runs |
| 7.2 | Logs are append-only and retained | Inspect | Attempt to alter; check retention |
| 7.3 | Ongoing monitoring of accuracy and drift, with thresholds and owner | Inspect | Review recent monitoring outputs and actions |
| 7.4 | Incident process: how an error found later is recorded and fed back | Inspect | Trace a past incident |

## 8. Change management

| # | Control / check | Test of design | Test of operating effectiveness |
|---|---|---|---|
| 8.1 | Version control with review and release tags | Inspect repository settings | Check history, tags, branch protection |
| 8.2 | Automated regression suite (known errors and clean items) run before release | Inspect | Run it; break something and confirm it fails |
| 8.3 | Dependencies and model versions pinned, with a lockfile | Inspect | Rebuild from a clean environment |
| 8.4 | Parameters (thresholds, tolerances, windows, prompts) documented with rationale, approver and date | Inspect | Compare code values with the approved record |
| 8.5 | Silent provider changes (model updates, API changes) detected | Inspect | Compare recorded model version with current |

## 9. Security and access

| # | Control / check | Test of design | Test of operating effectiveness |
|---|---|---|---|
| 9.1 | Least privilege: granted permissions match what the system needs (can it write to the source system?) | Compare requested scope with code | Confirm granted scope in the vendor portal; grep for write calls |
| 9.2 | Secrets in a secrets manager or keychain, not plaintext files or code | Inspect | Scan history and working tree; check token storage |
| 9.3 | Secrets and real data never committed to public repositories | Inspect ignore rules | Pattern and scanner search of full history, including non-code files |
| 9.4 | Authentication and access on the application itself (including public demos) | Inspect | Attempt access as an unauthorised user |
| 9.5 | LLM systems only: prompt injection via data fields, sensitive data disclosure, excessive agency, insecure output handling (see OWASP LLM Top 10) | Inspect prompt construction | Adversarial items in the test set, for example injected instructions in description fields; report successful attempts ÷ attempts |

## 10. Third parties

| # | Control / check | Test of design | Test of operating effectiveness |
|---|---|---|---|
| 10.1 | Provider terms reviewed: data use, retention, training, sub-processors | Read terms | Confirm settings match the terms |
| 10.2 | Provider outage and change plan | Inspect | Tabletop or failover test |
| 10.3 | Licence and supply-chain review of libraries | Inspect | Dependency scan |

## 11. Transparency and documentation

| # | Control / check | Test of design | Test of operating effectiveness |
|---|---|---|---|
| 11.1 | Users are told what the system is, what it can and cannot detect, and that outputs need review | Read | Check the statement is visible where results are shown |
| 11.2 | Static or published figures are labelled as static | Inspect UI | Compare displayed values with live computation |
| 11.3 | Known limitations and error types not covered are listed | Read | Compare with the test results |

---

## Evidence and reporting conventions

- **Evidence log:** for each test record time, what, how, sample size, result, evidence reference. Write entries as you test, not afterwards.
- **Freeze before running:** record hashes of the test data, labels and harness before the first run, and say the record is self-attested.
- **Criteria before results:** set thresholds first; report every criterion, including the ones that are not met.
- **Findings:** Condition, Criteria, Cause, Effect, Recommendation, with a High, Medium or Low rating and references to risks and controls.
- **Sensitivity and uncertainty:** show how outcomes change under alternative labelling; note clustering of errors and small samples.
- **Challenge:** have the testing challenged by someone who has not seen your reasoning. A model-based challenge is useful but is not independent human review; say which you used.
- **Wording:** "conclusion", not "audit opinion". Do not claim assurance or certification for a self-assessment.
- **Remediation:** if you fix things, do it on a copy or in a labelled version, retest with the same frozen data, and report costs and side effects as well as improvements.

## Quick triage (30 minutes)

If time is short, answer these first: (1) does it use AI or fixed rules; (2) can it write to the source system; (3) is there a record of each run; (4) does a person accept or reject each flag; (5) has accuracy been tested on data the developer did not write the rules for, including clean items; (6) does the output change if the input order changes; (7) is the description of the system accurate. A "no" or "don't know" on any of these is where to look first.
