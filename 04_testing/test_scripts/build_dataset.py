"""Build the synthetic test ledger and ground-truth labels for the Northbridge assurance review.

Ground truth is defined by ACCOUNTING meaning (is this record really an error?), recorded in
labels.csv before the system is run. Hard cases (legitimate items that look like errors) are
labelled clean on purpose. Same schema as Northbridge (src/db/schema.sql). Synthetic data only.

Usage: python build_dataset.py <subject_dir> <out_dir>
"""
from __future__ import annotations

import csv
import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

SUBJECT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
rng = random.Random(2026)

contacts, accounts, invoices, lines, banks, payments, labels = {}, {}, [], [], [], [], []
n = {"AP": 0, "AR": 0, "BT": 0, "PAY": 0}


def nid(p):
    n[p] += 1
    return f"{p}-{n[p]:03d}"


def contact(name, customer=False, supplier=False):
    cid = "C-" + name.upper().replace(" ", "-").replace("&", "AND")
    contacts[cid] = (cid, name, int(customer), int(supplier))
    return cid


def account(code, name, typ):
    accounts[code] = (f"ACC-{code}", code, name, typ, None)


def weekday(d, forward=True):
    step = 1 if forward else -1
    while d.weekday() >= 5:
        d += timedelta(days=step)
    return d


def rand_bizday(lo=date(2026, 1, 5), hi=date(2026, 8, 28)):
    return weekday(lo + timedelta(days=rng.randrange((hi - lo).days)))


def iso(d):
    return d.isoformat() + "T00:00:00"


def label(item_id, unit, cid, d, amt, group, err_type, rule, note):
    labels.append({
        "item_id": item_id, "unit_type": unit, "contact": contacts[cid][1] if cid else "",
        "date": d.isoformat(), "amount": f"{amt:.2f}", "group": group,
        "is_error": 1 if group == "error" else 0, "error_type": err_type,
        "expected_rule": rule, "construction": note})


def bill(cid, code, d, total, tax="INPUT2", group="clean", err="", rule="", note="", desc="Supplier bill"):
    iid = nid("AP")
    vat = round(total - total / 1.2, 2) if tax == "INPUT2" else 0.0
    net = round(total - vat, 2)
    invoices.append((iid, cid, "ACCPAY", iso(d), iso(d + timedelta(days=30)), total, tax, "AUTHORISED"))
    lines.append((f"{iid}-L1", iid, code, desc, 1.0, net, net, tax, vat))
    label(iid, "bill", cid, d, total, group, err, rule, note)
    return iid


def sales(cid, code, d, total, group="clean", err="", rule="", note="", desc="Sales invoice"):
    iid = nid("AR")
    vat = round(total - total / 1.2, 2)
    net = round(total - vat, 2)
    invoices.append((iid, cid, "ACCREC", iso(d), iso(d + timedelta(days=30)), total, "OUTPUT2", "AUTHORISED"))
    lines.append((f"{iid}-L1", iid, code, desc, 1.0, net, net, "OUTPUT2", vat))
    label(iid, "invoice", cid, d, total, group, err, rule, note)
    return iid


def bank(cid, d, total, typ, group="clean", err="", rule="", note=""):
    bid = nid("BT")
    banks.append((bid, cid, iso(d), total, typ, 0))
    label(bid, "bank_txn", cid, d, total, group, err, rule, note)
    return bid


def payment(iid, d, amount, typ):
    pid = nid("PAY")
    payments.append((pid, iid, "ACC-090", iso(d), amount, typ, "AUTHORISED"))
    return pid


for code, name, typ in [("400", "Consulting Fees", "REVENUE"), ("405", "Retainer Fees", "REVENUE"),
                        ("402", "Software Subscriptions", "EXPENSE"), ("406", "Contractor Fees", "EXPENSE"),
                        ("413", "Office Supplies", "EXPENSE"), ("420", "Travel", "EXPENSE"),
                        ("425", "Marketing", "EXPENSE"), ("430", "Professional Fees", "EXPENSE"),
                        ("440", "Utilities", "EXPENSE"), ("450", "Equipment", "EXPENSE"),
                        ("090", "Business Bank Account", "BANK"), ("404", "Bank Fees", "EXPENSE")]:
    account(code, name, typ)

