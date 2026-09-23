# Challenge review (raw), Northbridge testing

## Summary
**Verdict: sound enough for findings about mechanics and specific defects, not for population accuracy claims. Reword and add caveats before reporting.**

Task A: I re-derived everything from labels.csv plus detections.csv (script in /tmp/ch/a.py). TP 28, FN 3, FP 22, TN 177, recall 0.903, precision 0.560, F1 0.691, FPR 0.111. Per-type, per-rule and Wilson figures (0.751-0.967, 0.423-0.688, 0.074-0.162) all match results/*.csv. The record_id to item_id mapping is right: 54 flags, 0 unmapped, no mismatch with the item_id column.

Robust: DUP_AP 0/3 (A1 is ACCREC only), so the duplicates/breaks recall criterion is not met. Precision and F1 are not met under most reasonable relabelling. Fragile: the FPR result. The determinism "met" result is overstated (CH-01). Several control results are overstated (CH-07 to CH-09).

Must change: (1) qualify determinism; (2) present the precision and FPR outcomes as properties of a designed mix; (3) report all 8 ToR criteria; (4) correct the C22, C19, C06, C07 and C23 wording; (5) add the coverage caveats.

## Challenges

**CH-01 High. Determinism claim (E-03, C14).** Output depends on database row order. I copied ledger_test.db to /tmp, rebuilt `invoices` and `bank_transactions` in reverse-id order, and re-ran the pinned engine. Flags went from 54 to 53. True DUP_PAY BT-044 was lost. BT-023 and BT-035 were replaced by new false positives BT-026 and BT-031, both clean receipts. Cause: matcher.py `break` on the first exact match, with no ORDER BY and no one-to-one matching. The 5 identical runs used one fixed row order. Resolution: state "deterministic for identical input ordering only". Add a shuffled-order test and record a finding on matcher order dependence. The DUP_PAY 4/4 result is not stable.

**CH-02 High. Test-set validity and bias.** ToR s3/s4 says the set was "not written to fit the rules". build_dataset.py shows otherwise:
- Errors sit inside each rule's envelope: duplicates 1-6 days against A1's 10-day window; 488/492/497 against A3's 475-500 band; Saturday/Sunday dates; outliers about 9x with modified z of 21-46 against the 3.5 cutoff; consistent INPUT2 history before the VAT error.
- Hard cases were chosen by reading the rules: 474.99 and 500.00 boundary values, a Cobalt fixed licence at 489, Fenwick VAT registration, Kestrel and Marlow weekend billing.
- Recall of 13/13 on "other" rules is therefore near-guaranteed. Precision and FPR mainly reflect the reviewer's mix: 32 of 199 clean items are adversarial, FPR is 62.5% on hard clean and 1.2% on standard clean (2/167).
- There is no near-miss outlier (3-5x), no near-duplicate (>10 days or differing amounts), and no fuzzy supplier names.
Resolution: report stratified results only. Say the "not met" outcomes on precision and FPR apply to this constructed mix and are not estimates for real books.

**CH-03 High. Label inconsistency, favourable to the system.** The stated principle is "is the record really wrong". WEEKEND, THRESHOLD and OUTLIER are review indicators, not accounting errors. Their labels rest on unobservable narrative: "supplier does not trade at weekends". E-01 note 5 concedes the data cannot show trading days. Stationery Direct, City Cabs and Pearce (error) are indistinguishable in the data from Kestrel and Marlow (clean). AdSpark 497 (error) and Cobalt 489 (clean) are likewise indistinguishable. A different reasonable labelling (treat weekend and threshold as review flags, not errors) changes the result to: recall 0.880 (22/25); precision 0.44; FPR 0.137; recall on other rules 1.000 on the remaining 7 items. Outcomes are unchanged, but the "13/13 met" result depends on labelling that no one else could reproduce from the data alone.

**CH-04 Medium. Sensitivity of criteria outcomes (my reruns).** Rows show items dropped from the scored set.

| Scenario | FP | Precision | F1 | FPR | Dup/break recall |
|---|---|---|---|---|---|
| Base | 22 | 0.560 | 0.691 | 0.111 | 0.833 |
| Drop 6 bank charges | 16 | 0.636 | 0.747 | 0.083 | 0.833 |
| Also drop 4 weekend + 7 Cobalt/boundary | 7 | 0.800 | 0.848 | 0.038 | 0.833 |
| Drop DUP_AP | 22 | 0.560 | 0.718 | 0.111 | 1.000 |

- FPR flips to MET with the bank charges removed, or with any 3 of the 22 FPs removed.
- Precision needs three groups of hard cases removed together to reach 0.80, and F1 is still under 0.85.
- Duplicates/breaks recall passes only if A1's ACCREC-only scope is excluded.
- Bank charges: the README counts these as false positives against precision, so the labelling is consistent with the owner's own convention. It is still a judgement, and FPR sits on a knife-edge.
Resolution: report FPR as "borderline, label-sensitive".

**CH-05 Medium. Statistical treatment.** Wilson intervals assume independent items. The 22 FPs come from about 8 root causes (bank charges x6, Fenwick x3, Cobalt x3, Kestrel x2, Marlow x2, equipment x2, boundary x2, recurring receipts x2). The intervals are therefore too narrow. 13/13 has a lower bound of about 0.77, below the 85% criterion, so "met" cannot be shown above threshold. Resolution: say "met on point estimate; CI spans the threshold".

**CH-06 Medium. Criteria coverage and definition.**
- criteria_assessment.csv scores 5 of the 8 ToR criteria. Determinism (met), audit trail and human disposition are omitted. Matrix C17 says "4 of 5 not met". On the ToR's own list, 6 of 8 are not met (audit trail 0% per C26, disposition 0% per C21).
- Precision is computed per item (28/50). ToR says "correct flags / all flags": 29/54 = 0.537 per flag.
- The A7 flag on weekend bill AP-098 is credited as correct.
Resolution: add all 8 criteria and state the per-flag figure.

**CH-07 Medium. C22 "54/54 reasons naming the contact" is unsupported.** control_tests.py excludes A6 from the name test (`and d["target_anomaly_id"] != "A6"`), so 12 flags were never checked. The check is `str(contact_name) in reason`, which passes for None. BT-050's reason reads "Bank line for None". The test also checks presence, not correctness, although the plan says "meaningful, correct reason". A4 text says "Northbridge doesn't operate on weekends", which is a hard-coded assumption about the client and not about the supplier. Resolution: rate C22 "Partly effective".

**CH-08 Medium. C19 and QuickBooks 0/40.** "12/12 listed" is tautological: the report is built from the same no_match list it is compared against. No independent check of match correctness was done. I verified the 0/40 from the data (read-only): 8 bank-to-invoice contact joins, 0 same-contact same-amount pairs, and 7 lines with no contact. So there are no valid matches to miss, and the cause is sandbox data rather than matcher failure. R08's wording "fails to auto-match valid items" is not supported. E-04's "probable cause" wording is appropriately hedged. Resolution: reword R08 and C19.

**CH-09 Medium. Other control results that outrun the tests.**
- C06: git grep excludes *.md, *.csv and *.db. It is regex-only, with no scanner. "Effective (no credentials in history)" should read "no matches for these patterns in code files".
- C07: it printed only the first 12 alphabetical names per database, so "no personal data" is unsupported. The QuickBooks demo has 55 contacts, including address-like names ("0969 Ocean View Road").
- C23: "13 commits, history intact, commit reproducible" has no supporting output in control_tests_output.txt. I confirmed 13 commits and 0 tags myself.
- C11: it recounts the dashboard against similar queries on the same DB, not against source totals. It shows arithmetic consistency, not pull completeness.
- C01 and C02: the regex covers `requests.*` only. Xero portal grants are unverified (acknowledged).
- C28: it relies on hard-coded line numbers 184-187 plus a keyword. That is weak but the conclusion is supported: the caption does not disclose the fallback.

**CH-10 Medium. Matcher claim.** Mechanism verified: BT-023 (receipt for AR-002) matched AR-001, which already has PAY-036. But "likely on real data" is extrapolation. The dataset itself mixes Payment-linked and bank-line settlement for the same retainer customers (ar_clean[:20] versus [20:34]), which creates the condition. Combined with CH-01, the root cause is broader: no one-to-one allocation and first-match ordering. Resolution: reword as "demonstrated on constructed data".

**CH-11 Medium. Coverage not tested.**
- Ingestion: connectors, Xero and QuickBooks field mapping, dates, currency, tax mapping, pagination (C12). The test DB bypasses all of them.
- Data shape: multi-line bills (the harness `-L1` strip would push "-L2" into "unknown"), VOIDED or DELETED invoices, NULL contact or tax_type inputs, multi-currency.
- Rule logic: A1 across more than 10 days or with differing amounts; A5 on sales-side double receipts or two payments; A2 in the reverse direction; A3 evasion (e.g. £470 or split across suppliers); the effect of A7 small-population and MAD=0 handling; A6 tolerance boundary (£5 or 2%).
- Dashboard behaviour, unauthenticated public app, scale beyond 230 items, and runs on the real Xero snapshot.
- The 5,000-row synthetic set is the only larger test.

**CH-12 Low. Provenance and independence.** Frozen-before-run cannot be independently evidenced. The hashes match the files now, but E-01 records them at 17:33Z, the same minute as run_utc 17:33:23. The self-attestation is acceptable if labelled as such. C16's Xero score used an answer key from the original tree, not the pinned clone.

## Section F. Evidence log overreach
- E-01: "labels follow accounting meaning rather than rule logic" (see CH-03). "Frozen before the first run" is self-attested.
- E-02 note 2: "Most hard-case FPs are by design of the test" is circular; the designer chose those cases.
- E-02 note 3: "Retainer billing is common, so likely on real data" is unsupported (CH-10). The mechanism is verified for two cases only, and the order dependence (CH-01) is missed.
- E-03: "100% ... met" needs the row-order caveat. The 5 runs were on unchanged input.
- E-04: "C22 all 54 flags name the contact" (CH-07); "secrets scan found no credentials" (CH-09); "committed contacts are fictional ... no personal data seen" (CH-09).
- E-04 C19 "12 of 12" (CH-08); C23 has no logged evidence.
- E-05: "17 of 52" counts any opposing driver, including mixed cases (e.g. "Skyline +£235 and Kestrel -£130"), so it is not "wrong direction" in all cases. Also, only contacts present in period_b are ever named, a second defect not reported. The wording is otherwise supported (explainer.py).
