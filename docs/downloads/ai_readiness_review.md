# AI Readiness Review Template

A template for assessing a business process for AI or automation adoption: what the process costs today, where AI or automation could help, what it would return, and what risks and controls each option needs. Use it **before** buying or building. Use `ai_audit_checklist.md` afterwards to assess a system once it exists.

**Limits.** This is a structured template, not a validated method. It contains no benchmark data. Any number you enter must come from your own measurement or be labelled as an assumption with its source. Scores are judgements, so record who scored and why.

**How to use:** complete sections 1 to 8 in order. Keep a separate line in each table for evidence or assumption. Where the process is a finance control, note the control objective it serves.

---

## 1. Scope and sponsor

| Item | Entry |
|---|---|
| Process under review | |
| Process owner and sponsor | |
| Control objective or business outcome the process serves | |
| Systems, data and people involved | |
| In scope / out of scope | |
| Reviewer and date | |
| Independent of the process owner? (Y/N; if N, say so throughout) | |

## 2. Process map

Map the process as it is actually performed, not as documented. Interview the people who do it and watch it once if you can.

| Step | Who | System / tool | Input | Output | Manual / automated | Decision or judgement involved? | Where errors arise |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |

Also record: hand-offs and waiting time, rework loops, exceptions and how they are handled, and existing controls (preventive and detective).

## 3. Baseline: time, cost, volume, quality

Measure a representative period (state it). If you estimate, mark the row "estimate" and give the basis.

| Measure | Value | Period | Source (measured / estimate) | Notes |
|---|---|---|---|---|
| Volume (items per period) | | | | |
| Effort per item (minutes) | | | | |
| Total effort per period (hours) | | | | |
| Loaded cost per hour | | | | |
| Cost per period | | | | |
| Cycle time (elapsed) | | | | |
| Error / exception rate | | | | |
| Cost of an error (rework, loss, penalty) | | | | |
| Errors found late (after close, by auditors, by customers) | | | | |
| Peak-period pressure (backlog, overtime) | | | | |

## 4. Opportunity list and ranking

List every candidate, including "improve the process without AI" and "do nothing". Many opportunities are better served by simple rules, a checklist, a report or a process fix.

| ID | Opportunity | Step(s) affected | Type (rules / analytics / ML / LLM / process change) | Why this type |
|---|---|---|---|---|
| O1 | | | | |
| O2 | | | | |

### Scoring (1 to 5; record the reason for each score)

- **Value:** size of the time, cost, error or control benefit.
- **Feasibility:** data available and usable, integration effort, skills, time to deploy.
- **Risk (5 = highest):** consequence of error, need for explanation, personal data, regulatory exposure, dependence on a provider.
- **Explainability need:** can the output be explained to a reviewer or auditor in the terms they need?

| ID | Value | Feasibility | Risk | Explainability need | Priority score | Rank | Reason for scores |
|---|---|---|---|---|---|---|---|
| O1 | | | | | | | |
| O2 | | | | | | | |

Suggested priority score (state it if you change it): **Value × Feasibility ÷ Risk**. Apply judgement to the ranking: a high-value, high-risk opportunity may need a pilot with human review first.

## 5. Data readiness (per shortlisted opportunity)

| Question | O1 | O2 |
|---|---|---|
| Is the data needed available, complete and accessible? | | |
| Is there labelled history (known good and known bad) to test against? | | |
| Data quality issues found (missing, duplicated, inconsistent)? | | |
| Does it include personal or confidential data? Lawful basis and retention? | | |
| Will the data leave your environment (cloud provider, API)? | | |
| Can the data be used for a **test set that was not built to fit the solution**? | | |

## 6. ROI estimate

Use one row per input, keep assumptions visible, and calculate from those cells.

| Input | Value | Type (measured / assumption) | Source or basis |
|---|---|---|---|
| Baseline cost per period (from section 3) | | | |
| Share of effort the solution could remove | | assumption | |
| Residual human review effort (do not assume zero) | | assumption | |
| Solution run cost per period (licences, usage, hosting) | | | |
| One-off build or implementation cost | | | |
| Ongoing support and monitoring cost | | | |
| Cost of new false-alarm handling | | assumption | |
| Errors avoided per period × cost per error | | assumption | |

Formulas (keep them in a spreadsheet, not hard-coded):

- Net benefit per period = (baseline cost × share removed) − residual review cost − run cost − support cost − false-alarm cost + (errors avoided × cost per error)
- Payback period = one-off cost ÷ net benefit per period
- Show the result at a **low, expected and high** case, and state which assumptions move it most.

Do not present ROI as a finding. It is an estimate resting on the assumptions above.

## 7. Risks and controls per recommendation

For each shortlisted opportunity, list what could go wrong and what would control it. Use the same risk-and-control structure as an assurance review so the design can be assessed later.

| Opportunity | Risk (what could go wrong) | Likelihood (1-5) | Impact (1-5) | Control needed | Owner | Test before go-live |
|---|---|---|---|---|---|---|
| O1 | Misses real errors | | | Test on an independent set including hard cases; recall threshold agreed in advance | | |
| O1 | Flags too much legitimate activity | | | False-positive threshold and suppression process | | |
| O1 | Output changes with input order or environment | | | Determinism and order tests; pinned versions | | |
| O1 | No record of what ran | | | Run log with input hash, version, user | | |
| O1 | Flags accepted without review | | | Recorded human disposition | | |
| O1 | Over-broad permissions or exposed credentials | | | Least privilege; secrets manager | | |
| O1 | Misdescribed capability (for example "AI" for fixed rules) | | | Accurate description and limitations statement | | |
| O1 (LLM only) | Unsupported explanations; prompt injection; provider data use | | | Faithfulness checks; adversarial tests; provider terms | | |

Add a row per opportunity and remove rows that do not apply, saying why.

## 8. Recommendation and decision

| Item | Entry |
|---|---|
| Recommended option(s) and sequence | |
| What would make you stop or not proceed | |
| Pilot design: scope, duration, success criteria set **before** the pilot, comparison with current process | |
| Human review arrangement during the pilot | |
| Independent test set and who builds it | |
| Owner for controls after go-live | |
| Reassessment triggers (change of model, data, scope, regulation) | |
| Decision, decision maker, date | |

## Guidance notes

- **Start with the process, not the technology.** A poorly understood process automates its problems.
- **Ask whether it needs AI at all.** Compare against fixed rules, reports and process changes first. A rules-based tool described as "AI" hides how it behaves and what it cannot do.
- **Measure the baseline honestly.** Without it, any improvement claim is unsupported.
- **Budget for review and false alarms.** Detection tools create work as well as saving it.
- **Plan the test before the build.** Agree accuracy thresholds and an independent test set in advance; a test written after the solution tends to confirm it.
- **Keep the design assessable.** Decide up front what would be logged, who reviews outputs and how a wrong output is corrected. It is much cheaper than adding them later.
- **Check the regulatory position** for the specific use (for example EU AI Act classification, data protection) with primary sources at the time of decision.