# ---------- 1. Clean regular supplier bills (bills that will be reused later are tracked) ----------
SUP = {  # account -> [(supplier, tax, (lo, hi), count)]
    "402": [("Harbour Cloud Hosting", "INPUT2", (140, 190), 6), ("Pixelworks Software", "INPUT2", (90, 160), 5)],
    "413": [("Stationery Direct", "INPUT2", (40, 110), 5), ("Office Depot UK", "INPUT2", (55, 120), 5)],
    "420": [("Rail Europe Ltd", "INPUT2", (90, 320), 4), ("City Cabs", "INPUT2", (35, 120), 4), ("Skyline Hotels", "INPUT2", (140, 330), 4)],
    "425": [("AdSpark Media", "INPUT2", (150, 400), 5), ("Brightside Print", "INPUT2", (120, 300), 5)],
    "430": [("Marlowe Legal LLP", "INPUT2", (250, 420), 4), ("Pearce Accounting", "INPUT2", (260, 380), 4)],
    "440": [("Northern Power Ltd", "INPUT2", (110, 180), 6), ("Clearwater Utilities", "INPUT2", (95, 150), 6)],
    "406": [("Aoife Byrne Freelance", "NONE", (300, 450), 4), ("Studio Kite Ltd", "INPUT2", (320, 460), 4), ("DevCraft Contractors", "INPUT2", (310, 440), 4)],
    "450": [("Techbench Supplies", "INPUT2", (200, 380), 4), ("Ergo Office Furniture", "INPUT2", (210, 390), 4)],
}
clean_bills = []  # (bill_id, cid, total, date)
sup_bills = {}
for code, sups in SUP.items():
    for name, tax, (lo, hi), cnt in sups:
        cid = contact(name, supplier=True)
        for k in range(cnt):
            total = round(rng.uniform(lo, hi), 2)
            d = rand_bizday()
            bid = bill(cid, code, d, total, tax, note=f"Ordinary {name} bill", desc=f"{name} - {code}")
            clean_bills.append((bid, cid, total, d))
            sup_bills.setdefault(name, []).append(bid)
# recurring fixed-amount subscription (legitimate, MAD=0 style)
cid = contact("FixedFee Backup Services", supplier=True)
for k in range(6):
    d = weekday(date(2026, 1, 12) + timedelta(days=30 * k))
    bid = bill(cid, "402", d, 144.00, "INPUT2", note="Fixed monthly subscription, same amount each month (legitimate)", desc="Backup subscription")
    clean_bills.append((bid, cid, 144.00, d))

# ---------- 2. Error bills ----------
# A2 VAT mis-coding: re-code one bill from four suppliers (consistent INPUT2 history)
for name in ["Northern Power Ltd", "AdSpark Media", "Studio Kite Ltd", "Rail Europe Ltd"]:
    bid = sup_bills[name][2]
    idx = next(i for i, r in enumerate(invoices) if r[0] == bid)
    r = invoices[idx]
    invoices[idx] = r[:6] + ("NONE",) + r[7:]
    li = next(i for i, l in enumerate(lines) if l[1] == bid)
    l = lines[li]
    lines[li] = l[:5] + (r[5], r[5], "NONE", 0.0)  # gross booked as net, no VAT
    for L in labels:
        if L["item_id"] == bid:
            L.update(group="error", is_error=1, error_type="VAT_MISCODE", expected_rule="A2",
                     construction=f"{name} is VAT-registered and normally INPUT2; this bill coded NONE (VAT lost)")

