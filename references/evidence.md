# Evidence: games the skill has been run on

One entry per game. The rest of the skill states rules without naming games; what each game
showed, and what changed in the skill because of it, lives here. A lesson that comes back on
several games belongs in the rules; one that stays with a single game is that game's quirk.

The procedure in `SKILL.md` is general, but the *patterns* are a growing list, and the only way
the list grows is if each new game's surprises get written down. Most valuable of all is a game
that **contradicts** an earlier one: the second game here disagreed with the first about text
encoding, entropy meaning, checksums and cross-version diffing, and each disagreement turned a
rule into a game-dependent check. Record disagreements first.

## Entry format

When you finish a game, add an entry with:

* what the engine's dispatch idioms turned out to be, and whether they were already in
  `idioms.md`
* how text was encoded, and anything `text.md` did not predict
* what cost you the most time, and what would have found it sooner
* which of this skill's claims turned out to be wrong for this game
* the progress report's numbers at the end (step 13), main metric first
* a closing `What changed in the skill` list, one line per lesson:
  `what broke or surprised -> what changed`, naming the step or rule it went into. A later
  pass on the same game appends its own section and list.

Then fold the general parts into the other references, and add any new dispatch idiom to
`scripts/trace.py`.

## Games

### Game 1: 2 MiB fighting game, 1994 (the reference game)

The game this skill was extracted from. Disassembled from nothing in a day,
with three regional/translated builds and six third-party patches available.

#### Numbers

| | |
|---|---|
| ROM | 2 MiB |
| vector-table trace alone | 0.2% of ROM |
| after resolving the dispatch idioms | ~5%, about 106 KiB |
| what the other 95% was | asset payload, entropy 6.5 to 7.2 |
| unresolved indirect sites at the end | 5 |

5% sounded like failure and was not: the entropy map showed the rest was art
and audio. Coverage percentage is a bad target; the unresolved-site count is
the useful one.

#### Engine shape

* Boot at the reset vector, checksum over `$000200` to the ROM end compared
  against a header field, hanging on mismatch.
* A main loop reading a mode variable and dispatching through a `bra.w` slot
  table.
* Everything below that dispatched through **self-relative word tables**, in
  both code and data. This one idiom was the difference between 0.2% and 5%.
* Data addressed exactly like code, so "what points here" is a scan for
  self-relative words.

#### Text

Raw VDP tilemap words, `$FFFF` terminated, fixed-width pre-padded fields. Split
alphabet ranges, proportional glyphs with continuation tiles, separate case
blocks, and attribute bits that differed between the Japanese and European
builds of the same game.

Solved from two language versions of the same lines. Punctuation identified
afterwards from context, by frequency, inside runs of known letters.

A second, parallel set of the same names existed as **pixel art** for the HUD
and the character grid, while the tables held real text. Both were live at
once. Do not assume one representation.

#### What the third-party patches gave up

Without reading any code: the palette tables, the sprite art region, the frame
and hitbox tables, the sound driver and PCM, and the character-select screen's
code. Also that ROM expansion past 2 MiB is viable for this platform, visible
in one patch's write offsets.

#### Biggest time sinks

1. Inferring hardware facts from code instead of measuring them. Three separate
   wrong answers, each corrected by one runtime measurement.
2. Assuming a constant appeared once. It appeared in seven places.
3. Patching the address a disassembler printed rather than where the immediate
   byte sits.
4. Trusting an incomplete font map, which turned three missing glyphs into 46
   false findings about the data.

#### Art pass (later, Japanese ROM)

Art was mapped in a second session, to lift sprites into another game.

* **Compression**: a custom LZSS, not Nemesis (an early false lead). A size
  word's top bit picks byte or word mode.
* **Fighter art**: a two-level table of per-frame LZSS streams. The sprite-piece
  table is a list of words that are self-relative **to the entry**, not to the
  table base. Its pieces are 6 bytes: a tile word with flip bits, signed X and Y
  from the feet, and a size byte. Trusted only once each frame's piece tile
  counts summed to its art size.
* **Portraits**: select-screen portraits are 80-tile streams, 10x8 row-major,
  from their own table next to the loader's palette table. The big story
  portraits are nametable-placed and look scrambled without their map.
* **Items**: none. A whole-ROM sweep found fighters, portraits, story art, stage
  backgrounds and hit effects; a fighting game has no pickups.

