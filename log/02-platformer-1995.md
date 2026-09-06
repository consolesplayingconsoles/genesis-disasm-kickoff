# Second game: 4 MiB licensed platformer, 1995/96

Mapped by a different agent session from `SKILL.md` alone. Its own full write-up
lives with that project; this entry records what it changed in the skill.

Value of this game to the skill: it **disagreed with the first one** on almost
every specific while confirming the procedure.

## What it contradicted

| | game 1 | game 2 |
|---|---|---|
| text encoding | custom tilemap glyphs, split alphabet, proportional | plain uppercase 7-bit ASCII, no glyph table |
| mid-entropy regions | mostly code | 45% of ROM at H 3-5, almost no code: level and tilemap data |
| boot checksum | verified, hangs on mismatch | not verified at runtime; a released patch leaves it stale |
| cross-version diff | located the whole script | useless, the two releases are separate compiles |
| coverage when done | ~5% | 3.26% |

Every one of those was stated as general in the skill after one game. All are
now marked as game-dependent, with both observations given.

## What it added

* **Computed jump into unrolled code**, which mimics a trampoline table at the
  call site and produces garbage if read as one. Distinguishing test added to
  `references/idioms.md`.
* **Self-relative word tables have two origins**: the entry's own address in
  game 1, the table's base address in game 2. The origin must be read from the
  instruction that does the addition.
* **Bounding a table by the index masks** (`andi.w #mask,dn`) rather than
  scanning entries, which is the only sound method when the index is built from
  two fields.
* **A legitimate stopping point**: `jsr (an)` where the register comes from an
  object field at runtime is a per-instance behaviour pointer and is not
  statically resolvable. That was the entire remaining unresolved set here.
* **Fan patches as the text oracle** when versions have diverged too far to
  diff: two independent translations landing on the same span confirmed the
  script region.

## Process failures worth keeping

* Two supplied files were not what their names claimed: a `.zip` named for this
  game held a Game Boy ROM, and an `.ips` was a saved HTML page of a GitHub
  blob view. The first was reported and the operator supplied a correct file
  within the session. **The second was silently written off**, costing a third
  translation, which is the input the text step benefits from most. The skill
  now requires reporting every bad input and asking for a replacement even when
  the work can continue without it.
* The skill was delivered as `SKILL.md` only, with no `scripts/` or
  `references/`. The tooling was successfully rebuilt from the procedure text,
  which is a good sign for the procedure, but the idiom catalogue was lost and
  all three dispatch shapes were rediscovered from scratch. The essentials are
  now repeated inline in `SKILL.md`, and the skill should be packaged as an
  archive so the directories travel.