# A3 threshold-avoidance: bills just under the GBP 500 approval limit (split job / single bill)
cid = contact("DevCraft Contractors", supplier=True)
d0 = rand_bizday(date(2026, 3, 2), date(2026, 3, 20))
bill(cid, "406", d0, 488.00, group="error", err="THRESHOLD", rule="A3", note="Split job: two bills same week both just under 500 approval limit")
bill(cid, "406", weekday(d0 + timedelta(days=2)), 492.00, group="error", err="THRESHOLD", rule="A3", note="Second half of split job (see previous)")
cid = contact("AdSpark Media", supplier=True)
bill(cid, "425", rand_bizday(), 497.00, group="error", err="THRESHOLD", rule="A3", note="Single bill priced 3 GBP under the approval limit after quote revised")
# A3 hard-clean: legitimate fixed licence at 489 each month; and boundary values
cid = contact("Cobalt Analytics", supplier=True)
for k in range(3):
    bid = bill(cid, "402", weekday(date(2026, 4, 6) + timedelta(days=30 * k)), 489.00, group="clean_hard",
               note="Legitimate fixed-price licence that happens to sit in the 475-500 band")
bill(cid, "402", rand_bizday(), 474.99, group="clean_hard", note="Boundary: just below the 95% band, should not flag")
bill(cid, "402", rand_bizday(), 500.00, group="clean_hard", note="Boundary: exactly at limit, should not flag")

# A4 weekend-dated bills
wk = [date(2026, 2, 7), date(2026, 5, 17), date(2026, 7, 11)]
for i, d in enumerate(wk):
    cid = contact(["Stationery Direct", "City Cabs", "Pearce Accounting"][i], supplier=True)
    code = ["413", "420", "430"][i]
    bill(cid, code, d, round(rng.uniform(80, 250), 2), group="error", err="WEEKEND", rule="A4",
         note="Bill dated on a weekend for a supplier that does not trade at weekends (unusual timing, review)")
for i, (name, code) in enumerate([("Kestrel Couriers", "420"), ("Marlow Events Catering", "425")]):
    cid = contact(name, supplier=True)
    for d in ([date(2026, 3, 14), date(2026, 6, 20)] if i == 0 else [date(2026, 4, 25), date(2026, 7, 4)]):
        bill(cid, code, d, round(rng.uniform(70, 260), 2), group="clean_hard",
             note=f"{name} trades at weekends; a weekend date is legitimate")
    for d in [rand_bizday() for _ in range(2)]:
        bill(cid, code, d, round(rng.uniform(70, 260), 2), note=f"Ordinary {name} bill")

# A2 hard-clean: supplier became VAT-registered part way through the year
cid = contact("Fenwick Design", supplier=True)
for k in range(3):
    bill(cid, "430", rand_bizday(date(2026, 1, 5), date(2026, 5, 20)), round(rng.uniform(200, 320), 2), "NONE", group="clean_hard",
         note="Before supplier's VAT registration on 1 Jun 2026: NONE is correct")
for k in range(4):
    bill(cid, "430", rand_bizday(date(2026, 6, 3), date(2026, 8, 28)), round(rng.uniform(200, 320), 2), "INPUT2", note="After VAT registration: INPUT2 is correct")

# A7 outliers (about 9x the account norm) and legitimate large one-offs
for code, cname, amt in [("420", "Rail Europe Ltd", 2890.00), ("413", "Stationery Direct", 1150.00), ("440", "Clearwater Utilities", 1620.00)]:
    bill(contact(cname, supplier=True), code, rand_bizday(), amt, group="error", err="OUTLIER", rule="A7",
         note="Amount roughly 9x the normal amount for this account with no supporting explanation")
for amt, nm in [(2900.00, "Techbench Supplies"), (3600.00, "Ergo Office Furniture")]:
    bill(contact(nm, supplier=True), "450", rand_bizday(), amt, group="clean_hard",
         note="Legitimate one-off capital purchase (new equipment); large but valid")