What cost time: decoding addresses from the European listing against the
Japanese ROM, a facts label that named an animation script as art, and a
whole-ROM sweep that should have started from the decompressor's callers.

#### Animation pass (later, same ROM)

Frames were picked for specific moves (punches, kicks, ground and air) to port
into another game. The animation scripts are still not located.

* **Frames identified by eye, from one contact sheet**: every frame of one
  fighter rendered side by side with its index and tile count. Index order is
  grouped by move class (stance and walk, crouch, jumps, air attacks, punches,
  kicks, crouch attacks), so one sheet named every move needed. This is a
  reading, not a fact from the animation table.
* **The frame table bounds itself**: its length is not stored, and the first
  index where the piece tile counts stop summing to the art size is the end
  (49 frames for the first fighter).
* **The origin is the fighter's position, not the body's centre**: a lunging
  kick draws the body about 24px ahead of it, and two frames looked empty
  because they fell outside a canvas sized for the standing frame.

#### Where this game's map lives

This game's facts module and text codec live with its own repository; the skill's
`references/example-facts.py` shows the shape only, with made-up values.

#### Roster and power-up pass (later, same ROM)

* **The roster names the fighter index**: the select screen's name list is in
  the same order as the art, sprite-piece and palette tables, so one list in the
  facts module names every per-fighter table. Confirmed by extracting each
  fighter's frames, not by the list's order alone.
* **The power-up aura**: its tiles are part of the fight art (loaded to a fixed
  VRAM tile base), and its one sprite frame is stored **twice**, at two
  unrelated addresses.
* **Poses matched against recordings**: the main fighter's frames named by
  matching gameplay recordings frame by frame (a flight, a fight, half an hour
  of story mode), since the animation scripts are still not located.

#### What changed in the skill

* a frame stored twice -> the rule "A constant appears in more than one place"
* the progress report put the map first, and a mapped share is not completion
  -> step 12: equivalent source is the main metric

#### Sound driver pass (later, same ROM)

The 68000 routine that copies a program to Z80 RAM states the program's length in its loop count;
a block of exactly that size sits where the source address points (8008 bytes both). That is exact
evidence for a Z80 driver, tagged `recognised_z80` (known program, not yet source). The 200 KB
after the sound code is eight 32 KB-aligned banks that no 68000 routine points at, which is the
shape of banks the Z80 reads through its window; unconfirmed without reading the Z80 code.

Negative: the game's own LZSS decoder accepts almost any bytes (it "decodes" blocks as 7-byte
streams), so a clean decode is not evidence of the format; format evidence has to come from code
that loads the block.

* a decoder that never rejects is not a detector -> format comes from the loading routine, not from a scan

### Game 2: 4 MiB licensed platformer, 1995/96

Mapped by a different agent session from `SKILL.md` alone. Its own full write-up
lives with that project; this entry records what it changed in the skill.

Value of this game to the skill: it **disagreed with the first one** on almost
every specific while confirming the procedure.

#### What it contradicted

| | game 1 | game 2 |
|---|---|---|
| text encoding | custom tilemap glyphs, split alphabet, proportional | plain uppercase 7-bit ASCII, no glyph table |
| mid-entropy regions | mostly code | 45% of ROM at H 3-5, almost no code: level and tilemap data |
| boot checksum | verified, hangs on mismatch | not verified at runtime; a released patch leaves it stale |
| cross-version diff | located the whole script | useless, the two releases are separate compiles |
| coverage when done | ~5% | 3.26% |

Every one of those was stated as general in the skill after one game. All are
now marked as game-dependent, with both observations given.

#### What it added

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

#### Process failures worth keeping

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

#### Art pass (later, same ROM)

Art was lifted into another game: one character's sprite frames, with their palette.

* **Compression**: RNC ProPack, methods 1 and 2. Its header carries a CRC of the
  packed and the unpacked data, so a sweep for the magic needs no judgement:
  264 blocks, every one CRC-clean, about 3.3 MB unpacked.
* **Frames**: a header whose first word is `6 + 6 * count`, then `count`, then
  6-byte pieces, tiles column-major in each piece. The header's arithmetic is
  the sweep signature (step 10).
* **Two encodings**: the player's frames run-length code their tiles; every
  other object's frames store raw tiles.
* **A fourth pointer origin**: the player's frame table measures each pointer
  from the start of the frame bank, and the top byte of each long is a separate
  field (a literal offset, halved). Every player frame decoded as bad until the
  offsets were read as bank-relative.
