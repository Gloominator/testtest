import subprocess, csv, io, sys
csv.field_size_limit(2**31 - 1)

REPO = r"C:\Diablo II - Lord of Destruction\reawakening-s14"
PATH = "data/global/excel/CubeMain.txt"

def load(rev):
    raw = subprocess.run(["git", "show", f"{rev}:{PATH}"], capture_output=True, cwd=REPO).stdout
    text = raw.decode("cp1252", errors="replace").replace("\r\n", "\n")
    rows = list(csv.reader(io.StringIO(text), delimiter="\t"))
    header = rows[0]
    out = []
    for r in rows[1:]:
        if len(r) < 15 or not r[0].strip():
            continue
        d = dict(zip(header, r))
        if d.get("description", "").strip().upper() == "MAPS":  # section marker
            continue
        out.append(d)
    return out

def sig(d):
    """signature: normalized key fields"""
    fields = ["description","enabled","ladder","min diff","version","op","param","value",
              "class","numinputs","input 1","input 2","input 3","input 4","input 5",
              "input 6","input 7","output","lvl","plvl","ilvl","output b","output c"]
    return tuple(" ".join((d.get(f,"") or "").split()).lower() for f in fields)

base = load("6206a2c")
cur = load("HEAD")

from collections import Counter
cb = Counter(sig(d) for d in base)
added, removed = [], []
seen = Counter()
for d in cur:
    s = sig(d)
    seen[s] += 1
    if seen[s] > cb.get(s, 0):
        added.append(d)
seenb = Counter()
for d in base:
    s = sig(d)
    seenb[s] += 1
    if seenb[s] > Counter(sig(x) for x in cur).get(s, 0):
        removed.append(d)

def show(rows, title):
    print(f"\n===== {title} ({len(rows)}) =====")
    for d in rows:
        ins = [d.get(f"input {i}","") for i in range(1,8)]
        ins = [i for i in ins if i]
        outs = [d.get("output",""), d.get("output b",""), d.get("output c","")]
        outs = [o for o in outs if o]
        en = "ON " if d.get("enabled")=="1" else "off"
        print(f"[{en}] {d.get('description','').strip()}\n    {' + '.join(ins)}  =>  {' | '.join(outs)}")

show(added, "ADDED by Reawakening")
show(removed, "REMOVED vs S14 vanilla")
