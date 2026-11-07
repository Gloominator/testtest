# Plan: Disenchant Uniques and Sets into Eternal Coins

## Status

Implemented 2026-11-07 (approved by user request). The three recipes were appended to
`data/global/excel/CubeMain.txt` (byte-append only; cp1252/CRLF preserved; 3 046 data
rows), all static checks in step 3 passed (105-column format, exact cell values, no
duplicates, `key`/`ncoi`/`dvia` resolve in `Misc.txt`, integrity checker shows no new
issues vs. baseline), and `docs/ra_cube_recipes.md` §17 documents the feature.

Deployed: the edited file was copied to `ProjectD2/data/global/excel/CubeMain.txt`
(byte-verified) and the old `cubemain.bin` was deleted so the game recompiles from text.

**Not yet done:** the in-game acceptance tests below (sections A–G) have not been
performed. Do not treat the feature as verified end-to-end until they pass.
Launch `ProjectD2/PlugY.exe` directly (not the RA launcher) with a disposable
character and run tests A–G.

## Feasibility

**Yes, this is possible with the existing Diablo II cube system.** No DLL, code, new item, new stat, or localization change is needed.

The authoritative source is the local game data, not the wiki:

- `data/global/excel/CubeMain.txt` already uses quality filters such as `weap,uni`, `armo,set`, `char,uni`, and `jew,uni`.
- More importantly, existing Tainted Jeweller's Orb recipes use `any,sock,uni` and `any,sock,set`. This establishes that the broad `any` item-type filter works with unique and set quality filters.
- `Misc.txt` already defines Eternal Coin as `ncoi` and Vial of Awakening as `dvia`.
- Existing recipes already use quantities such as `ncoi,qty=4` and outputs such as `dvia,qty=10`.

Implement this as **three generic CubeMain rows**, not hundreds of per-item recipes.

## Required behavior

| Recipe | Inputs | Output |
|---|---|---|
| Disenchant a unique | One item of unique quality + one `key` | One `ncoi` |
| Disenchant a set item | One item of set quality + one `key` | One `ncoi` |
| Exchange Eternal Coins | Five `ncoi` | One `dvia` |

There is no key in the coin-to-vial exchange. Five disenchanting operations therefore cost five items and five keys total, after which the five resulting coins can become one Vial of Awakening.

All unique and set items have the same disenchanting value in this first version: exactly one coin. Do not add rarity tiers, extra outputs, random outcomes, or additional currencies.

## Confirmed scope

These decisions are part of the requested behavior, not optional enhancements:

1. **Match actual item quality, not merely membership in an item table.** A normal/magic/rare item whose base type also has a unique variant must not disenchant. Only an item actually generated as unique (`uni`) or set (`set`) matches.
2. **Include Reawakening automatically.** RA uniques, replicas, legacy items, unique jewels, unique charms, and unique quivers all have unique quality at runtime. The generic `any,uni` recipe covers them without a separate RA list.
3. **Include unique jewels and all unique charms.** Do not limit the feature to weapons and armor.
4. **Include unique maps and special/trophy charms.** This is explicitly approved. `any,uni` includes unique map items and unique trophy/dev charms if a character possesses them. The implementer must not add exclusions or replace the generic recipe with narrower item categories.
5. **Include modified items.** Ethereal, socketed, corrupted, awakened, mirrored, and otherwise modified unique/set items still match their quality. Disenchanting destroys the item. Socket contents are expected to be destroyed with it; this must be tested and treated as an irreversible operation.
6. **Table enabled flags do not restrict an existing item.** Even an item definition with `enabled=0` can still have unique quality if obtained through old saves or special means. The generic recipe matches the item's quality, not the definition's drop-enabled flag.
7. **Eternal Coins are not a stacked rune/gem type.** The five-coin recipe means five separate `ncoi` items in the cube. Do not introduce a new stacked coin code or alter `Misc.txt`.