# Duplicate supplier bills (AP): second bill same supplier and amount 2-5 days later
for nm, code in [("Brightside Print", "425"), ("Skyline Hotels", "420"), ("Pearce Accounting", "430")]:
    src = next(b for b in clean_bills if contacts[b[1]][1] == nm)
    bill(src[1], code, weekday(src[3] + timedelta(days=rng.randint(2, 5))), src[2], group="error", err="DUP_AP", rule="A1",
         note=f"Duplicate of {src[0]} (same supplier, same amount, days later)")

# ---------- 3. Sales invoices ----------
for nm, amt in [("Alder Group", 1200.00), ("Brookes Partners", 1800.00), ("Crestline Retail", 2400.00)]:
    cid = contact(nm, customer=True)
    for k in range(6):
        sales(cid, "405", weekday(date(2026, 1, 15) + timedelta(days=30 * k)), amt, note=f"Monthly retainer for {nm} (legitimate recurring)")
cust = {}
for nm in ["Dunmore Ltd", "Elm & Oak", "Fairway Foods", "Granite Systems", "Hollis Media"]:
    cid = contact(nm, customer=True); cust[nm] = cid
    for k in range(4):
        sales(cid, "400", rand_bizday(), round(rng.uniform(600, 2600), 2), note="Consulting invoice")
# hard clean: bi-weekly billing same amount
cid = contact("Ironbridge Labs", customer=True)
for k in range(4):
    sales(cid, "400", weekday(date(2026, 2, 2) + timedelta(days=14 * k)), 900.00, group="clean_hard", note="Bi-weekly billing at same amount, 14 days apart (legitimate)")
# hard clean: same amount, same day, different customers
d = date(2026, 5, 11)
for nm in ["Jasper Co", "Kilburn Ltd"]:
    sales(contact(nm, customer=True), "400", d, 1500.00, group="clean_hard", note="Same amount and date as another customer's invoice (different customer)")
# hard clean: invoice and credit note reversing it
cid = contact("Larch Holdings", customer=True)
sales(cid, "400", date(2026, 6, 1), 1350.00, group="clean_hard", note="Invoice later reversed by credit note")
sales(cid, "400", date(2026, 6, 4), -1350.00, group="clean_hard", note="Credit note reversing the invoice above (negative total)")
# errors: duplicates (AR)
for nm in ["Dunmore Ltd", "Fairway Foods", "Hollis Media"]:
    src = next(i for i in invoices if i[1] == cust[nm] and i[2] == "ACCREC")
    d = date.fromisoformat(src[3][:10])
    sales(cust[nm], "400", weekday(d + timedelta(days=rng.randint(1, 6))), src[5], group="error", err="DUP_AR", rule="A1",
          note=f"Duplicate of {src[0]} (same customer and amount, within days)")
src = next(i for i in invoices if i[1] == cust["Granite Systems"] and i[2] == "ACCREC")
d = date.fromisoformat(src[3][:10])
for k in (1, 2):
    sales(cust["Granite Systems"], "400", weekday(d + timedelta(days=2 * k)), src[5], group="error", err="DUP_AR", rule="A1",
          note=f"Entered again ({k + 1}th time) with same customer and amount: {src[0]}")

# ---------- 4. Bank lines and payments ----------
ap_clean = [b for b in clean_bills if contacts[b[1]][1] != "FixedFee Backup Services"]
rng.shuffle(ap_clean)
paid_bank_ap, paid_pay_ap = ap_clean[:20], ap_clean[20:45]
for k, (bid, cid, total, d) in enumerate(paid_bank_ap):
    diff = [0.01, -0.50, 1.25, -2.99][k] if k < 4 else 0.0
    bank(cid, weekday(d + timedelta(days=rng.randint(20, 32))), round(total + diff, 2), "SPEND",
         group="clean_hard" if k < 4 else "clean",
         note=("Rounding difference of GBP %.2f vs bill (should still reconcile)" % diff) if k < 4 else f"Payment of {bid} by bank")
