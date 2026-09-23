"""Challenge review CH-01: does engine output depend on database row order?
Usage: python order_sensitivity.py <subject> <dataset> <scratch_dir>   (copies the test DB; original untouched)"""
import sqlite3, shutil, random, sys, csv
from pathlib import Path
subject, dataset, scratch = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, subject)
from src.pipeline import detect_all
from src.reconciliation.matcher import build_reconciliation_report, match_bank_transactions
src = dataset / "ledger_test.db"
labels = {r["item_id"]: r for r in csv.DictReader(open(dataset / "labels.csv"))}
def item(d):
    r = d.get("record_id"); return r[:-3] if r and r.endswith("-L1") else r
def run(db):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    det = detect_all(c, build_reconciliation_report(match_bank_transactions(c)))
    items = {item(d) for d in det}
    tp = [i for i in items if labels[i]["is_error"] == "1"]
    fpbank = sorted(i for i in items if i.startswith("BT") and labels[i]["is_error"] == "0")
    missed = sorted(i for i, l in labels.items() if l["is_error"] == "1" and i not in items)
    return {"flags": len(det), "true_positive_items": len(tp), "false_positive_items": len(items) - len(tp), "bank_false_positives": fpbank, "missed_errors": missed}
print("original order:", run(src))
for seed in range(6):
    dst = scratch / f"s{seed}.db"; shutil.copy(src, dst)
    c = sqlite3.connect(dst)
    for t in ("invoices", "bank_transactions", "payments"):
        rows = c.execute(f"select * from {t}").fetchall(); n = len(rows[0])
        if seed == 0: rows.reverse()
        else: random.Random(seed).shuffle(rows)
        c.execute(f"delete from {t}"); c.executemany(f"insert into {t} values ({','.join('?' * n)})", rows)
    c.commit(); c.close()
    print("reversed" if seed == 0 else f"shuffle seed {seed}", run(dst))
