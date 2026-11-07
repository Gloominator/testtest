"""Port Reawakening's intentional skill edits onto the S14 data.

Run from the scout directory. Ordinary edits are isolated by comparing each
Reawakening commit with its parent; the two official S11 import commits are
excluded. Only cells touched by those commits are taken from the final S11
source, so unrelated S14 fields remain intact.
"""
import argparse
from collections import Counter, defaultdict
import os
import re
import subprocess
import sys

import merge_patchstring as tbl

MOD_REPO = "pd2-reawakening"
MOD = os.path.join(MOD_REPO, "data", "global", "excel")
OUT = os.path.join("..", "reawakening-s14", "data", "global", "excel")
SEASON_IMPORTS = {"4e03dc8", "308bca9", "fad81aa"}
TABLES = ("Skills.txt", "Skilldesc.txt", "Missiles.txt", "MonStats.txt", "MonProp.txt", "PetType.txt")
SUMMONS = {
    "bloodgolem", "claygolem", "firegolem", "irongolem", "necroskeleton",
    "necroarcher", "necromage", "valkyrie", "dopplezonnew", "druidhawk",
    "druidbear", "spiritwolf", "fenris", "voidling", "shadowwarrior",
    "chainlightningsentry", "hydra1", "hydra2", "hydra3", "lesserhydra1",
    "lesserhydra2", "lesserhydra3",
}
MASTERY_ROWS = {
    "One Hand Mastery": ("General Mastery", "general mastery", 128),
    "Two Hand Mastery": ("Pole Arm and Spear Mastery", "pole arm and spear mastery", 134),
}
ITEM_TABLES = (
    "UniqueItems.txt", "SetItems.txt", "Sets.txt", "Runes.txt", "MagicPrefix.txt",
    "MagicSuffix.txt", "AutoMagic.txt", "CubeMain.txt",
)
STRING_KEYS = {
    "StrExtraRevives2", "StrExtraSpirits", "ExtraGrizzly", "ExtraSkeleWar",
    "ExtraSkeleMage", "ExtraSkeleArcher", "ExtraGolem", "ExtraHydra", "ExtraValk",
    "GustReduction", "joustreduction", "ExtraSkeleMageGrim", "dragonflightreduction",
    "SacrificeLongDesc", "StrChanceToParry", "GustLongDesc", "StrIncreasedBombs",
    "skillsd9_PD2", "skillld9_PD2", "skillld19_PD2", "skillld23_PD2",
    "skillsd54_PD2", "skillld54_PD2", "skillname128_PD2", "skillsd128_PD2",
    "skillld128_PD2", "skillan128_PD2", "skillname134_PD2", "skillsd134_PD2",
    "skillld134_PD2", "skillan134_PD2", "FrenzyDurationDesc", "ExtraShadow",
    "ExtraSpiritWolf", "JoustreductionZeraes", "PVPTome2Paragraph2", "PVPTome2Paragraph3",
}
for difficulty in ("Normal", "Nightmare", "Hell"):
    STRING_KEYS.add(difficulty + "BasePVPModifier")
    for charclass in ("Amazon", "Assassin", "Barbarian", "Druid", "Necromancer", "Paladin", "Sorceress"):
        STRING_KEYS.add(difficulty + charclass + "PVPModifiers")


def load(path):
    with open(path, "r", encoding="latin1", newline="") as f:
        raw = f.read()
    lines = raw.splitlines()
    header = lines[0].split("\t")
    trailing = header and header[-1] == ""
    if trailing:
        header.pop()
    rows = [line.split("\t") for line in lines[1:] if line.strip()]
    return header, rows, trailing


def save(path, header, rows, trailing):
    width = len(header)
    with open(path, "w", encoding="latin1", newline="") as f:
        first = "\t".join(header) + ("\t" if trailing else "")
        f.write(first + "\r\n")
        for row in rows:
            row = row[:width] + [""] * max(0, width - len(row))
            f.write("\t".join(row) + ("\t" if trailing else "") + "\r\n")


def keyed(rows):
    return {row[0]: row for row in rows}


