"""Operating-effectiveness tests for controls that can be tested from the pinned code and data.
Read-only against the subject. Prints results; secrets are never printed (counts and file names only).

Usage: python control_tests.py <subject_dir> <test_dataset_dir> <original_tree_for_answer_key>
"""
from __future__ import annotations

import csv
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

S = Path(sys.argv[1]).resolve()
DS = Path(sys.argv[2]).resolve()
ORIG = Path(sys.argv[3]).resolve()
sys.path.insert(0, str(S))


def sh(*a, cwd=S):
    return subprocess.run(a, cwd=cwd, capture_output=True, text=True).stdout


def h(t):
    print(f"\n=== {t} ===")


print("Control tests run", datetime.now(timezone.utc).isoformat(timespec="seconds"), "subject", sh("git", "rev-parse", "HEAD").strip())

# ---- C01 / C02 / C03 / C05: connector scopes and request methods, token storage
h("C01 Xero scopes and HTTP calls")
x = (S / "src/connectors/xero_connector.py").read_text()
m = re.search(r"SCOPE\s*=\s*(.*?)\n\n", x, re.S)
scopes = re.findall(r'"([a-z_.]+)"', m.group(1)) if m else []
print("scopes:", scopes)
print("non-read scopes beyond identity/offline:", [s for s in scopes if not s.endswith(".read") and s not in ("offline_access", "openid", "profile", "email")])
print("requests calls:", sorted(set(re.findall(r"requests\.(get|post|put|delete|patch)\(", x))))
print("post targets:", re.findall(r"requests\.post\(\s*([A-Za-z_\"'./:]+)", x))

h("C02/C03 QuickBooks scope and HTTP calls")
q = (S / "src/connectors/quickbooks_connector.py").read_text()
print("scope line:", [l.strip() for l in q.splitlines() if "SCOPE" in l and "=" in l][:2])
print("requests calls:", sorted(set(re.findall(r"requests\.(get|post|put|delete|patch)\(", q))))
print("post targets:", re.findall(r"requests\.post\(\s*([A-Za-z_\"'./:]+)", q))
print("non-GET data calls (get is query only):", [l.strip() for l in q.splitlines() if "requests.get(" in l])

h("C04 .env handling")
print("git check-ignore .env ->", sh("git", "check-ignore", "-v", ".env").strip() or "NOT IGNORED")
print("commits touching .env (all refs):", len(sh("git", "log", "--all", "--oneline", "--", ".env").split("\n")) - 1)
ex = (S / ".env.example").read_text().splitlines()
kv = [l.split("=", 1) for l in ex if "=" in l and not l.strip().startswith("#")]
print(".env.example keys:", len(kv), "| keys with a non-empty value:", [k for k, v in kv if v.strip()])

h("C05 token storage")
print([l.strip() for f in ("xero_connector.py", "quickbooks_connector.py") for l in (S / "src/connectors" / f).read_text().splitlines() if "set_key" in l or "REFRESH_TOKEN" in l][:8])

