"""Retest helper: published-figure regression and variance-direction check against a given subject copy.
Usage: python retest_published_and_variance.py <subject_dir> <dataset_dir> <original_tree_with_answer_key>"""
import sys, sqlite3, re
from pathlib import Path
S, DS, ORIG = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
sys.path.insert(0, str(S))
from src.anomaly.statistical import score_against_answer_key, score_against_planted_records
from src.pipeline import detect_all
from src.reconciliation.matcher import build_reconciliation_report, match_bank_transactions
from src.variance.explainer import compute_account_movement, explain_movement
def run(db):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    return detect_all(c, build_reconciliation_report(match_bank_transactions(c)))
keys = ("caught", "total_planted_anomalies", "false_positive_count", "precision", "recall")
r = score_against_planted_records(run(S / "data/demo_ledger_large.db"), str(S / "data/synthetic_planted.csv"))
print("synthetic:", {k: r[k] for k in keys}, "(published: 84/84, 24 FP, 0.778)")
r = score_against_answer_key(run(S / "data/demo_ledger.db"), str(ORIG / "data/anomaly_answer_key.csv"))
print("xero:", {k: r[k] for k in keys}, "(published: 7/7, 3 FP, 0.70)")
print("quickbooks demo flags:", len(run(S / "data/demo_ledger_quickbooks.db")))
def direction(db, months):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True); tot = contra = 0
    for pa, pb in zip(months, months[1:]):
        for mv in compute_account_movement(c, pa, pb):
            if not mv["account_code"]: continue
            s = explain_movement(c, mv["account_code"], pa, pb)
            h = re.search(r" (up|down) \d+%", s)
            if not h or not re.search(r"driven by|largest contributors", s): continue
            tot += 1
            tail = re.split(r"driven by|largest contributors in that direction:", s)[1]
            d = re.findall(r"\(([+-])£", tail)
            contra += any((x == "+") != (h.group(1) == "up") for x in d)
    return tot, contra
print("variance sentences with a driver against the headline (sentences, contradicting):")
print(" test dataset:", direction(DS / "ledger_test.db", [f"2026-{m:02d}" for m in range(1, 9)]))
for name in ("demo_ledger.db", "demo_ledger_quickbooks.db", "demo_ledger_large.db"):
    c = sqlite3.connect(f"file:{S/'data'/name}?mode=ro", uri=True)
    months = sorted({r[0] for r in c.execute("select substr(invoice_date,1,7) from invoices")})
    print(" ", name, direction(S / "data" / name, months))
