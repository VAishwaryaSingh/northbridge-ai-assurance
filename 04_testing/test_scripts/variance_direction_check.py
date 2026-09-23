"""C20 follow-up: do the named drivers move in the same direction as the headline? Usage: python variance_direction_check.py <subject> <dataset>"""
import sys, sqlite3, re
sys.path.insert(0, sys.argv[1])
from src.variance.explainer import compute_account_movement, explain_movement
c = sqlite3.connect(f"file:{sys.argv[2]}/ledger_test.db?mode=ro", uri=True)
tot = contra = 0
ex = []
for m0 in range(1, 8):
    pa, pb = f"2026-{m0:02d}", f"2026-{m0+1:02d}"
    for mv in compute_account_movement(c, pa, pb):
        if not mv["account_code"]:
            continue
        s = explain_movement(c, mv["account_code"], pa, pb)
        h = re.search(r" (up|down) \d+%", s)
        if not h or "driven by" not in s:
            continue
        tot += 1
        drivers = re.findall(r"\(([+-])£", s.split("driven by")[1])
        if any((d == "+") != (h.group(1) == "up") for d in drivers):
            contra += 1
            ex.append(s)
print("sentences with an up/down headline and named drivers:", tot)
print("of which a named driver moves opposite to the headline:", contra)
for e in ex[:4]:
    print(" -", e)