# ---- C06 secrets scan over all history (patterns only; matches masked)
h("C06 secrets scan across all history at pinned commit")
revs = sh("git", "rev-list", "--all").split()
pats = {
    "hex32+": r"[0-9a-fA-F]{32,}", "b64-40+": r"[A-Za-z0-9+/=_-]{40,}", "client_secret assign": r"(?i)client_secret\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{10,}",
    "refresh_token assign": r"(?i)refresh_token\s*[=:]\s*['\"]?[A-Za-z0-9_\-\.]{20,}", "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "bearer": r"(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}"}
tot = {}
for name, pat in pats.items():
    out = sh("git", "grep", "-I", "-l", "-E", pat, *revs, "--", ".", ":(exclude)*.db", ":(exclude)*.md", ":(exclude)*.csv")
    files = sorted({l.split(":", 1)[1] for l in out.splitlines() if ":" in l})
    tot[name] = files
    print(f"{name}: {len(files)} file(s) {files[:6]}")

# ---- C07 data labelling
h("C07 committed data: contact names in demo DBs; synthetic banner")
for db in ("demo_ledger.db", "demo_ledger_quickbooks.db", "demo_ledger_large.db"):
    c = sqlite3.connect(f"file:{S/'data'/db}?mode=ro", uri=True)
    names = [r[0] for r in c.execute("select name from contacts order by name")]
    print(db, "contacts:", len(names), "sample:", names[:12])
print("dashboard synthetic banner present:", "synthetic, seeded data" in (S / "dashboard/app.py").read_text())

# ---- C11 data coverage re-performance
h("C11 re-perform data coverage counts")
from src.reconciliation.stats import compute_data_stats  # noqa: E402
for db in ("demo_ledger.db", "demo_ledger_quickbooks.db", "demo_ledger_large.db"):
    c = sqlite3.connect(f"file:{S/'data'/db}?mode=ro", uri=True)
    st = compute_data_stats(c)["quality"]
    indep = {
        "payments_unlinked": c.execute("select count(*) from payments where invoice_id is null or invoice_id=''").fetchone()[0],
        "bank_txns_no_contact": c.execute("select count(*) from bank_transactions where contact_id is null or contact_id=''").fetchone()[0],
        "total_cash_movements": c.execute("select (select count(*) from bank_transactions)+(select count(*) from payments)").fetchone()[0],
        "invoices_voided_or_deleted": c.execute("select count(*) from invoices where status in ('VOIDED','DELETED')").fetchone()[0],
    }
    diff = {k: (st.get(k), v) for k, v in indep.items() if st.get(k) != v}
    print(db, "dashboard vs independent mismatches:", diff or "none", "| values", {k: st.get(k) for k in indep})

# ---- C13/C15/C21/C24/C25/C26/C28: confirm absent controls
h("Absent controls: confirm not in place (C13, C15, C21, C24, C25, C26, C28)")
print("tests dir / test files:", [p.name for p in S.rglob("test*") if ".git" not in p.parts][:5] or "none")
print("git tags:", len(sh("git", "tag").split()))
print("lockfile present:", any((S / f).exists() for f in ("requirements.lock", "poetry.lock", "Pipfile.lock", "uv.lock", "constraints.txt")))
print("requirements pinned (==):", [l for l in (S / "requirements.txt").read_text().splitlines() if "==" in l] or "none")
src = "\n".join(p.read_text() for p in (S / "src").rglob("*.py")) + (S / "dashboard/app.py").read_text()
for kw in ("import logging", "logger", "hashlib", "run_id", "disposition", "approve", "reviewed_by", "sign_off", "__version__"):
    print(f"keyword {kw!r} in code:", kw in src)
schema = (S / "src/db/schema.sql").read_text()
print("schema tables:", re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", schema))
app = (S / "dashboard/app.py").read_text()
print("app.py lines 184-187 caption mentions static/published figure:", "published" in "\n".join(app.splitlines()[183:187]).lower())

# ---- C14 determinism of IsolationForest path
h("C14 IsolationForest determinism (informational; not the default path)")
code = ("import sys,sqlite3,hashlib,json;sys.path.insert(0,%r);from src.anomaly.statistical import find_statistical_outliers as f;"
        "c=sqlite3.connect('file:%s?mode=ro',uri=True);print(hashlib.sha256(json.dumps(sorted(map(str,f(c,'isolation_forest')))).encode()).hexdigest()[:16])") % (str(S), DS / "ledger_test.db")
hs = [subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip() for _ in range(3)]
print("3 fresh-process hashes:", hs, "identical:", len(set(hs)) == 1)

# ---- C16 reproduce published scores
h("C16 reproduce published accuracy figures")
from src.anomaly.statistical import score_against_answer_key, score_against_planted_records  # noqa: E402
from src.pipeline import detect_all  # noqa: E402
from src.reconciliation.matcher import build_reconciliation_report, match_bank_transactions  # noqa: E402


def run(db):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    return detect_all(c, build_reconciliation_report(match_bank_transactions(c)))

det = run(S / "data/demo_ledger_large.db")
r = score_against_planted_records(det, str(S / "data/synthetic_planted.csv"))
print("synthetic:", {k: r[k] for k in ("caught", "total_planted_anomalies", "false_positive_count", "precision", "recall")}, "(README: 84/84, 24 FP, precision 0.778)")
key = ORIG / "data/anomaly_answer_key.csv"
if key.exists():
    det = run(S / "data/demo_ledger.db")
    r = score_against_answer_key(det, str(key))
    print("xero:", {k: r[k] for k in ("caught", "total_planted_anomalies", "false_positive_count", "precision", "recall")}, "(README: 7/7, 3 FP, precision 0.70)")
else:
    print("xero: answer key not available")

# ---- C19 reconciliation list completeness on test data + QuickBooks 0/40 investigation
h("C19 unmatched list completeness (test dataset) and QuickBooks investigation")
c = sqlite3.connect(f"file:{DS/'ledger_test.db'}?mode=ro", uri=True)
matches = match_bank_transactions(c)
rep = build_reconciliation_report(matches)
nm = {m["bank_transaction_id"] for m in matches if m["match_status"] == "no_match"}
listed = {u["bank_transaction_id"] for u in rep["unmatched_items"]}
print("test data: bank lines", len(matches), "no_match", len(nm), "listed", len(listed), "complete:", nm == listed, "pct_auto_matched", rep["pct_auto_matched"])
c = sqlite3.connect(f"file:{S/'data/demo_ledger_quickbooks.db'}?mode=ro", uri=True)
ms = match_bank_transactions(c)
rp = build_reconciliation_report(ms)
print("QuickBooks demo: bank lines", rp["total_bank_transactions"], "auto-matched %", rp["pct_auto_matched"])
print("  bank lines with contact_id:", c.execute("select count(*) from bank_transactions where contact_id is not null and contact_id!=''").fetchone()[0])
print("  bank types:", c.execute("select type,count(*) from bank_transactions group by type").fetchall())
print("  invoices by type:", c.execute("select invoice_type,count(*) from invoices group by invoice_type").fetchall())
print("  distinct bank contacts that also have invoices:", c.execute("select count(distinct bt.contact_id) from bank_transactions bt join invoices i on i.contact_id=bt.contact_id").fetchone()[0])
print("  sample bank rows:", c.execute("select date,total,type,contact_id from bank_transactions limit 3").fetchall())

# ---- C20 variance sentences re-performance
h("C20 variance sentences re-performed from source rows (test dataset)")
from src.variance.explainer import compute_account_movement, explain_movement  # noqa: E402
c = sqlite3.connect(f"file:{DS/'ledger_test.db'}?mode=ro", uri=True)
ok = bad = 0
samples = []
for pa, pb in [("2026-05", "2026-06"), ("2026-06", "2026-07"), ("2026-07", "2026-08")]:
    for mv in compute_account_movement(c, pa, pb)[:5]:
        if not mv["account_code"]:
            continue
        s = explain_movement(c, mv["account_code"], pa, pb)
        a = c.execute("select coalesce(sum(li.line_amount),0) from line_items li join invoices i on i.invoice_id=li.invoice_id where li.account_code=? and substr(i.invoice_date,1,7)=?", (mv["account_code"], pa)).fetchone()[0]
        b = c.execute("select coalesce(sum(li.line_amount),0) from line_items li join invoices i on i.invoice_id=li.invoice_id where li.account_code=? and substr(i.invoice_date,1,7)=?", (mv["account_code"], pb)).fetchone()[0]
        fa, fb = f"£{a:,.0f}", f"£{b:,.0f}"
        good = (fa in s and fb in s) if a else (fb in s)
        ok += good
        bad += (not good)
        samples.append((pa, pb, s, good))
print("sentences checked:", ok + bad, "figures agree with source:", ok, "disagree:", bad)
for pa, pb, s, g in samples[:5]:
    print(" -", pa, pb, g, s)
print("wording implying causation ('driven by') in sentences:", sum("driven by" in s for _, _, s, _ in samples), "of", len(samples))

# ---- C22 reason strings on test detections
h("C22 reason strings on flags (test dataset)")
det = run(DS / "ledger_test.db")
missing = [d for d in det if not d.get("reason")]
weak = [d for d in det if d.get("reason") and (str(d.get("contact_name")) not in d["reason"] and d["target_anomaly_id"] != "A6")]
print("flags", len(det), "without reason", len(missing), "reason lacks contact name (non-A6)", len(weak))

# ---- C27 / C09 documentation checks
h("C27/C09 README wording and disclosures")
rd = (S / "README.md").read_text()
print("'AI-native' present:", "AI-native" in rd, "| says rules-based:", "rules-based" in rd.lower() or "rule-based" in rd.lower(), "| says no LLM:", "no llm" in rd.lower() or "does not use an llm" in rd.lower())
for kw in ("fictional", "synthetic", "not affiliated", "independent", "false negative", "intended use", "owner", "limitation", "not production", "production"):
    print(f"README mentions {kw!r}:", kw in rd.lower())
