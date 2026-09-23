"""Post-challenge-review analysis (does not change the frozen harness or dataset).
1. Label sensitivity: recompute metrics under alternative reasonable labellings / exclusions.
2. Full criteria assessment: all 8 criteria in the Terms of Reference, plus per-flag precision.
Usage: python sensitivity_and_full_criteria.py <results_dir>"""
import csv, sys
from pathlib import Path
R = Path(sys.argv[1])
items = list(csv.DictReader(open(R / "item_results.csv")))
dets = list(csv.DictReader(open(R / "detections.csv")))
def m(rows, relabel_clean=(), drop=()):
    tp = fp = fn = tn = 0
    for i in rows:
        if i["item_id"] in drop: continue
        err = i["is_error"] == "1" and i["item_id"] not in relabel_clean
        fl = i["flagged"] == "1"
        tp += err and fl; fn += err and not fl; fp += (not err) and fl; tn += (not err) and not fl
    p = tp / (tp + fp) if tp + fp else float("nan"); r = tp / (tp + fn)
    return dict(TP=tp, FN=fn, FP=fp, TN=tn, recall=round(r, 3), precision=round(p, 3), F1=round(2 * p * r / (p + r), 3), FPR=round(fp / (fp + tn), 3))
ids = lambda pred: {i["item_id"] for i in items if pred(i)}
fees = ids(lambda i: "Monthly bank charge" in i["note"])
wk_legit = ids(lambda i: "trades at weekends" in i["note"])
cobalt = ids(lambda i: "fixed-price licence" in i["note"] or i["note"].startswith("Boundary"))
review_flag_types = ids(lambda i: i["error_type"] in ("WEEKEND", "THRESHOLD"))
dup_ap = ids(lambda i: i["error_type"] == "DUP_AP")
scen = [
    ("S0 Base (as frozen)", m(items)),
    ("S1 Weekend and threshold errors relabelled as review indicators (clean)", m(items, relabel_clean=review_flag_types)),
    ("S2 Drop 6 bank charges", m(items, drop=fees)),
    ("S3 Drop bank charges, legit weekend, fixed-price/boundary bills (15 hard cases)", m(items, drop=fees | wk_legit | cobalt)),
    ("S4 Drop duplicate supplier bills (A1 scope)", m(items, drop=dup_ap)),
]
with open(R / "sensitivity.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["scenario", *scen[0][1].keys()])
    for n, d in scen: w.writerow([n, *d.values()])
for n, d in scen: print(n, d)
lab = {i["item_id"]: i for i in items}
per_flag = sum(1 for d in dets if lab[d["item_id"]]["is_error"] == "1") / len(dets)
print("per-flag precision", round(per_flag, 3), sum(1 for d in dets if lab[d["item_id"]]["is_error"] == "1"), "/", len(dets))
# root-cause clusters of false positives
clusters = {"bank charges": fees, "weekend supplier": wk_legit, "fixed-price/boundary": cobalt,
            "VAT registration change": ids(lambda i: i["item_id"] in ("AP-109", "AP-110", "AP-111")),
            "large equipment": ids(lambda i: i["item_id"] in ("AP-119", "AP-120")),
            "recurring receipt attribution": {"BT-023", "BT-035"}}
fps = {i["item_id"] for i in items if i["is_error"] == "0" and i["flagged"] == "1"}
print("FP clusters:", {k: len(v & fps) for k, v in clusters.items()}, "unassigned:", sorted(fps - set().union(*clusters.values())))
full = [
 ("Recall, duplicates and reconciliation breaks", ">= 95%", "83.3% (15/18)", "NOT MET", "Fails only because A1 checks sales invoices, not supplier bills (0/3). Robust to relabelling."),
 ("Recall, other rules (A2, A3, A4, A7)", ">= 85%", "100% (13/13)", "MET on point estimate", "Near-guaranteed by construction; Wilson lower bound about 0.77 spans the threshold; weekend/threshold labels are judgement (CH-02, 03, 05)."),
 ("Precision (per item, as scored)", ">= 80%", "56.0% (28/50)", "NOT MET", f"Per flag: {per_flag:.1%} (29/54). Depends on the constructed mix; reaches 80% only if 15 hard cases are dropped."),
 ("F1", ">= 0.85", "0.691", "NOT MET", "0.848 in the most favourable exclusion (S3), still below 0.85."),
 ("False positive rate", "<= 10%", "11.1% (22/199)", "NOT MET (borderline, label-sensitive)", "Flips to met if the 6 bank charges are excluded (8.3%). 1.2% on standard clean, 62.5% on hard clean."),
 ("Determinism (identical output on rerun)", "100%", "Fixed row order: 5/5 identical. Reordered rows: differs in 6 of 7 orderings", "NOT MET", "Output depends on database row order (matcher takes the first match, no one-to-one allocation). See order_sensitivity.txt."),
 ("Audit trail completeness", "100%", "0% (no run log exists)", "NOT MET", "C26 not in place."),
 ("Human disposition of flags", "100%", "0% (no disposition step)", "NOT MET", "C21 not in place."),
]
with open(R / "criteria_assessment_full.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["criterion", "threshold", "result", "assessment", "note"]); w.writerows(full)
print("criteria not met:", sum(1 for c in full if c[3].startswith("NOT MET")), "of", len(full))