## Files to change

Required:

- `data/global/excel/CubeMain.txt` — append exactly three enabled recipes.
- `docs/ra_cube_recipes.md` — add a short section documenting the three recipes and the broad unique-map/special-item behavior.

Do **not** change:

- `UniqueItems.txt`
- `SetItems.txt`
- `Misc.txt`
- `ItemTypes.txt`
- `ItemStatCost.txt`
- any DLL or BH/loot-filter file
- any save file
- the launcher configuration

Do not create an item list from the PD2 wiki. The local tables and runtime item quality are more complete and avoid stale wiki data.

## Why generic quality recipes are the correct design

A per-item approach is unnecessarily fragile:

- `UniqueItems.txt` currently has 672 definition rows and `SetItems.txt` has 136. Generating more than 800 cube rows would add substantial maintenance and conflict risk for no additional behavior.
- Multiple unique definitions share a base item code. For example, Rainbow Facet and Split Personality have several variants on base code `jew`. A recipe for base code `jew` without `uni` would incorrectly accept non-unique jewels.
- Some unique definitions are disabled, while existing copies can still remain in saves.
- Future PD2 or RA additions would need another generated recipe. A quality-based recipe covers future unique/set items automatically.
- Item names are not stable identifiers and should never be used as cube inputs.

The two quality rows are therefore both simpler and more complete.

## Exact CubeMain values

`CubeMain.txt` is a tab-separated table with **105 columns**, including the final `*eol` column. Append these three logical rows. Empty means an empty field, not `0`, `""`, or whitespace.

### Row 1: unique disenchanting

| Column | Exact value |
|---|---|
| `description` | `unique item + key -> eternal coin` |
| `enabled` | `1` |
| `version` | `100` |
| `numinputs` | `2` |
| `input 1` | `any,uni` |
| `input 2` | `key,qty=1` |
| `output` | `ncoi,qty=1` |
| `*eol` | `0` |
| every other column | empty |

### Row 2: set disenchanting

| Column | Exact value |
|---|---|
| `description` | `set item + key -> eternal coin` |
| `enabled` | `1` |
| `version` | `100` |
| `numinputs` | `2` |
| `input 1` | `any,set` |
| `input 2` | `key,qty=1` |
| `output` | `ncoi,qty=1` |
| `*eol` | `0` |
| every other column | empty |

### Row 3: five coins to one vial

| Column | Exact value |
|---|---|
| `description` | `5 eternal coins -> vial of awakening` |
| `enabled` | `1` |
| `version` | `100` |
| `numinputs` | `1` |
| `input 1` | `ncoi,qty=5` |
| `output` | `dvia,qty=1` |
| `*eol` | `0` |
| every other column | empty |

Important details:

- `numinputs` for the exchange is **1**, not 5. It is one input specification whose quantity is five.
- Leave `ladder`, `min diff`, `op`, `param`, `value`, and `class` empty. Do not copy awakening/corruption conditions into these recipes.
- Leave `lvl`, `plvl`, and `ilvl` empty. These are ordinary fixed-item outputs, not rerolls.
- Leave every mod column and outputs B/C empty.
- Do **not** use `useitem` or `usetype` for either disenchanting recipe. Those preserve/reuse an input item; this feature must consume the item and create `ncoi`.
- Do not put `dvia` or `ncoi` in an output-mod field. They belong in `output`.
- Quotes around comma-containing cells are accepted by the existing parser but are not required in these tab-separated rows. Use the unquoted values above consistently.

## Implementation procedure

### 1. Establish a clean baseline without disturbing existing work

From `reawakening-s14/`:

```bash
git status --short
```

There may already be unrelated modified or untracked files. Do not revert, overwrite, stage, or commit them. Restrict the feature edit to `CubeMain.txt` and the documentation update.

Before editing, record the current CubeMain row count and, if using the integrity checker, its baseline output. This lets the implementer distinguish pre-existing issues from new ones.