* **The frame sweep**: 1,406 object frames in 89 runs, after dropping overlaps
  with RNC blocks and every single-piece candidate. A random sample of 48,
  rendered, was 48 real sprites. Mapped share: 35.8% to 79.2%.

#### What changed in the skill

* a self-checking format (RNC's CRCs) ends a sweep's guesswork -> step 10
* frame headers that state their own length are a sweep signature, with the
  overlap, single-piece and sampling filters -> step 10
* bank-relative offsets with a reused top byte -> steps 3 and 10
* the map jumped 43 points while the code stayed 99.6% unnamed: mapped is not
  done -> the main metric is equivalent source (step 12), and the rule
  "Mapped is not done"
* its frames mix a mapping header with their tiles, so under the leaf rule the
  frame blocks counted for nothing (12.3% to 0.0%); a game-specific tool split
  each of 472 frames into header and tiles, checking each one, and wrote the
  list for the facts module: the tiles count, 0.0% to 11.6% -> step 12, the
  split and generated-list paragraphs

#### Recognised row pass (later, same ROM)

All 264 RNC blocks decode with a matching checksum, yet counted for nothing in the main figure.
Tagging them `recognised_rnc` and naming them `rnc_<address>` left the main figure alone and gave
a row of its own (1,330,891 bytes, 31.7% of the ROM). Naming them made 28 routines show which
block they load; one block was loaded by 7 of them, always to the same VRAM slot. Decoding and
rendering that block (172 tiles of letter and digit shapes) identified it, and it moved to a leaf
format with a real name: 24.6% to 24.7%. The method-1 unpacker (79 callers) and a timed-screen routine
were named from the same list.

Negative: matching routine skeletons (the instruction mnemonics from entry to the first return) of
this game against two Sonic engines found nothing (0 of 328 routines of at least 8 instructions),
although the same matcher found 13 shared routines between the two Sonic games. Matching only
helps against code from the same engine family.

* a decoded-but-unidentified block counted for nothing and hid the next step -> `recognised_<format>`
  blocks, their own progress row, step 12
* a block loaded from many routines is the one to identify first -> the bullet on recognised blocks

### Game 3: 1 MiB racing game, 1991

Mapped for a graphics mod: find the player car's driver and passenger sprites and
the roadside ground colours. Text and sound were not examined.

#### What it contradicted

| | games 1 and 2 | game 3 |
|---|---|---|
| dispatch idioms | three each, the highest-leverage step | none needed: 3.63% coverage, 0 unresolved sites on the first trace |
| how assets are found | decompressor callers, level tables | one resource directory: `[id.w][pointer.l][size.w]`, 221 entries, one lookup routine |
| self-relative origin | the entry, or the table base | a sprite frame's tile offset counts from the frame's own header |

#### What it added

* **Resource directory.** Reached from a CRAM write: the palette DMA copies a RAM
  buffer, the buffer is filled from a table built at boot, and the table's
  builder passes ID words to the lookup routine. Every asset is labelled at once.
* **Short absolute addresses are RAM.** `lea $B600.w` and `lea $DE00.w` were read
  as ROM first and rendered garbage. They are RAM tables at `$FFB600`/`$FFDE00`.
* **Two sprite formats, both confirmed by sizes.** One stores
  `[tile offset][tile count]` then raw tiles, and offset + count x 32 equals the
  resource size for every entry. The other stores per-frame tiles, and each
  frame's tiles end where the next frame's begin. Piece size byte is
  `(w-1)<<2 | (h-1)` with tiles column-major inside the piece; one format marks
  the last piece with `$FF` in the size word's low byte.
* **Data duplicated by context.** The first stage's palette exists twice (race
  start, stage table). Patching only one changed the colours a few seconds late.
* **Directly written palette slots.** The brake lights write one colour of the
  car's palette line straight to CRAM each frame. Art painted in that slot lit up
  on braking.
* **Art from a Game Gear ROM.** The borrowed character art was uncompressed 4bpp
  planar tiles, found by matching operator screenshots tile by tile, which also
  recovered the palette.

#### What cost the most time

* Treating sign-extended `.w` addresses as ROM.
* Assuming a screenshot showed the full screen. It was a crop at 12 pixels per
  console pixel; measuring the run lengths first would have matched on the first
  try.
* Scanning for palette-shaped data instead of following the CRAM write back.
