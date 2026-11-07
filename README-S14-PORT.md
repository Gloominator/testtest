# Reawakening — PD2 Season 14 port (skills, TC drop boosts, and content)

An AI-assisted port of [pd2-reawakening](https://github.com/synpoox/pd2-reawakening) (built for PD2 S11)
onto the PD2 Season 14 "Alliance" data. The game boots, characters enter the world, and the mod's
content (awakened items, replica/legacy items, fate cards, orbs, boosted rune/gem drops) is in place.

This document is written for the mod's original author (and anyone else who wants to polish it).

## How the port was done

The approach is a **data merge**, not a file swap: PD2 S14's data is the base (so all S12–S14
balance/content is preserved byte-for-byte), and Reawakening's additions are layered on top.

Sources:
- S14 vanilla data: extracted from `ProjectD2/Live/pd2data.mpq` (pristine S14 install)
- Mod S11 data: extracted from the installed modded `pd2data.mpq` (v11.0.1)

Merge rules (tools in `tools/`):
1. **S14 is the base; intentional Reawakening edits are replayed** — `tools/port_reawakening_skills.py`
   derives edited cells from Reawakening's Git history and applies their final S11 values to shared
   skill, descriptor, missile, summon, MonProp, and PetType rows. Untouched S14 cells stay verbatim.
2. **Mod-only rows are appended**, with values remapped by *name* where they reference skills
   (skill IDs shifted between S11 and S14; 36 params remapped, 0 misses).
3. **ItemStatCost** (the table you warned about): both files sit at the 511-row cap. The 41 mod-only
   stats were placed into 41 *dead/unreferenced* S14 rows (full mapping in `docs/itemstatcost_mapping.md`).
   Every live S14 row keeps its exact position, so S14 items/characters are unaffected. Mod stat IDs
   changed as little as possible — but they DID change, so **old mod items are not compatible**
   (fresh characters required; S12+ save-format changes broke old saves anyway).
4. **patchstring.tbl**: format fully reverse-engineered (ELF-hash linear probing, NumLoops =
   max probe distance + 1, CRC16-CCITT over the string pool). S14 entries keep their original idx
   values; 453 mod-only keys appended. The 61 skill/summon/mastery/PvP conflicts needed by
   Reawakening use the mod values; unrelated conflicts stay S14 (see `docs/patchstring_merge.md`).
5. 26 mod-only .dc6 item graphics copied verbatim.

## Bugs found & fixed (this is the hard-won knowledge)

1. **Experience.txt is positional.** The MaxLvl row must be the FIRST data row; a name-keyed merge
   put it last and the engine parsed level 0's row as the cap → crash on game creation.
   Fix: mod's file verbatim (MaxLvl=131, flat 100–131 curve).
2. **CRLF required.** D2's txt parser chokes on LF-only files. (This is why editing tables in a
   plain text editor bricks the game — editors also love stripping trailing tabs. All merging here
   is byte-exact programmatic.)
3. **Skills.txt / Missiles.txt: `Id` column must equal row index.** Appended mod rows kept their
   S11 Ids, colliding with S14 rows (e.g. Id 487: `NihlathakMapDeath` vs `Sentry Lightning Fury`).
   The engine builds Id-indexed arrays → duplicate Ids crash table compilation on game creation.
   Fixed: Id = row index for appended rows.
4. **Skilldesc.txt rows must be padded to the header width** (118 cols).

## Deliberately NOT ported yet (Stage 2)

See `docs/stage2_deferred.md` for the full list with recovery methods. Headlines:

- **Drop-rate boosts**: ✅ DONE — see `docs/tc_boosts.md`. Runes cascade probs, Good-TC
  gem/orb/fate-card injection, junk halving, Treasure Fallen, BR Arena + utility quality
  scalars are all ported (84 TC rows). Skipped per scope decision: boss/uber TC rows
  (including the mod's 10× key-drop boost and `bet`/`fed`→`dcso` material swap) and the
  outdated S11 map-tier pools — all recoverable if wanted.
- **Skill design and mastery rework**: ✅ DONE — intentional shared-row edits, custom item-stat
  formulas, summon behavior, projectiles, descriptors, and both Barbarian mastery replacements are
  active. Every class remains at 36 skills to avoid the earlier save-alignment corruption.
- **Density variants** (1x/2x/5x/10x): S14 base density currently; variants should be regenerated
  from S14 values using the per-row multipliers in your variant mpqs.
- 332 CubeMain label collisions kept as S14 (`docs/cubemain_conflicts.md`).

## Current install layout

```
C:\Diablo II - Lord of Destruction\
├─ reawakening-s14\        ← THIS REPO (merged data tree + tools + docs + S14 BH)
├─ ProjectD2\
│  ├─ data\                ← merged data on disk (the game reads this)
│  ├─ PlugY.ini            ← Param=-3dfx -plugy -direct -txt
│  ├─ BH.dll               ← S14 BH (copied from this repo's bin/BH.dll)
│  ├─ loot.filter          ← local Hiim Mystery filter + Reawakening rules (not tracked)
│  ├─ pd2data.mpq          ← vanilla S14 (fallback only; disk data wins)
│  └─ *.backup / *.before-s14mod-* ← originals
└─ scout\                  ← tooling workspace (mpq extractor, both extracted datasets,
                             clones of pd2-reawakening, BH source, ra-launcher)
```

Launch with `ProjectD2\PlugY.exe` directly. **Do not** click Play in the ra-launcher (it
re-downloads the S11 files per its manifest), and don't let the official PD2Launcher "repair".

### BH and loot filter

`bin/BH.dll` is built from native S14 BH source at upstream commit `66acd03d`, with Reawakening's
orange awakening markers and its property hooks restored so native red corruption markers also run.
It retains S14's formulas, sound effects, quiver conditions, and other filter features missing from
Reawakening's S11 BH. The pristine native DLL remains in `ProjectD2/Live/BH.dll`; the DLL replaced by
this custom build is preserved as `ProjectD2/BH.dll.before-ra-affix-markers`. The older RA DLL is
preserved as `ProjectD2/BH.dll.before-s14bh-upgrade`. Modified BH is for single-player only.

S14 BH does not implement Reawakening's custom `CARD` keyword. The installed filter therefore uses
an `RA_CARDS` alias listing all 60 fate-card item codes. Launcher filter selection is cleared so BH
loads `ProjectD2/loot.filter`; the filter itself is deliberately not tracked in this repository.

### Editing workflow

1. Edit txt files in `reawakening-s14\data\` (programmatically or with a D2-safe editor only).
2. Copy `data\` over `ProjectD2\data\`, delete `ProjectD2\data\global\excel\*.bin`.
3. Launch once — the game recompiles all bins from txt. A crash during this writes bins up to the
   failing table, which pinpoints the culprit.
4. Commit in git after every working change (`.gitattributes` forces byte-exact storage;
   never let git's autocrlf touch these files).

## Known open items

- **MPQ packaging**: a minimal MPQ writer was built (`tools/mpq_write.py`, read-back verified)
  but Storm.dll rejects the result ("file data is corrupt"). Currently unnecessary (txt mode),
  but packaging would restore the original distribution format + faster boot.
- GitHub mirror of this repo is pending (local-only for now).

## For the author

Everything above is reproducible from the scripts in `tools/` and the docs in `docs/`.
Run `python ../reawakening-s14/tools/port_reawakening_skills.py --check` from `scout/` to verify
the skill port. Review `docs/stage2_deferred.md` for the remaining non-skill work.