### 2. Append rows programmatically; do not rewrite the whole table

`CubeMain.txt` is not UTF-8. Read and write it as **Windows-1252 (`cp1252`)**. It uses **CRLF** line endings. Every existing row has 105 tab-separated fields, including `*eol=0`.

Do not open and save it in a normal text editor. Do not run a CSV writer over the entire file: that can normalize quoting, line endings, or unrelated cells and create a huge risky diff. Preserve every existing byte and append only the three new CRLF-terminated lines.

The following is a reference implementation for the one-time edit. Run it from the repository root. It deliberately refuses to append if any target description already exists, preventing duplicate recipes on a second run.

```python
from pathlib import Path

path = Path("data/global/excel/CubeMain.txt")
raw = path.read_bytes()
text = raw.decode("cp1252")

if not text.endswith("\r\n"):
    raise SystemExit("Unexpected file ending; refusing to edit")
if "\n" in text.replace("\r\n", ""):
    raise SystemExit("Found bare LF line endings; refusing to edit")

lines = text[:-2].split("\r\n")
header = lines[0].split("\t")
if len(header) != 105 or header[-1] != "*eol":
    raise SystemExit(f"Unexpected CubeMain format: {len(header)} columns")

new_recipes = [
    {
        "description": "unique item + key -> eternal coin",
        "numinputs": "2",
        "input 1": "any,uni",
        "input 2": "key,qty=1",
        "output": "ncoi,qty=1",
    },
    {
        "description": "set item + key -> eternal coin",
        "numinputs": "2",
        "input 1": "any,set",
        "input 2": "key,qty=1",
        "output": "ncoi,qty=1",
    },
    {
        "description": "5 eternal coins -> vial of awakening",
        "numinputs": "1",
        "input 1": "ncoi,qty=5",
        "output": "dvia,qty=1",
    },
]

target_names = {recipe["description"] for recipe in new_recipes}
existing_names = {line.split("\t", 1)[0] for line in lines[1:]}
collisions = target_names & existing_names
if collisions:
    raise SystemExit(f"Recipes already exist; refusing duplicates: {sorted(collisions)}")

new_lines = []
for recipe in new_recipes:
    values = {name: "" for name in header}
    values.update({"enabled": "1", "version": "100", "*eol": "0"})
    values.update(recipe)
    row = [values[name] for name in header]
    if len(row) != 105:
        raise AssertionError("Generated row has the wrong width")
    new_lines.append("\t".join(row) + "\r\n")

path.write_bytes(raw + "".join(new_lines).encode("cp1252"))
```

No permanent generator script is necessary for three fixed rows. If the implementer turns this into a tool, it must retain the same format checks and duplicate protection; otherwise use it as a one-time edit and do not add scaffolding to the repository.

### 3. Perform static validation before launching the game

Parse the edited file again with `encoding="cp1252"` and `newline=""` or equivalent raw-line handling. Verify all of the following:

- The file still has a 105-column header.
- Every row, including all old rows and the three new rows, has exactly 105 fields.
- There are exactly three additional data rows.
- Each new row has `enabled=1`, `version=100`, and `*eol=0`.
- Each new row has exactly the inputs, input count, and output specified above.
- No new row has `useitem`, output mods, output B, or output C.
- The target descriptions occur once each.
- No other enabled recipe already has the same unordered input set and output as one of the new rows.
- `key`, `ncoi`, and `dvia` still resolve to definitions in `Misc.txt`.
- The file still decodes as cp1252 and uses CRLF throughout.

Review the actual diff:

```bash
git diff -- data/global/excel/CubeMain.txt
git diff --check -- data/global/excel/CubeMain.txt
```

The data diff must contain only the three appended rows. If old rows changed, quoting was normalized, or the entire file appears rewritten, stop and correct the editing method rather than accepting the diff.