def git_show(revision, path):
    result = subprocess.run(
        ["git", "-C", MOD_REPO, "show", revision + ":" + path],
        capture_output=True,
    )
    if result.returncode:
        return None
    return result.stdout.decode("latin1").splitlines()


def history_rows(lines):
    header = lines[0].split("\t")
    while header and header[-1] == "":
        header.pop()
    rows = keyed([line.split("\t") for line in lines[1:] if line.strip()])
    return header, rows


def intentional_cells(filename):
    path = "data/global/excel/" + filename
    command = ["git", "-C", MOD_REPO, "log", "--format=%H %h", "--", path]
    commits = subprocess.check_output(command, text=True).splitlines()
    touched = defaultdict(set)
    for line in commits:
        commit, short = line.split()
        if short in SEASON_IMPORTS:
            continue
        old_lines = git_show(commit + "^", path)
        new_lines = git_show(commit, path)
        if old_lines is None or new_lines is None:
            continue
        old_header, old_rows = history_rows(old_lines)
        new_header, new_rows = history_rows(new_lines)
        if old_header != new_header:
            raise RuntimeError(f"Header changed in {short}:{filename}; review required")
        for name in old_rows.keys() & new_rows.keys():
            if filename in {"MonStats.txt", "MonProp.txt"} and name not in SUMMONS:
                continue
            old = old_rows[name]
            new = new_rows[name]
            for index, column in enumerate(old_header):
                before = old[index] if index < len(old) else ""
                after = new[index] if index < len(new) else ""
                if before != after and column != "Id":
                    touched[name].add(column)
    return touched


def apply_edits(filename, touched):
    mod_header, mod_rows, _ = load(os.path.join(MOD, filename))
    out_path = os.path.join(OUT, filename)
    out_header, out_rows, trailing = load(out_path)
    mod_by_name = keyed(mod_rows)
    common = {name: i for i, name in enumerate(out_header) if name in mod_header}
    mod_index = {name: i for i, name in enumerate(mod_header)}
    changes = 0
    missing = []
    for row in out_rows:
        name = row[0]
        columns = touched.get(name, set())
        if name not in mod_by_name:
            if columns:
                missing.append(name)
            continue
        source = mod_by_name[name]
        for column in columns:
            if column not in common:
                continue
            target_i = common[column]
            source_i = mod_index[column]
            value = source[source_i] if source_i < len(source) else ""
            if filename == "MonProp.txt" and value == "inc_splash_radius":
                value = "inc-splash-radius"
            if target_i >= len(row):
                row.extend([""] * (target_i + 1 - len(row)))
            if row[target_i] != value:
                row[target_i] = value
                changes += 1
    if missing:
        raise RuntimeError(f"{filename}: edited rows absent from final S11 source: {missing}")
    if filename == "MonProp.txt":
        for row in out_rows:
            for i, value in enumerate(row):
                if value == "inc_splash_radius":
                    row[i] = "inc-splash-radius"
                    changes += 1
    return out_header, out_rows, trailing, changes


def apply_initial_exceptions(header, rows):
    mod_header, mod_rows, _ = load(os.path.join(MOD, "Skills.txt"))
    mod = keyed(mod_rows)
    target = keyed(rows)
    hi = {name: i for i, name in enumerate(header)}
    mi = {name: i for i, name in enumerate(mod_header)}
    changes = 0

    dragon = target["Dragon Flight"]
    source = mod["Dragon Flight"]
    value = source[mi["delay"]]
    if dragon[hi["delay"]] != value:
        dragon[hi["delay"]] = value
        changes += 1

    for target_name, (source_name, descriptor, expected_id) in MASTERY_ROWS.items():
        row = target[target_name]
        source = mod[source_name]
        if int(row[hi["Id"]]) != expected_id:
            raise RuntimeError(f"Unexpected mastery row Id: {target_name}")
        for column, target_i in hi.items():
            if column in {"skill", "Id", "skilldesc"} or column not in mi:
                continue
            source_i = mi[column]
            value = source[source_i] if source_i < len(source) else ""
            if target_i >= len(row):
                row.extend([""] * (target_i + 1 - len(row)))
            if row[target_i] != value:
                row[target_i] = value
                changes += 1
        if row[hi["skilldesc"]] != descriptor:
            row[hi["skilldesc"]] = descriptor
            changes += 1
    return changes


