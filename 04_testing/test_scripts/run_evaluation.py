"""Evaluation harness: run the Northbridge engine (pinned commit) over the test ledger and compare
with ground-truth labels. Does not modify the system under review or the test database.

Usage (from the subject's venv):
  python run_evaluation.py <subject_dir> <dataset_dir> <results_dir>
  python run_evaluation.py <subject_dir> <dataset_dir> --hash     # print hash of detections only
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import sqlite3
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SUBJECT = Path(sys.argv[1]).resolve()
DATASET = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(SUBJECT))

from src.pipeline import detect_all  # noqa: E402
from src.reconciliation.matcher import build_reconciliation_report, match_bank_transactions  # noqa: E402

DB = DATASET / "ledger_test.db"


def run_engine() -> tuple[list[dict], float]:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)  # read-only
    t0 = time.perf_counter()
    recon = build_reconciliation_report(match_bank_transactions(conn))
    detected = detect_all(conn, recon)
    elapsed = time.perf_counter() - t0
    conn.close()
    return detected, elapsed


def item_of(d: dict) -> str:
    rid = d.get("record_id")
    return rid[:-3] if rid and rid.endswith("-L1") else rid


def detections_hash(detected: list[dict]) -> str:
    canon = sorted(json.dumps(d, sort_keys=True, default=str) for d in detected)
    return hashlib.sha256("\n".join(canon).encode()).hexdigest()


if "--hash" in sys.argv:
    det, _ = run_engine()
    print(detections_hash(det), len(det))
    sys.exit(0)

RES = Path(sys.argv[3]).resolve()
RES.mkdir(parents=True, exist_ok=True)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def write_csv(path, rows, fields):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


# ---------- run and load ----------
labels = list(csv.DictReader(open(DATASET / "labels.csv")))
by_id = {L["item_id"]: L for L in labels}
detected, elapsed = run_engine()
flags = defaultdict(list)  # item -> [rule ids]
unknown = []
for d in detected:
    it = item_of(d)
    if it in by_id:
        flags[it].append(d["target_anomaly_id"])
    else:
        unknown.append(d)

# ---------- item-level results ----------
items = []
for L in labels:
    fr = sorted(set(flags.get(L["item_id"], [])))
    err = L["is_error"] == "1"
    items.append({
        "item_id": L["item_id"], "unit_type": L["unit_type"], "group": L["group"], "is_error": L["is_error"],
        "error_type": L["error_type"], "expected_rule": L["expected_rule"], "flagged_by": ";".join(fr),
        "flagged": int(bool(fr)), "detected_by_expected_rule": int(err and L["expected_rule"] in fr),
        "note": L["construction"]})
write_csv(RES / "item_results.csv", items, list(items[0].keys()))
write_csv(RES / "detections.csv",
          [{"rule": d["target_anomaly_id"], "item_id": item_of(d), "record_id": d.get("record_id"),
            "contact": d.get("contact_name"), "amount": d.get("amount"), "reason": d.get("reason")} for d in detected],
          ["rule", "item_id", "record_id", "contact", "amount", "reason"])

errs = [i for i in items if i["is_error"] == "1"]
clean = [i for i in items if i["is_error"] == "0"]
tp = sum(i["flagged"] for i in errs)
fn = len(errs) - tp
fp = sum(i["flagged"] for i in clean)
tn = len(clean) - fp
prec = tp / (tp + fp) if tp + fp else float("nan")
rec = tp / len(errs)
f1 = 2 * prec * rec / (prec + rec) if prec + rec else float("nan")
fpr = fp / len(clean)
clean_std = [i for i in clean if i["group"] == "clean"]
clean_hard = [i for i in clean if i["group"] == "clean_hard"]
fp_std = sum(i["flagged"] for i in clean_std)
fp_hard = sum(i["flagged"] for i in clean_hard)

overall = [
    {"metric": "Items (units) tested", "value": len(items), "ci95_low": "", "ci95_high": ""},
    {"metric": "Real errors", "value": len(errs), "ci95_low": "", "ci95_high": ""},
    {"metric": "Clean items (standard + hard)", "value": len(clean), "ci95_low": "", "ci95_high": ""},
    {"metric": "True positives", "value": tp, "ci95_low": "", "ci95_high": ""},
    {"metric": "False negatives", "value": fn, "ci95_low": "", "ci95_high": ""},
    {"metric": "False positives", "value": fp, "ci95_low": "", "ci95_high": ""},
    {"metric": "True negatives", "value": tn, "ci95_low": "", "ci95_high": ""},
    {"metric": "Recall (item level, any rule)", "value": pct(rec), "ci95_low": pct(wilson(tp, len(errs))[0]), "ci95_high": pct(wilson(tp, len(errs))[1])},
    {"metric": "Precision (item level)", "value": pct(prec), "ci95_low": pct(wilson(tp, tp + fp)[0]), "ci95_high": pct(wilson(tp, tp + fp)[1])},
    {"metric": "F1", "value": pct(f1), "ci95_low": "", "ci95_high": ""},
    {"metric": "False positive rate (all clean)", "value": pct(fpr), "ci95_low": pct(wilson(fp, len(clean))[0]), "ci95_high": pct(wilson(fp, len(clean))[1])},
    {"metric": "False positive rate (standard clean)", "value": pct(fp_std / len(clean_std)), "ci95_low": pct(wilson(fp_std, len(clean_std))[0]), "ci95_high": pct(wilson(fp_std, len(clean_std))[1])},
    {"metric": "False positive rate (hard clean)", "value": pct(fp_hard / len(clean_hard)), "ci95_low": pct(wilson(fp_hard, len(clean_hard))[0]), "ci95_high": pct(wilson(fp_hard, len(clean_hard))[1])},
    {"metric": "Flags on unknown records (harness check)", "value": len(unknown), "ci95_low": "", "ci95_high": ""},
    {"metric": "Engine run time (s)", "value": f"{elapsed:.3f}", "ci95_low": "", "ci95_high": ""},
]
write_csv(RES / "metrics_overall.csv", overall, ["metric", "value", "ci95_low", "ci95_high"])

# ---------- by error type ----------
by_type = []
for et in sorted({i["error_type"] for i in errs}):
    grp = [i for i in errs if i["error_type"] == et]
    k_any = sum(i["flagged"] for i in grp)
    k_rule = sum(i["detected_by_expected_rule"] for i in grp)
    lo, hi = wilson(k_any, len(grp))
    by_type.append({"error_type": et, "expected_rule": grp[0]["expected_rule"], "n_errors": len(grp),
                    "detected_any_rule": k_any, "recall_any_rule": pct(k_any / len(grp)),
                    "ci95_low": pct(lo), "ci95_high": pct(hi),
                    "detected_by_expected_rule": k_rule, "recall_expected_rule": pct(k_rule / len(grp)),
                    "missed_items": ";".join(i["item_id"] for i in grp if not i["flagged"])})
write_csv(RES / "metrics_by_error_type.csv", by_type, list(by_type[0].keys()))

# ---------- by rule (flags) ----------
type_of_rule = {}
for t in by_type:
    type_of_rule[t["expected_rule"]] = t["error_type"]
by_rule = []
for r in ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]:
    flagged_items = sorted({item_of(d) for d in detected if d["target_anomaly_id"] == r and item_of(d) in by_id})
    correct = [x for x in flagged_items if by_id[x]["is_error"] == "1" and by_id[x]["expected_rule"] == r]
    other_err = [x for x in flagged_items if by_id[x]["is_error"] == "1" and by_id[x]["expected_rule"] != r]
    wrong = [x for x in flagged_items if by_id[x]["is_error"] == "0"]
    by_rule.append({"rule": r, "items_flagged": len(flagged_items), "correct_for_this_rule": len(correct),
                    "flagged_error_of_other_type": len(other_err), "false_positives_on_clean": len(wrong),
                    "precision_strict": pct(len(correct) / len(flagged_items)) if flagged_items else "n/a",
                    "false_positive_items": ";".join(wrong)})
write_csv(RES / "metrics_by_rule.csv", by_rule, list(by_rule[0].keys()))

# ---------- criteria (from Terms of Reference s6) ----------
def grp_recall(types):
    g = [i for i in errs if i["error_type"] in types]
    k = sum(i["flagged"] for i in g)
    return k, len(g)

kd, nd = grp_recall({"DUP_AR", "DUP_AP", "DUP_PAY", "BREAK"})
ko, no = grp_recall({"VAT_MISCODE", "THRESHOLD", "WEEKEND", "OUTLIER"})
crit = [
    ("Recall, duplicates and reconciliation breaks", ">= 0.95", kd / nd, kd / nd >= 0.95, f"{kd}/{nd}"),
    ("Recall, other rules (A2, A3, A4, A7)", ">= 0.85", ko / no, ko / no >= 0.85, f"{ko}/{no}"),
    ("Precision", ">= 0.80", prec, prec >= 0.80, f"{tp}/{tp + fp}"),
    ("F1", ">= 0.85", f1, f1 >= 0.85, ""),
    ("False positive rate", "<= 0.10", fpr, fpr <= 0.10, f"{fp}/{len(clean)}"),
]
write_csv(RES / "criteria_assessment.csv",
          [{"criterion": c[0], "threshold": c[1], "result": pct(c[2]), "met": "YES" if c[3] else "NO", "counts": c[4]} for c in crit],
          ["criterion", "threshold", "result", "met", "counts"])

# ---------- determinism: 5 fresh processes ----------
hashes = []
for _ in range(5):
    out = subprocess.run([sys.executable, __file__, str(SUBJECT), str(DATASET), "--hash"], capture_output=True, text=True, check=True).stdout.split()
    hashes.append(out[0])
det = {"runs": 5, "distinct_hashes": len(set(hashes)), "hash": hashes[0], "identical": len(set(hashes)) == 1,
       "in_process_hash": detections_hash(detected)}
det["in_process_matches"] = det["in_process_hash"] == hashes[0]

# ---------- metadata ----------
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def pkg(n):
    try:
        import importlib.metadata as m
        return m.version(n)
    except Exception:
        return "not installed"

meta = {
    "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "subject_commit": subprocess.run(["git", "-C", str(SUBJECT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
    "python": platform.python_version(), "platform": platform.platform(),
    "packages": {p: pkg(p) for p in ["pandas", "scikit-learn", "streamlit", "requests"]},
    "ledger_test_db_sha256": sha(DB), "labels_csv_sha256": sha(DATASET / "labels.csv"),
    "determinism": det, "flags_total": len(detected), "flags_on_unknown_records": len(unknown),
}
(RES / "run_metadata.json").write_text(json.dumps(meta, indent=2))

# ---------- chart (dependency-free SVG): recall by error type vs threshold ----------
W, H, L, T, B = 760, 40 + 34 * len(by_type) + 50, 150, 40, 40
bars = []
for i, t in enumerate(by_type):
    y = T + i * 34
    v = float(t["recall_any_rule"])
    thr = 0.95 if t["error_type"] in ("DUP_AR", "DUP_AP", "DUP_PAY", "BREAK") else 0.85
    col = "#2e7d32" if v >= thr else "#c62828"
    bars.append(f'<text x="{L-8}" y="{y+16}" text-anchor="end" font-size="12" font-family="Arial">{t["error_type"]} (n={t["n_errors"]})</text>'
                f'<rect x="{L}" y="{y}" width="{v*(W-L-60):.1f}" height="22" fill="{col}"/>'
                f'<text x="{L+v*(W-L-60)+6:.1f}" y="{y+16}" font-size="12" font-family="Arial">{v:.0%}</text>'
                f'<line x1="{L+thr*(W-L-60):.1f}" x2="{L+thr*(W-L-60):.1f}" y1="{y-3}" y2="{y+25}" stroke="#000" stroke-dasharray="3,2"/>')
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
       f'<rect width="100%" height="100%" fill="#fff"/><text x="{L}" y="22" font-size="14" font-weight="bold" font-family="Arial">'
       f'Recall by error type, any rule (dashed line = criterion; red = below it)</text>' + "".join(bars) +
       f'<text x="{L}" y="{H-10}" font-size="10" font-family="Arial">Synthetic data, small n per type: indicative only. Pinned commit {meta["subject_commit"][:7]}.</text></svg>')
(RES / "recall_by_error_type.svg").write_text(svg)

# ---------- console summary ----------
print(f"items={len(items)} errors={len(errs)} clean={len(clean)} flags={len(detected)} unknown={len(unknown)}")
print(f"TP={tp} FN={fn} FP={fp} TN={tn} recall={rec:.3f} precision={prec:.3f} f1={f1:.3f} fpr={fpr:.3f} (std {fp_std}/{len(clean_std)}, hard {fp_hard}/{len(clean_hard)})")
for t in by_type:
    print(t["error_type"], t["expected_rule"], f'{t["detected_any_rule"]}/{t["n_errors"]} any-rule, {t["detected_by_expected_rule"]} expected-rule; missed: {t["missed_items"]}')
for r in by_rule:
    print(r["rule"], r["items_flagged"], "flagged;", r["correct_for_this_rule"], "correct;", r["false_positives_on_clean"], "FP:", r["false_positive_items"])
for c in crit:
    print(("MET " if c[3] else "NOT MET ") + c[0], pct(c[2]), c[4])
print("determinism", det)
print(f"engine time {elapsed:.3f}s")