for bid, cid, total, d in paid_pay_ap:
    payment(bid, weekday(d + timedelta(days=rng.randint(15, 30))), total, "ACCPAYPAYMENT")

ar_clean = [i for i in invoices if i[2] == "ACCREC" and i[5] > 0 and
            next(L for L in labels if L["item_id"] == i[0])["group"] == "clean"]
rng.shuffle(ar_clean)
for i in ar_clean[:20]:
    d = date.fromisoformat(i[3][:10])
    bank(i[1], weekday(d + timedelta(days=rng.randint(20, 32))), i[5], "RECEIVE", note=f"Receipt for {i[0]}")
for i in ar_clean[20:34]:
    d = date.fromisoformat(i[3][:10])
    payment(i[0], weekday(d + timedelta(days=rng.randint(15, 30))), i[5], "ACCRECPAYMENT")

# Duplicate payments (A5): bill paid via Payment AND again by a bank spend line
for bid, cid, total, d in paid_pay_ap[:4]:
    bank(cid, weekday(d + timedelta(days=rng.randint(24, 34))), total, "SPEND", group="error", err="DUP_PAY", rule="A5",
         note=f"Bill {bid} already paid via recorded payment; second bank payment of the same amount")
# Reconciliation breaks (A6)
for nm, amt in [("Kingsley Consulting Ltd", 730.00), ("Vantage Holdings", 1265.40), ("Orchid Trading", 312.75)]:
    bank(contact(nm, supplier=True), rand_bizday(), amt, "SPEND", group="error", err="BREAK", rule="A6",
         note="Payment to a payee with no bill or invoice in the ledger")
for bid, cid, total, d in [b for b in ap_clean[45:] if b[2] > 250][:2]:
    bank(cid, weekday(d + timedelta(days=25)), round(total - max(45.0, total * 0.05), 2), "SPEND", group="error", err="BREAK", rule="A6",
         note=f"Short payment against {bid}: bank amount differs from bill by more than tolerance")
bank(None, rand_bizday(), 415.00, "SPEND", group="error", err="BREAK", rule="A6", note="Bank line with no contact and no matching document")
# Legitimate unmatched lines (bank charges): no bill ever exists
bk = contact("Northbridge Bank", supplier=True)
for m in range(1, 7):
    bank(bk, date(2026, m, 28) if date(2026, m, 28).weekday() < 5 else weekday(date(2026, m, 28), False), 15.00, "SPEND", group="clean_hard",
         note="Monthly bank charge; legitimately has no bill (reconciliation will list it as unmatched)")

# ---------- write DB ----------
db = OUT / "ledger_test.db"
db.unlink(missing_ok=True)
conn = sqlite3.connect(db)
conn.executescript((SUBJECT / "src/db/schema.sql").read_text())
conn.executemany("INSERT INTO accounts VALUES (?,?,?,?,?)", accounts.values())
conn.executemany("INSERT INTO contacts VALUES (?,?,?,?)", contacts.values())
conn.executemany("INSERT INTO invoices VALUES (?,?,?,?,?,?,?,?)", invoices)
conn.executemany("INSERT INTO line_items VALUES (?,?,?,?,?,?,?,?,?)", lines)
conn.executemany("INSERT INTO bank_transactions VALUES (?,?,?,?,?,?)", banks)
conn.executemany("INSERT INTO payments VALUES (?,?,?,?,?,?,?)", payments)
conn.commit()
conn.close()

with open(OUT / "labels.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(labels[0].keys()))
    w.writeheader()
    w.writerows(labels)

from collections import Counter
c = Counter((L["unit_type"], L["group"]) for L in labels)
print("units", len(labels), "errors", sum(L["is_error"] for L in labels), "clean", sum(1 - L["is_error"] for L in labels))
print("by error type", Counter(L["error_type"] for L in labels if L["is_error"]))
print("by group", Counter(L["group"] for L in labels))
print("payments", len(payments), "contacts", len(contacts))