def property_column(header, column):
    normalized = column.strip().lower()
    if "prop" in normalized:
        target = normalized.replace("prop", "par")
    elif "code" in normalized:
        target = normalized.replace("code", "param")
    elif normalized.startswith("mod"):
        target = normalized + " param"
    else:
        return None
    return {name.strip().lower(): i for i, name in enumerate(header)}.get(target)


def mastery_skill_params():
    header, rows, _ = load(os.path.join(OUT, "Properties.txt"))
    skill_stats = {
        "item_skillonequip", "item_skillonattack", "item_skillonkill", "item_skillondeath",
        "item_skillonstriking", "item_skillonstruck", "item_skillonlevelup", "item_aura",
        "item_charged_skill", "item_nonclassskill", "item_singleskill",
        "item_skillonequip_display", "item_nonclassskill_display",
    }
    stat_columns = [i for i, name in enumerate(header) if re.fullmatch(r"stat[1-7]", name or "")]
    codes = set()
    for row in rows:
        stats = {row[i].strip() for i in stat_columns if i < len(row) and row[i].strip()}
        if stats & skill_stats:
            codes.add(row[0])
    return codes


def remap_mastery_references():
    skills_header, skills_rows, _ = load(os.path.join(OUT, "Skills.txt"))
    skills = keyed(skills_rows)
    id_i = skills_header.index("Id")
    remap = {
        skills["General Mastery"][id_i]: skills["One Hand Mastery"][id_i],
        skills["Pole Arm and Spear Mastery"][id_i]: skills["Two Hand Mastery"][id_i],
    }
    skill_props = mastery_skill_params()
    prop_pattern = re.compile(r"^(prop ?\d+|mod ?\d+ ?code|mod ?\d+|t1code ?\d+|pcode ?\d+[ab]?)$", re.I)
    changes = 0
    for filename in ITEM_TABLES:
        path = os.path.join(OUT, filename)
        header, rows, trailing = load(path)
        for row in rows:
            for i, column in enumerate(header):
                if i >= len(row) or not prop_pattern.match(column or "") or row[i] not in skill_props:
                    continue
                param_i = property_column(header, column)
                if param_i is not None and param_i < len(row) and row[param_i] in remap:
                    row[param_i] = remap[row[param_i]]
                    changes += 1
        if changes:
            save(path, header, rows, trailing)
    return changes


def restore_strings(apply):
    mod_path = os.path.join(MOD_REPO, "data", "local", "LNG", "ENG", "patchstring.tbl")
    out_path = os.path.join("..", "reawakening-s14", "data", "local", "LNG", "ENG", "patchstring.tbl")
    _, _, mod_entries = tbl.parse(mod_path)
    _, _, out_entries = tbl.parse(out_path)
    mod_values = {}
    for entry in sorted(mod_entries, key=lambda e: e["idx"]):
        key = entry["key"].decode("latin1")
        if key in STRING_KEYS:
            mod_values.setdefault(key, set()).add(entry["val"])
    missing = STRING_KEYS - mod_values.keys()
    if missing:
        raise RuntimeError(f"Missing Reawakening strings: {sorted(missing)}")
    ambiguous = {key for key, values in mod_values.items() if len(values) != 1}
    if ambiguous:
        raise RuntimeError(f"Ambiguous Reawakening strings: {sorted(ambiguous)}")
    values = {key.encode("latin1"): next(iter(mod_values[key])) for key in STRING_KEYS}
    pairs = [(e["key"], e["val"]) for e in sorted(out_entries, key=lambda e: e["idx"])]
    changed = 0
    result = []
    for key, value in pairs:
        if key in values and value != values[key]:
            value = values[key]
            changed += 1
        result.append((key, value))
    blob, loops = tbl.build(result)
    bad, ok = tbl.verify(blob, result)
    if bad or not ok:
        raise RuntimeError(f"String table verification failed: bad={bad}, content_ok={ok}")
    if apply:
        with open(out_path, "wb") as f:
            f.write(blob)
    return changed, loops


