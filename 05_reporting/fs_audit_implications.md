# Financial Statement Audit Implications

**Question:** if an entity used Northbridge in its month-end close, how would an external auditor treat it? Based on the results of this review at commit `9c4127a`. Northbridge is a portfolio tool; this is an illustration of the approach, not a statement that any entity relies on it. ISA references are UK (Revised 2019 for ISA 315) and should be checked against current text before publication.

## 1. Conclusion in one paragraph
On this evidence an auditor would **take no controls reliance** on Northbridge, and would treat its output as an analytical aid whose completeness and accuracy would themselves need testing. The IT general controls a reliance strategy needs (change management, logging, access) are absent or weak; the automated control missed a whole error class (duplicate supplier bills) and its output can vary with record order; and there is no evidenced human review control.

## 2. Starting point (ISA 315)
Management remains responsible for the financial statements and for controls over the tool. The tool is part of the information system and is assessed as an IT application. Relevant accounts and assertions: cash and payables (existence, completeness, accuracy, classification); receivables for duplicate sales invoices.

## 3. The four layers applied

| Layer | Auditor's question | Result of this review | Effect |
|---|---|---|---|
| **1. IT general controls** (ISA 315) | Are access, change management, logging and operations effective? | No run log (F-03), no regression tests, tags or pinned dependencies (F-06), plaintext tokens and excess QuickBooks scope (F-09) | ITGCs not effective. This alone prevents reliance on automated outputs |
| **2. The tool as an automated control** (ISA 330) | Does it perform to the required precision? A test of one is not enough for a tool whose output can vary | Recall on duplicates and breaks 83.3% against 95% (F-01); output changes with record order (F-02); precision 0.56 and false positive rate 11.1% on a constructed mix (F-08) | Does not meet the precision needed to address completeness and accuracy of payables |
| **3. Human review control** | Is there evidence each flag was dispositioned by a competent reviewer? | No disposition step, owner or intended use (F-04) | No management review control to test |
| **4. Substantive procedures** (ISA 330, ISA 500) | Can the exceptions list be used as audit evidence? | Completeness and accuracy of the list not established: order-dependent (F-02), missing supplier duplicates (F-01), completeness of the data pull unevidenced (F-11) | Auditor would re-perform on source data rather than use the tool's list |

## 4. Effect on the audit approach
- **No controls reliance.** Substantive testing is not reduced.
- **Worked example (from this review):** recall on duplicate payables is 0 of 3 supplier-bill duplicates and 15 of 18 across the duplicate and break group, against a 95% criterion. The detective control does not operate at the required precision for payables completeness and accuracy. The auditor would run a duplicate-payment and duplicate-bill analysis over the full accounts payable population directly from source data, and would not use the tool's exception list as evidence.
- **Use as a supplementary analytic:** the auditor could run the tool as an additional lead generator, but would not treat a clean run as evidence of no errors, and would record the version and input used (which the tool does not do itself).

## 5. Deficiencies and communication (ISA 265)
The findings are evaluated as control deficiencies in the entity's IT and review controls. Candidates for written communication to those charged with governance as significant deficiencies, if the entity relied on the tool for the close: F-03 (no audit trail), F-04 (no evidenced review), F-01 (undetected duplicate payables). Whether a deficiency is significant depends on the entity's circumstances and the auditor's judgement.

## 6. Documentation on file (illustrative)
- Description of the system, its owner and where it sits in the process (`01_planning/system_description.md`)
- Risk assessment linking risks to accounts and assertions (`02_risk/risk_register.xlsx`)
- ITGC and control test results (`03_controls/control_matrix.xlsx`, `04_testing/evidence_log.md`)
- Performance evidence and criteria (`04_testing/results/`, `terms_of_reference.md` s6)
- The reliance decision and its effect on substantive procedures (this document)
- Deficiencies and communication (`05_reporting/findings.md`)

## 7. Limits
The performance evidence comes from a constructed test mix and is indicative only. The determination that an entity could not rely on the tool is a consequence of missing controls as much as of measured error rates: even with better recall, absent logging and change control would prevent reliance. Excludes the auditor's own use of AI tools.