The repository's general integrity checker can also be run from Git Bash in the repository root:

```bash
CHK_ROOT=data/global/excel python tools/check_integrity.py
```

This checker does not fully validate cube input/output syntax, so it does not replace the explicit checks above. If it reports existing issues, compare against the baseline; the requirement is **no new issues**, not an unrelated cleanup.

### 4. Update the recipe documentation

Add a section to `docs/ra_cube_recipes.md` containing:

- Unique-quality item + 1 key -> 1 Eternal Coin (`ncoi`).
- Set-quality item + 1 key -> 1 Eternal Coin.
- 5 Eternal Coins -> 1 Vial of Awakening (`dvia`).
- The recipes are quality-based and include RA additions, jewels, charms, quivers, maps, and special unique items.
- Disenchanting destroys the item and any socket contents.

Do not claim that in-game verification has passed until the tests below have actually been performed.

### 5. Deploy and force CubeMain recompilation

Follow the repository's `-txt` workflow in `README-S14-PORT.md`. For this isolated change:

1. Copy the edited `data/global/excel/CubeMain.txt` over `ProjectD2/data/global/excel/CubeMain.txt`.
2. Delete the generated `ProjectD2/data/global/excel/CubeMain.bin` so the game must rebuild it from the edited text.
3. Launch `ProjectD2/PlugY.exe` directly and enter a disposable test game.
4. Confirm that a new `CubeMain.bin` is generated and the game reaches the world without a table-compilation crash.

Do not click Play in the RA launcher and do not run an official launcher repair; those can replace the S14 port with other data. Do not assume the feature works merely because the repository text file changed—the installed data and regenerated bin are what the game reads.

## In-game acceptance tests

Use a disposable character and disposable items. Do not test destructive recipes on valuable equipment or the user's normal save. If the implementer cannot obtain suitable test items safely, report that limitation rather than claiming end-to-end success.

### A. Basic disenchanting

1. Put one ordinary unique weapon and exactly one key in the cube.
2. Transmute.
3. Confirm the weapon and key are both gone and exactly one Eternal Coin appears.
4. Repeat with one set armor piece and one key; confirm exactly one coin.
5. Confirm there are no extra outputs and no random outcomes.

### B. Required category coverage

Test at least one of each, always with one key:

- Unique ring.
- Unique amulet.
- Unique jewel, such as an enabled Rainbow Facet variant.
- Unique small charm, such as Annihilus.
- Unique large charm, such as Hellfire Torch.
- Unique grand charm, such as Gheed's Fortune.
- Unique quiver/arrows/bolts.
- One RA-added unique jewel or charm, such as Ember of Eternity or Light's Hope.
- One RA replica/legacy equipment item.
- One set ring or amulet, not only set armor/weapons.

Every case must produce one `ncoi` and consume exactly one key. These tests specifically guard against accidentally choosing a narrow item type such as `weap` or `armo` instead of `any`.

### C. Broad-scope behavior

Because this plan intentionally uses `any,uni`, test one unique map with a key and confirm it also disenchants. If a unique trophy/special charm is safely available on the disposable setup, test that too. Do not change the recipe just because these match; they are within the stated every-unique scope.

### D. Negative tests

Confirm that each of these does **not** disenchant and does not consume the key:

- Normal item + key.
- Magic item + key.
- Rare item + key.
- Crafted item + key.
- Unique item without a key.
- Set item without a key.
- Eternal Coin + key.

A normal/magic/rare version of a base that has a unique variant must still fail. This verifies that quality, not base-code membership, controls the recipe.

### E. Modified-item and socket behavior

On a disposable socketed unique containing a cheap gem/jewel:

1. Add one key and transmute.
2. Confirm the unique and key are consumed and one coin is produced.
3. Confirm the socket contents are not returned as separate items.

Also test one corrupted or awakened unique if available. Its extra properties must not prevent disenchanting or change the one-coin output.

### F. Exact coin quantity