def verify(touched):
    errors = []
    for filename in TABLES:
        mod_header, mod_rows, _ = load(os.path.join(MOD, filename))
        out_header, out_rows, _ = load(os.path.join(OUT, filename))
        mod = keyed(mod_rows)
        out = keyed(out_rows)
        mi = {name: i for i, name in enumerate(mod_header)}
        oi = {name: i for i, name in enumerate(out_header)}
        for name, columns in touched.items():
            if name not in mod or name not in out:
                continue
            for column in columns:
                if column not in mi or column not in oi:
                    continue
                source_i, target_i = mi[column], oi[column]
                expected = mod[name][source_i] if source_i < len(mod[name]) else ""
                if filename == "MonProp.txt" and expected == "inc_splash_radius":
                    expected = "inc-splash-radius"
                actual = out[name][target_i] if target_i < len(out[name]) else ""
                if actual != expected:
                    errors.append(f"{filename}:{name}:{column}: {actual!r} != {expected!r}")
        if filename in {"Skills.txt", "Missiles.txt"}:
            id_i = out_header.index("Id")
            for index, row in enumerate(out_rows):
                if row[id_i] != str(index):
                    errors.append(f"{filename}: row {index} has Id {row[id_i]}")

    header, rows, _ = load(os.path.join(OUT, "Skills.txt"))
    oi = {name: i for i, name in enumerate(header)}
    counts = Counter(row[oi["charclass"]] for row in rows if row[oi["charclass"]])
    expected_counts = {"ama": 36, "sor": 36, "nec": 36, "pal": 36, "bar": 36, "dru": 36, "ass": 36}
    if counts != expected_counts:
        errors.append(f"Class skill counts: {dict(counts)}")
    names = [row[0] for row in rows]
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    if duplicates:
        errors.append(f"Duplicate skill names: {duplicates}")

    stat_header, stat_rows, _ = load(os.path.join(OUT, "ItemStatCost.txt"))
    stats = {row[0] for row in stat_rows}
    stat_pattern = re.compile(r"stat\('([^']+)'", re.I)
    for row in rows:
        for value in row:
            for stat in stat_pattern.findall(value):
                if stat not in stats:
                    errors.append(f"Missing stat {stat!r} referenced by {row[0]}")

    for target_name, (_, descriptor, expected_id) in MASTERY_ROWS.items():
        row = keyed(rows)[target_name]
        if row[oi["Id"]] != str(expected_id) or row[oi["skilldesc"]] != descriptor:
            errors.append(f"Mastery replacement invalid: {target_name}")
    for unused in MASTERY_ROWS.values():
        row = keyed(rows)[unused[0]]
        if row[oi["charclass"]]:
            errors.append(f"Unused appended mastery is class-tagged: {unused[0]}")

    changed, _ = restore_strings(apply=False)
    if changed:
        errors.append(f"{changed} skill strings still differ from Reawakening")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify without writing files")
    args = parser.parse_args()
    touched = {filename: intentional_cells(filename) for filename in TABLES}
    if args.check:
        errors = verify(touched)
        if errors:
            print("\n".join(errors))
            return 1
        print("Reawakening skill port verification passed")
        print("Tracked edited rows:", {name: len(rows) for name, rows in touched.items()})
        return 0

    totals = {}
    for filename in TABLES:
        header, rows, trailing, changes = apply_edits(filename, touched[filename])
        if filename == "Skills.txt":
            changes += apply_initial_exceptions(header, rows)
        save(os.path.join(OUT, filename), header, rows, trailing)
        totals[filename] = changes
    totals["mastery item references"] = remap_mastery_references()
    totals["patchstring values"], loops = restore_strings(apply=True)
    errors = verify(touched)
    if errors:
        print("\n".join(errors))
        return 1
    print("Applied changes:", totals)
    print("String table NumLoops:", loops)
    print("Verification passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
