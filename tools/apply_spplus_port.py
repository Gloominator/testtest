#!/usr/bin/env python3
"""Apply the PD2 Single-Player-Plus box/card port to this S14/Reawakening tree.

Idempotent: run it after `tools/tc_apply_boosts.py` or `tools/merge_patchstring.py`,
or just re-run it to repair the Hell-only orb wrapper, restored Fate cards, box
items/recipes/strings and the two re-enabled card turn-ins.

What it does (all data-only; no DLL or engine change):
  * Misc.txt: adds gcbx / ccbx using the SP+ v14.0.2 item rows (cleaned names),
    and sets type2=void on the 12 restored cards that lacked it.
  * CubeMain.txt: appends the two-phase Gheed/Charsi cube recipes using the
    local stacked gpXs/skzs/jewf and crf*/iwss codes; enables fswe/fsre and
    clarifies the historical "(DROP DISABLED)" reward notes.
  * TreasureClassEx.txt: appends `Boxes` (gcbx:ccbx = 1:1) and `Orbs (H)`;
    points Hell Good, Map Orbs Drop and Treasure Fallen Orbs H at `Orbs (H)`;
    distributes the 15 restored cards into the six existing Fate pools at Prob 1.
  * patchstring.tbl: appends gcbx, ccbx, gcbxDesc, ccbxDesc via the ELF-hash
    builder in tools/merge_patchstring.py.
  * Removes stale cubemain.bin / misc.bin / itemscode.bin from this repo copy
    (TreasureClassEx.bin was already removed in Stage 2).
  * Expects the two SP+ .dc6 inventory icons to be present in data/global/items.

Preserves CRLF, Latin-1, trailing tabs/columns and the existing *eol/Term=0
convention. Run from anywhere: `python3 tools/apply_spplus_port.py`.
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from merge_patchstring import parse, build, verify  # noqa: E402

MISC = ROOT / "data/global/excel/Misc.txt"
CUBE = ROOT / "data/global/excel/CubeMain.txt"
TCEX = ROOT / "data/global/excel/TreasureClassEx.txt"
TBL = ROOT / "data/local/LNG/ENG/patchstring.tbl"
ICONS = [
    ROOT / "data/global/items/invgcbx.dc6",
    ROOT / "data/global/items/invccbx.dc6",
]
# Compiled tables that correspond to txt files edited below. TreasureClassEx.bin
# was already removed in Stage 2; these three must go so the game recompiles.
STALE_BINS = [
    ROOT / "data/global/excel/cubemain.bin",
    ROOT / "data/global/excel/misc.bin",
    ROOT / "data/global/excel/itemscode.bin",
]

# Exactly 15 restored cards, assigned to the 15 free Item slots across the six
# Fate pools. Every restored card gets Prob 1 (same per-card roll as its pool),
# so the existing 45 cards are diluted rather than protected by a low-weight group.
RESTORED = {
    "Fate Common A": ["fsls"],
    "Fate Common B": ["fsgd"],
    "Fate Common C": ["fsse", "fsmw"],
    "Fate Uncommon A": ["fsdg", "fsdb", "fstb"],
    "Fate Uncommon B": ["fsap", "fsus", "fstm"],
    "Fate Rare A": ["fsdn", "fsht", "fshs", "fswe", "fsre"],
}
ALL_RESTORED = [c for codes in RESTORED.values() for c in codes]
assert len(ALL_RESTORED) == len(set(ALL_RESTORED)) == 15
NON_VOID_CARDS = [
    "fsls", "fsus", "fstm", "fsdn", "fsht", "fsgd", "fshs",
    "fsdg", "fsdb", "fsap", "fsmw", "fstb",
]

# SP+ v14.0.2 Misc rows, with the upstream "Gheeds"/"Charsis" typos corrected.
MISC_ROWS = []
MISC_ROWS.append("Gheed's Curious Box\tGheed's Curious Box\t\t0\t100\t99\t0\t1\t1\t0\t1\t99999\t\t\tgcbx\tgcbx\tgcbx\t16\t1\t1\t0\t0\t0\tflpmss\tinvgcbx\t\t\t0\txxx\t\t\t0\t0\tnorb\t\titem_gem\t12\titem_gem\t0\t0\t5\t0\t0\t0\t0\t0\t0\t0\t\t\t0\t-1\t\t\t\t\t\t\t\t\t\t\t\t1\tgcbxDesc\t\t0\t0\t0\tnon\t0\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t0\t0\t0\txxx\txxx\t\t\tgcbx\tgcbx\tgcbx\t\t\t\t0")
MISC_ROWS.append("Charsi's Crafting Box\tCharsi's Crafting Box\t\t0\t100\t99\t0\t1\t1\t0\t1\t99999\t\t\tccbx\tccbx\tccbx\t16\t1\t1\t0\t0\t0\tflpmss\tinvccbx\t\t\t0\txxx\t\t\t0\t0\tnorb\t\titem_gem\t12\titem_gem\t0\t0\t5\t0\t0\t0\t0\t0\t0\t0\t\t\t0\t-1\t\t\t\t\t\t\t\t\t\t\t\t1\tccbxDesc\t\t0\t0\t0\tnon\t0\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t\t\t255\t\t\t0\t0\t0\txxx\txxx\t\t\tccbx\tccbx\tccbx\t\t\t\t0")

# UTF-8 bytes used by the existing tbl for the D2 colour escape 0xC3 0xBF.
NEW_STRINGS = [
    (b"gcbx", b"\xc3\xbfc4Gheed's Curious Box"),
    (b"ccbx", b"\xc3\xbfc4Charsi's Crafting Box"),
    (b"gcbxDesc", b"Cube twice to receive 50 random perfect gems or 50 jewel fragments."),
    (b"ccbxDesc", b"Cube twice to receive 5 random crafting infusions or 5 catalyst shards."),
]


# ---------------------------------------------------------------- I/O helpers
def read_txt(path: Path):
    raw = path.read_bytes()
    text = raw.decode("latin1")
    crlf = "\r\n" in text
    lines = text.replace("\r\n", "\n").split("\n")
    return lines, crlf


def write_txt(path: Path, lines, crlf: bool):
    out = "\n".join(lines)
    if crlf:
        out = out.replace("\n", "\r\n")
    path.write_bytes(out.encode("latin1"))


def cols(line: str, n: int):
    c = line.split("\t")
    return c + [""] * (n - len(c)) if len(c) < n else c[:n]


def idx_map(hdr):
    return {h: i for i, h in enumerate(hdr)}


def append_row(lines, row):
    """Insert before the terminal empty line produced by a trailing newline."""
    if lines and lines[-1] == "":
        lines.insert(len(lines) - 1, row)
    else:
        lines.append(row)


# ---------------------------------------------------------------- CubeMain row
def cube_row(**kw):
    c = [""] * 105
    c[0] = kw.get("description", "")
    c[1] = str(kw.get("enabled", "1"))
    c[2] = str(kw.get("ladder", ""))
    c[3] = str(kw.get("min diff", ""))
    c[4] = str(kw.get("version", "100"))
    c[5] = str(kw.get("op", ""))
    c[6] = str(kw.get("param", ""))
    c[7] = str(kw.get("value", ""))
    c[9] = str(kw.get("numinputs", "1"))
    c[10] = kw.get("input_1", kw.get("input 1", ""))
    c[17] = kw.get("output", "")
    c[21] = kw.get("mod_1", kw.get("mod 1", ""))
    c[22] = str(kw.get("mod_1_chance", kw.get("mod 1 chance", "")))
    c[24] = str(kw.get("mod_1_min", kw.get("mod 1 min", "")))
    c[25] = str(kw.get("mod_1_max", kw.get("mod 1 max", "")))
    c[104] = "0"                       # *eol
    return "\t".join(c)


def box_recipes():
    rows = []
    # Gheed: v14.0.2 RNG (1501..1515) mapped onto this tree's stacked gem codes.
    rows.append(cube_row(
        description="SP+ GHEED'S CURIOUS BOX - PHASE 1 - ROLL",
        ladder="2", op="18", param="361", value="0", input_1="gcbx",
        output="useitem", mod_1="corruptnum", mod_1_chance="100",
        mod_1_min="1501", mod_1_max="1515",
    ))
    gheed = [
        (1502, "gpvs,qty=50", "Perfect Amethysts"),
        (1504, "gpys,qty=50", "Perfect Topazes"),
        (1506, "skzs,qty=50", "Perfect Skulls"),
        (1508, "gprs,qty=50", "Perfect Rubies"),
        (1510, "gpws,qty=50", "Perfect Diamonds"),
        (1512, "gpbs,qty=50", "Perfect Sapphires"),
        (1514, "gpgs,qty=50", "Perfect Emeralds"),
        (1515, "jewf,qty=50", "Jewel Fragments"),
    ]
    for val, out, label in gheed:
        rows.append(cube_row(
            description=f"SP+ Gheed: {label}",
            op="16", param="361", value=str(val), input_1="gcbx", output=out,
        ))
    # Charsi: v11.0.4 thresholds (5 infusions / 5 catalyst shards), not v14's 10.
    rows.append(cube_row(
        description="SP+ CHARSI'S CRAFTING BOX - PHASE 1 - ROLL",
        ladder="2", op="18", param="361", value="0", input_1="ccbx",
        output="useitem", mod_1="corruptnum", mod_1_chance="100",
        mod_1_min="0", mod_1_max="506",
    ))
    charsi = [
        (66, "crfb,qty=5", "Blood infusion"),
        (133, "crfc,qty=5", "Caster infusion"),
        (200, "crfs,qty=5", "Safety infusion"),
        (267, "crfh,qty=5", "Hitpower infusion"),
        (334, "crfv,qty=5", "Vampiric infusion"),
        (401, "crfu,qty=5", "Bountiful infusion"),
        (468, "crfp,qty=5", "Prismatic infusion"),
        (506, "iwss,qty=5", "Catalyst shards"),
    ]
    for val, out, label in charsi:
        rows.append(cube_row(
            description=f"SP+ Charsi: {label}",
            op="16", param="361", value=str(val), input_1="ccbx", output=out,
        ))
    return rows


# ---------------------------------------------------------------- TCEx row
def tc_row(name, picks, items):
    """Build a 33-column TCEx row. `items` is [(item, prob), ...] up to 10."""
    assert len(items) <= 10
    c = [""] * 33
    c[0] = name
    c[3] = str(picks)
    c[8] = "0"                         # NoDrop
    for i, (item, prob) in enumerate(items):
        c[9 + 2 * i] = item
        c[10 + 2 * i] = str(prob)
    c[32] = "0"                        # Term
    return "\t".join(c)


# ---------------------------------------------------------------- main edits
def do_misc():
    lines, crlf = read_txt(MISC)
    hdr = idx_map(lines[0].split("\t"))
    n = len(lines[0].split("\t"))
    assert n == 172, n
    ci, t2 = hdr["code"], hdr["type2"]
    codes = {cols(l, n)[ci] for l in lines[1:] if l.strip()}
    changed = False
    for row in MISC_ROWS:
        code = row.split("\t")[ci]
        if code not in codes:
            append_row(lines, row)
            codes.add(code)
            changed = True
    fixed = []
    for i, l in enumerate(lines[1:], 1):
        if not l.strip():
            continue
        c = cols(l, n)
        if c[ci] in NON_VOID_CARDS and c[t2] != "void":
            c[t2] = "void"
            lines[i] = "\t".join(c)
            fixed.append(c[ci])
            changed = True
    if changed:
        for l in lines[1:]:
            if l.strip():
                assert len(l.split("\t")) == n, (len(l.split("\t")), n)
        write_txt(MISC, lines, crlf)
    return len(fixed)


def do_cube():
    lines, crlf = read_txt(CUBE)
    hdr = idx_map(lines[0].split("\t"))
    n = len(lines[0].split("\t"))
    assert n == 105, n
    e, desc, inp = hdr["enabled"], hdr["description"], hdr["input 1"]
    enabled = []
    clarified = 0
    for i, l in enumerate(lines[1:], 1):
        if not l.strip():
            continue
        c = cols(l, n)
        d = c[desc]
        if " - INACTIVE" in d and ("Winter's End" in d or "Resilience" in d):
            c[desc] = d.replace(" - INACTIVE", "")
            c[e] = "1"
            lines[i] = "\t".join(c)
            enabled.append(c[desc])
        elif "(DROP DISABLED)" in d:
            c[desc] = d.replace("(DROP DISABLED)", "(reward not a natural drop)")
            lines[i] = "\t".join(c)
            clarified += 1
    appended = 0
    if not any(l.startswith("SP+ GHEED'S CURIOUS BOX") for l in lines):
        for r in box_recipes():
            append_row(lines, r)
            appended += 1
    for l in lines[1:]:
        if l.strip():
            assert len(l.split("\t")) == n, (len(l.split("\t")), n)
    write_txt(CUBE, lines, crlf)
    return enabled, clarified, appended


def do_tcex():
    lines, crlf = read_txt(TCEX)
    hdr = idx_map(lines[0].split("\t"))
    n = len(lines[0].split("\t"))
    assert n == 33, n
    name_i = hdr["Treasure Class"]

    def find(name):
        for i, l in enumerate(lines[1:], 1):
            if l.strip() and cols(l, n)[name_i] == name:
                return i
        raise KeyError(name)

    # 1) New wrapper rows. Orbs (H) = original Orbs + Boxes at exactly mfo's 30/1000.
    orbs_i = find("Orbs")
    oc = cols(lines[orbs_i], n)
    orbs_items = []
    for k in range(1, 11):
        it, pr = oc[hdr[f"Item{k}"]], oc[hdr[f"Prob{k}"]]
        if it:
            orbs_items.append((it, pr))
    assert ("mfo", "30") in orbs_items
    existing = {cols(l, n)[name_i] for l in lines[1:] if l.strip()}
    if "Boxes" not in existing:
        append_row(lines, tc_row("Boxes", 1, [("gcbx", 1), ("ccbx", 1)]))
    if "Orbs (H)" not in existing:
        append_row(lines, tc_row("Orbs (H)", 1, orbs_items + [("Boxes", 30)]))

    # 2) Hell-only switch. Normal/NM and Treasure Fallen N/NM keep plain Orbs.
    switch = ["Act 1 (H) Good", "Act 2 (H) Good", "Act 3 (H) Good",
              "Act 4 (H) Good", "Act 5 (H) Good",
              "Map Orbs Drop", "Treasure Fallen Orbs H"]
    for nm in switch:
        i = find(nm)
        c = cols(lines[i], n)
        found = False
        for k in range(1, 11):
            j = hdr[f"Item{k}"]
            if c[j] == "Orbs":
                c[j] = "Orbs (H)"
                lines[i] = "\t".join(c)
                found = True
                break
            if c[j] == "Orbs (H)":
                found = True
                break
        assert found, f"{nm} references neither Orbs nor Orbs (H)"

    # 3) Restored cards into the six existing pools, Prob 1 each, first free slot.
    for nm, codes in RESTORED.items():
        i = find(nm)
        c = cols(lines[i], n)
        have = {c[hdr[f"Item{k}"]] for k in range(1, 11) if c[hdr[f"Item{k}"]]}
        for code in codes:
            if code in have:
                continue
            for k in range(1, 11):
                ij, pj = hdr[f"Item{k}"], hdr[f"Prob{k}"]
                if not c[ij]:
                    c[ij], c[pj] = code, "1"
                    have.add(code)
                    break
            else:
                raise AssertionError(f"{nm} has no free Item slot for {code}")
        lines[i] = "\t".join(c)

    for l in lines[1:]:
        if l.strip():
            assert len(l.split("\t")) == n, (len(l.split("\t")), n)
    write_txt(TCEX, lines, crlf)


def do_bins():
    removed = []
    for p in STALE_BINS:
        if p.exists():
            p.unlink()
            removed.append(p.name)
    return removed


def do_tbl():
    hdr, warr, entries = parse(str(TBL))
    by_idx = sorted(entries, key=lambda e: e["idx"])
    pairs = [(e["key"], e["val"]) for e in by_idx]
    have = {k for k, _ in pairs}
    for k, v in NEW_STRINGS:
        if k not in have:
            pairs.append((k, v))
    blob, loops = build(pairs)
    bad, content_ok = verify(blob, pairs)
    assert bad == 0 and content_ok, (bad, content_ok)
    TBL.write_bytes(blob)
    return hdr["keycount"], len(pairs), loops, len(blob)


def validate():
    # Icons
    for p in ICONS:
        assert p.exists() and p.stat().st_size > 0, p

    # Misc: box rows + all 60 cards are void
    ml, _ = read_txt(MISC)
    mh = idx_map(ml[0].split("\t"))
    mn = len(ml[0].split("\t"))
    misc = {cols(l, mn)[mh["code"]]: cols(l, mn) for l in ml[1:] if l.strip()}
    for code in ("gcbx", "ccbx"):
        assert code in misc, code
        assert misc[code][mh["type2"]] == "", code
        assert misc[code][mh["invfile"]] == f"inv{code}"
    cards = [c for c in misc if c.startswith("fs")]
    assert len(cards) == 60, len(cards)
    assert all(misc[c][mh["type2"]] == "void" for c in cards)

    # CubeMain: two re-enabled turn-ins, 18 appended box recipes, no duplicates
    cl, _ = read_txt(CUBE)
    ch = idx_map(cl[0].split("\t"))
    cn = len(cl[0].split("\t"))
    cube = [cols(l, cn) for l in cl[1:] if l.strip()]
    assert len(cube) == 3046 + 18, len(cube)
    descs = [c[ch["description"]] for c in cube]
    sp_descs = [d for d in descs if d.startswith("SP+ ")]
    assert len(sp_descs) == len(set(sp_descs)) == 18, "duplicate SP+ CubeMain description"
    for d in ("2 of Winter's End -> rare jewel, CBF",
              "4 of Resilience -> unique jewel, 50% curse length"):
        row = next(c for c in cube if c[ch["description"]].startswith(d))
        assert row[ch["enabled"]] == "1", d

    # TCEx: new rows resolve, all 60 cards in pools, Hell-only box references
    tl, _ = read_txt(TCEX)
    th = idx_map(tl[0].split("\t"))
    tn = len(tl[0].split("\t"))
    tc = {cols(l, tn)[th["Treasure Class"]]: cols(l, tn) for l in tl[1:] if l.strip()}
    assert "Boxes" in tc and "Orbs (H)" in tc
    assert tc["Orbs (H)"][3] == "1"
    boxes = [tc["Orbs (H)"][th[f"Item{k}"]] for k in range(1, 11)]
    assert "Boxes" in boxes and "mfo" in boxes
    refs = Counter()
    pool_cards = set()
    for nm, c in tc.items():
        for k in range(1, 11):
            it = c[th[f"Item{k}"]]
            if not it:
                continue
            if it in ("Orbs", "Orbs (H)"):
                refs[(nm, it)] += 1
            if nm.startswith("Fate ") and it.startswith("fs"):
                pool_cards.add(it)
    assert pool_cards == set(cards), (len(pool_cards), len(cards))
    hell_refs = {nm for (nm, it) in refs if it == "Orbs (H)"}
    assert hell_refs == {"Act 1 (H) Good", "Act 2 (H) Good", "Act 3 (H) Good",
                         "Act 4 (H) Good", "Act 5 (H) Good",
                         "Map Orbs Drop", "Treasure Fallen Orbs H"}, hell_refs
    assert not any(nm.startswith("Act ") and "(H)" not in nm and "(N)" not in nm
                   for (nm, it) in refs if it == "Orbs (H)")

    # patchstring: appended keys findable
    hdr, warr, entries = parse(str(TBL))
    keys = {e["key"]: e["val"] for e in entries}
    for k, v in NEW_STRINGS:
        assert keys.get(k) == v, k
    bad, content_ok = verify(TBL.read_bytes(), [(e["key"], e["val"]) for e in sorted(entries, key=lambda x: x["idx"])])
    assert bad == 0 and content_ok


def main():
    os.chdir(ROOT)
    fixed = do_misc()
    enabled, clarified, appended = do_cube()
    do_tcex()
    old_n, new_n, loops, size = do_tbl()
    removed_bins = do_bins()
    validate()
    print("OK: SP+ port applied/verified")
    print(f"  Misc.txt: 2 box rows present, {fixed} card type2=void fixes")
    print(f"  CubeMain.txt: {len(enabled)} card turn-ins enabled, {clarified} reward notes clarified, {appended} box recipes appended")
    print(f"  TreasureClassEx.txt: Boxes + Orbs (H), 7 Hell refs, 15 restored cards")
    print(f"  patchstring.tbl: {old_n} -> {new_n} keys, NumLoops={loops}, {size} bytes")
    print(f"  stale bins removed: {', '.join(removed_bins) if removed_bins else 'none (already clean)'}")
    print("  Reminder: copy data/ to ProjectD2/data/, delete ProjectD2/data/global/excel/*.bin, launch once.")


if __name__ == "__main__":
    main()