1. Put four separate Eternal Coins in the cube and transmute. Nothing should be consumed and no vial should appear.
2. Put exactly five coins in the cube and transmute. All five must be consumed and exactly one Vial of Awakening must appear.
3. Put six coins in the cube and transmute. Exactly one vial must appear and exactly one coin must remain.
4. Add a key to five coins and confirm the key is not part of this exchange; remove it before performing the normal exchange test if the extra input prevents matching.

The four- and six-coin cases are essential: a successful five-coin test alone does not prove that the quantity condition and consumption are correct.

### G. Regression checks

Confirm these existing behaviors still work:

- A unique item + Vial of Awakening still uses the awakening recipe when no key is present.
- A supported unique/set item + Divine Orb still rerolls when no key is present.
- An existing rune downgrade using a key still produces the expected lower rune.
- The existing Vex + jewel fragments + coin recipe is unchanged.

Save, leave, and re-enter the disposable game after producing a coin and a vial. Confirm both output items persist normally.

## Common failure modes and how to avoid them

| Mistake | Consequence | Prevention |
|---|---|---|
| Generating one row per unique/set definition | Hundreds of needless rows; missed future/RA items; duplicate base-code bugs | Use only `any,uni` and `any,set` |
| Using `misc,uni` to cover everything | Weapons and armor are excluded | Use `any`, then test every required category |
| Omitting `uni`/`set` | Normal/magic/rare items can be destroyed for coins | Keep the quality token in both inputs |
| Using `jewl` assumptions or separate charm subtype recipes unnecessarily | Category gaps and inconsistent aliases | Use `any,uni`; no jewel/charm-specific rows are needed |
| Setting exchange `numinputs=5` | Recipe does not represent one `ncoi,qty=5` input correctly | Set `numinputs=1` |
| Writing five separate coin input columns | Unnecessary and may exceed intended matching behavior | Use one input with `qty=5` |
| Using `useitem` for disenchanting | Keeps/reuses the input instead of producing the intended fixed currency | Output `ncoi,qty=1` directly |
| Copying `op`, `param`, `value`, or `ladder` from awakening recipes | Adds unwanted seasonal/stat conditions | Leave all condition fields empty |
| Forgetting `*eol=0` or a trailing empty field | Malformed row/table compilation problems | Generate from the 105-column header and validate every row |
| Saving as UTF-8 or LF-only | Encoding/parser failures or unrelated byte changes | Preserve cp1252 and CRLF; append bytes only |
| Editing only the installed copy or only the repo copy | Source and runtime diverge | Edit repo source, then deploy that exact file |
| Leaving the old `CubeMain.bin` in place | Game may continue using old recipes | Delete the installed bin and verify regeneration |
| Launching through the RA launcher | S11 manifest may replace the port's files | Launch `ProjectD2/PlugY.exe` directly |
| Ignoring maps/trophies in the design review | Surprising destruction of special unique items | Treat them as explicitly included by the every-unique scope |
| Testing only five coins | Incorrect quantity consumption can go unnoticed | Test four, five, and six coins |
| Testing on valuable real items | Irreversible loss of equipment/socket contents | Use a disposable character and items only |

## Completion criteria

The feature is complete only when:

1. The source `CubeMain.txt` contains exactly the three specified recipes and no unrelated data changes.
2. All rows retain the 105-column cp1252/CRLF format.
3. Static duplicate/reference checks pass with no new integrity errors.
4. The recipe documentation reflects actual behavior.
5. The edited file is deployed and the installed `CubeMain.bin` is regenerated successfully.
6. The in-game tests confirm unique/set destruction, key consumption, RA/jewel/charm coverage, exact five-coin exchange behavior, negative cases, and the listed regression cases.

Do not add future currency rewards, tiered coin yields, loot-filter changes, or additional exchanges in this implementation. Those are separate balance/features decisions after this minimal version works end to end.
