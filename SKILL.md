---
name: smd-disassembly
description: Disassemble and map an unknown Sega Mega Drive or Genesis ROM. Use when someone has a Mega Drive ROM and wants to know what is inside it, where the code is, how the engine dispatches, and where the tables, text and art live. Analysis only, not modding.
---

# Disassembling an unknown Mega Drive ROM

The goal is a map: which bytes are code, how the engine dispatches, which
tables are indexed by what, how text is encoded, and where the art lives.
Producing a patched ROM is a different job and is out of scope here.

## Read this first: how complete this skill is

**Evidence base: three games**, by different developers. A 1994 fighting game,
a 1995 licensed platformer and a 1991 racing game. Each was mapped from nothing
in a day, and each contradicted something the earlier ones taught:

| | game 1 | game 2 | game 3 |
|---|---|---|---|
| coverage after resolving idioms | ~5% | 3.26% | 3.63% |
| dispatch idioms | 3, all self-relative word tables | 3, only one of which overlapped | none needed: 0 unresolved on the first trace |
| text | custom tilemap glyphs, split alphabet | plain uppercase ASCII | not examined |
| mid-entropy regions | mostly code | mostly uncompressed level data | not examined |
| boot checksum | verified, hangs on mismatch | not verified at runtime | valid; not tested |
| how assets are found | decompressor call sites | level tables | a resource directory of id, pointer, size |

Take that table as the real lesson: **the procedure generalised, the specifics
did not.** Treat every byte pattern here as an example of a shape to look for,
never as a catalogue to match against. Expect a third game to break something
else.

When the ROM does something this skill does not describe, that is the expected
case, not a failure. Write it down in `log/` and fold the general part back
into `references/`.

## If the scripts are missing

This skill is sometimes delivered as `SKILL.md` alone, without `scripts/`,
`references/` or `log/`. That has already happened once in the field.

If `scripts/` is not present: **rebuild what you need from the procedure
below.** A tracer, an entropy mapper, a self-relative-word xref and an IPS
reader are each a short Python file against `capstone`'s M68K backend, and an
agent has already done exactly that successfully from this text alone. Say so
in your writeup, and hand the rebuilt tools back to the operator.

The most costly thing lost in that case is the accumulated idiom catalogue, so
the essentials are repeated inline in step 3 below.

## Ask the operator for more input, before starting

One ROM is the worst case, not the normal case. Ask for these every time, and
say why, because the operator usually can get them in minutes and does not know
how much they are worth:

1. **Every other release of the game.** Other regions, other languages, later
   revisions. A second language is the single most valuable thing you can be
   given: diffing two releases locates the entire script without reading any
   code, and it is how the text encoding gets solved at all.
2. **Every existing patch or hack**, in any format, including ones that look
   irrelevant. A patch's offsets label whatever it changes, so a colour hack
   hands you the palettes and a sprite patch hands you the art, for free.
3. Nothing else. Do not ask questions the ROM itself can answer.

**If any supplied file is not what it claims to be, stop and say so.** Check
every input before using it: size, header, magic bytes. A `.zip` named for a
Mega Drive game has turned out to hold a Game Boy ROM, and an `.ips` has turned
out to be a saved HTML page of a GitHub blob view rather than the patch itself.

Report a bad file and ask for a replacement **even when you can work without
it**. The operator can usually re-fetch it in seconds, and the input you are
quietly writing off is worth more than the time it costs to ask. In the field,
an agent asked about one bad file, got a corrected one, and silently dropped a
second bad file: the dropped one was a third translation, which is exactly the
input the text step is starved of.

Recommend this explicitly rather than proceeding quietly with one file. If the
operator only has one ROM, say what that costs before starting: the text
encoding has to be solved the hard way, the script map is guesswork, and whole
regions stay unlabelled that a single extra file would have named. Then start
anyway, and ask again if a later step stalls on exactly that gap.

## Procedure

### 1. Identity

Read the header: console name, region, ROM end pointer, checksum field. Hash
every ROM supplied so builds and findings can be tied to a specific file.

### 2. First trace

`scripts/trace.py <rom> <out.json>`

Recursive descent from the 68000 vector table. Expect very low coverage on the
first pass: on the reference game it reached **0.2%**. That is normal and not a
sign the tracer is broken.

The number that matters is not the percentage, it is the list of unresolved
indirect call sites the tracer prints.

The output JSON holds the instruction starts, a label per branch target (with
its kind: subroutine, local branch, table), the untraced gaps, the tables it
resolved and every data reference with the instructions that make it. Keep it:
the listing (step 11) and the progress report (step 12) are built from it.

### 3. Identify the dispatch idiom, then re-trace

Read those unresolved sites. There will be a small number of recurring shapes.
Teach the tracer each one and re-run until the unresolved count stops falling.
This is the highest-leverage step in the whole procedure: on the reference game
it took coverage from 0.2% to essentially all the code.

### The shapes seen so far

Repeated here because this is the knowledge most worth carrying, and the
expanded version in `references/idioms.md` does not always travel with the
skill.

**A. Trampoline table.** `jmp table(pc,d0.w)` where each 4-byte entry is a
literal `bra.w` (`$6000` + displacement), not an address. Resolve as
`entry + 2 + sign16(disp)`. Length is not stored: read forward while the word
at the 4-byte stride is still `$6000`. Also appears as
`lea table.w,a1 ; jsr (a1,d4.w)`, same table, different call site.

**B. Computed jump into unrolled code.** Identical at the call site, but the
target is *not* a table: it is a block-copy or fill loop written out N times,
and jumping partway in skips the first k iterations. Tell the two apart by
testing whether the first word is `$6000`. If it is not, it is ordinary code:
let linear decode continue through it and do not try to read entries.

**C. Word-relative switch table.** `lea table,a0 ; adda.w (a0,dn.w),a0 ; jmp
(a0)`. Entries are signed words, but relative to **the table's own base**, not
to the entry that holds them.

Note that both games used self-relative words and disagreed about the origin:
one measured from the entry, the other from the table base. A third measured a
sprite frame's tile offset from that frame's own header. Determine which from
the code that does the addition, never by assuming.

**Bounding a table's length.** Rarely stored. Ways that work: read entries
while they still match the idiom's own signature, or recover the index range
from the `andi.w #mask,dn` instructions that built the index, OR the masks
together and divide by the entry stride. The second is better where an index is
built from two fields, such as a state in the high bits and an event in the
low bits.

**Never take the first bad entry as the end.** Tables have empty slots in the
middle. A fighter's frame table in game 1 had placeholder entries at 49, 50,
54 to 57 and 81, and ran to 86: stopping at the first entry that failed an
independent check (step 10: piece tile counts against art size) cut it at 49.
Use such a check to judge each entry, and bound the table by the index range
the code can produce, or by the next table's start.

**When to stop.** Some sites are genuinely not statically resolvable:
`jsr (an)` where the register comes from an object field at runtime is a
per-instance behaviour pointer. Log the shape and move on. In the second game
that was the entire remaining unresolved set, and it is a legitimate stopping
point rather than a failure.

### 4. Decide when to stop chasing coverage

`scripts/mapdump.py <rom>` gives per-block entropy. High entropy regions are
art or audio, not code you failed to find.

What the middle of the range means is **game-dependent**, so read it against
your own trace rather than against a rule of thumb. In game 1, mid-entropy was
mostly code. In game 2, 45% of the ROM sat at entropy 3 to 5 with almost no
code in it: uncompressed level, tilemap and object-placement data plus the
script blob. Assuming mid-entropy meant code there would have sent you hunting
for a fourth idiom that does not exist.

Coverage percentages are not comparable between games and are not a target.
The two games here settled at ~5% and 3.26%, both essentially complete for
their engines. The number that means something is how many unresolved indirect
sites remain, and whether the remaining ones are genuinely runtime-dependent.

### 5. Seed by hand, and iterate

Coverage is not one-shot. Whenever you identify a screen handler, a mode table
or a step table, pass its entry points to the tracer as extra seeds and re-run:

`scripts/trace.py <rom> <out.json> 3CE12 3CF32 3D00A`

On the reference game, the routine handling the main menu cursor was invisible
until its step table was seeded by hand, several hours in.

### 6. Diff the versions

**First, measure how far apart the releases actually are.** Diff them and look
at the fraction of the ROM that differs before planning anything around it.

* A few percent: a revision. Offsets mostly transfer, and the diff is a precise
  map of what changed.
* Nearly everything, as in 98%: a genuine second compile, not a patch. In game
  2 the European build differed from the American one across 98% of the ROM,
  four months apart, with a different frame rate and an added password system.
  Nothing transfers between such builds, and cross-version diffing tells you
  nothing about where the text is.

When the releases have diverged that far, **fan translation patches become the
text oracle instead**, because each one is a diff against a single base. Two
independent translations landing on the same span is strong evidence, and that
is how game 2's script region was located after the version diff failed.

If more than one release is available:

* Same-language releases differ by revision; the diff tells you which offsets
  transfer between them.
* Different-language releases: **the diff regions are the text.** On the
  reference game, French versus English was 43 KiB across 40 tight regions,
  and that diff was the entire script map.
* Classify each diff region by whether it decodes as glyphs. Where it does, it
  is text. Where it does not, the translator redrew art, which tells you where
  the art for that screen lives.

### 7. Read the third-party patches

`scripts/ips.py <patch.ips>` summarises which regions a patch writes.
`scripts/ips_apply.py` applies one so you can re-run the analysis on the result.

A patch labels its own target by what it claims to do. On the reference game,
five patches identified the palettes, the sprite art, the frame and hitbox
tables, the sound driver and PCM, and the character-select screen code, before
any of those had been found by reading.

### 8. Solve the text encoding

**Check for plain ASCII first.** It costs one grep and game 2 turned out to be
exactly that: uppercase 7-bit ASCII with no glyph table at all. Do not start
solving a custom encoding until you have ruled out the free case.

If it is not ASCII, two releases saying the same line give you the font. See
`references/text.md` for the method and for the shapes to expect: split alphabet ranges,
proportional glyphs with continuation tiles, per-glyph attribute bits that
differ between regional builds.

Before declaring that something visible on screen is *not* text, test all of:
exact tilemap words, words shifted to another tile bank, letter-spacing
patterns, raw bytes, and bytes at any constant offset. What survives all five
is drawn art.

### 9. Map the tables

`scripts/xref.py <rom> <addr>` answers "what points here" by scanning for
self-relative words, because in this engine class data is addressed the same
way as code.

For anything indexed per entity, get the stride from the code that computes it,
never from how the data looks.

A name in a facts module is a hypothesis until what it points at decodes. On
the reference game a table labelled "portrait art" pointed at `$FF`-terminated
byte lists: an animation script, not art.

### 10. Find the art

**Start from the decompressor's callers, not from a sweep.** Once the art
decompressor is identified, each call site loads its source from a table a few
instructions earlier, and the palette table for the same screen is usually next
to it. On the reference game one select-screen call site gave the portrait
table and its palette table in minutes.

**If you do sweep**, decode at every even offset and filter hard:

* Over code, a decoder happily "succeeds": the output runs to the maximum size
  at a suspiciously high ratio (5x and up on the reference game).
* Real streams are **contiguous**: each ends exactly where the next begins, at a
  moderate ratio (about 1.5x to 4.5x there). Contiguity is the strongest signal.
* A sweep still yields far more than you can identify by eye. Use it to find
  clusters, then go back to the callers.

**Render every candidate in more than one tile order.** There is no single
correct layout:

* sprites are column-major inside each hardware piece (up to 4x4 tiles);
* portraits and backgrounds are usually row-major, at an unknown width;
* large screens may be tile-deduplicated and placed by a separate nametable,
  which looks scrambled in any order until you find the map.

Render row-major at several widths plus column-major 4-high, side by side, and
pick the one that reads cleanly. Greyscale is enough to see shapes; render with
the real palette to confirm what it is.

**Lay a whole set out before naming anything.** Render every frame of one
character on one sheet, each labelled with its index and tile count, on a wide
canvas with the origin drawn. On the reference game index order grouped frames
by move class, so one sheet named every move without the animation scripts. The
origin is the character's position, not the body's centre: a lunge draws the
body well ahead of it, and a frame that looks empty may be off a tight canvas.

**Map VRAM from the load lists, per screen.** Each pattern-load entry gives an
art's destination tile; the compressed stream's header gives its tile count;
the plane, sprite and scroll tables sit at the bases set in VDP registers 2, 3,
4, 5 and 13. What no list of any level covers is free. On a platformer this
found a 10-tile gap between two art sets that held in every zone.

**Check a decoded layout against an independent quantity.** On the reference
game the sprite-piece table was only trusted once each frame's piece tile counts
summed exactly to that frame's decompressed art size. An off-by-one origin in
the frame table produced plausible but wrong pieces until that check was run.
On the racing game the same check confirmed two sprite formats: header plus
tile count times 32 equalled every resource's size, and each frame's tiles ended
exactly where the next frame's began. A guess is confirmed when sizes add up
across all entries, not when one entry renders.

**Look for a resource directory.** Some engines keep every graphic and palette
behind one table of `[id.w][pointer.l][size.w]` entries read by a single lookup
routine, and load assets by ID. Once found, it labels the whole asset set at
once. Reach it from the hardware side: a CRAM write is usually a DMA from a RAM
palette buffer; find the code that fills that buffer, and the value passed to
the routine it calls is an ID. On the racing game this beat scanning the data
for palette-shaped runs, which gave 63 candidates and no answer.

**Use screenshots as runtime evidence.** A screenshot from the operator can find
the art when reading cannot. Measure the pixel grid first: a histogram of colour
run lengths gives the scale (one game's capture was exactly 12 screen pixels per
console pixel), and the commonest edge position modulo that gives the crop
offset. Never assume a capture shows the full screen. Then, at all 64 grid
alignments, test each 8x8 block against every ROM tile: require a one-to-one
mapping between screen colours and tile indices, with the background as index 0.
The matches give the tiles and the palette at once.

**When the art comes from a Game Gear or Master System ROM.** A Mega Drive
project can borrow art from another Sega system. Those tiles are 4bpp planar:
each 8-pixel row is 4 bytes, one bit plane each, and a pixel's index takes bit
`7-x` of each. The CPU is a Z80 (`z80dis` is a pure-Python disassembler). Find
the VRAM loaders from the VDP data port: `out ($BE),a`, or `outi`/`otir` after
`ld c,$BE`. Bank switching writes `$FFFF`, so a loader's source address is only
meaningful with the bank it set.

### 11. Record anchors, not addresses

Write findings as masked byte signatures with the volatile bytes wildcarded,
not as fixed addresses. Signatures survive across regional builds; addresses do
not. On the reference game the same engine sat at completely different
addresses in the Japanese and European releases, and signature-anchored tools
worked on both with no second codebase.

Keep the result as a single per-game facts module: addresses, layouts, and how
sure you are of each. `log/example-facts.py` is the one from the reference game.
Whatever else it holds, give it these, because the listing and the progress
report (step 12) read them:

* the identity of every ROM used: release, size, SHA-1 (step 1);
* `NAMES`, address to name, for every routine, table and RAM variable you have
  read well enough to name. `emit.py` prints these in place of `sub_`/`ram_`;
* the region map: one entry per mapped range (start, end, what it is) with a
  confidence (`solid`: read and confirmed; `likely`: strong structural
  evidence; `guess`).

### 12. Write it up

The map is only useful if someone else can rerun it. Package it so they can,
without shipping the game, and in the same shape every time: someone who has
read one of these repositories should find everything in the next one where
they expect it.

**No game bytes in the repository.** Every tool takes the ROM path as an
argument; nothing assumes a folder, and the README's commands use a placeholder
such as `<rom>`. Anything generated from the ROM that holds its bytes (the
listing, decoded art, a patched build) goes in `build/`, which `.gitignore`
lists. A file that holds only addresses and ranges (the trace JSON, a diff's
region list) holds no game bytes: track it, outside `build/`, so anyone can
check the numbers without a ROM. Third-party patches are studied, credited and
never included.

**The facts module is the source of truth.** Every address is recorded there
(step 11), and the tools and the progress report read it. Prose may cite an
address for orientation, but never as the only record of it: if the README or
the notes give an address the facts module lacks, add it to the module.

**The README**, with these headings, in this order:

1. `# <Game> disassembly`, two sentences on what it is, then the line
   **This repository contains no game code or data.** followed by a sentence
   on how the reader supplies their own ROM.
2. `## Supported version`: a table with one row per ROM used (release, size,
   SHA-1, what it was used for: the trace target, a diff partner, a patch
   base). A patched build is a row too, named by its base and its patch. Below
   the table, one sentence saying whether the releases are revisions or
   separate compiles (step 6).
3. `## Building`: the commands, with `<rom>` for the ROM path, and what each
   needs (Python 3, `capstone`). The trace command writes to the tracked trace
   (`traces/<release>.json`); the listing and anything else holding game bytes
   to `build/`.
4. `## What is here`: a table, one row per file or folder a reader would open:
   the facts module, the notes (in `log/`), the trace, each tool, the progress
   script.
5. `## Progress` (below).
6. One section per subject the analysis covered, short, pointing at the facts
   module and the notes: `## Engine` (dispatch idioms, unresolved sites), then
   any of `## Text`, `## Graphics`, `## Sound` that apply.
7. `## Third-party sources`: whose patches or translations were studied, by
   author where known (otherwise "author unknown" and where it came from), that
   none is included, and that the game's trademarks belong to their owners.
8. `## Licence`: the licence by its SPDX identifier (for example
   `GPL-3.0-or-later`), a `LICENSE` file with its text, and that it covers the
   tools and notes, not the game.

Anything the operator adds beyond that (links, credits, sections about tools
that live elsewhere) goes after section 6 and before Third-party sources.

**Bring the facts module up to step 11 first.** The report reads the
identities, `NAMES` and the region map; if the module lacks them (findings
still in prose, a region table in a separate file, a confidence scale of its
own), move them into the module before writing the report, keeping its scale
if it has one (HIGH, MED, LOW reads the same as solid, likely, guess).

**A progress report from a script, not from memory.** `<tools>/progress.py`
(`<tools>` being the folder the repository keeps its tools in, usually
`tools/`), run from the repository root, prints measures read from the trace
JSON and the facts module only, so it needs no ROM. Report, as
`label  percent  detail` lines, with `-` in place of the percent where a
measure has no total, and the release in the detail wherever the repository
measures more than one ROM:

* traced code: bytes and instructions reached, as a share of the ROM;
* indirect call sites still unresolved, and dispatch tables resolved;
* named routines: `NAMES` entries the trace labels as subroutines, out of
  all the subroutines the trace labels;
* named RAM variables: `NAMES` entries in RAM, out of the RAM addresses the
  trace saw referenced;
* mapped regions by confidence, and the bytes the solid and likely ones cover;
* assets decoded, where the facts module records them: compressed blocks that
  decode, sprite frames found and identified.

Coverage alone is meaningless (step 4): it is one line among these, never the
headline. A measure is never estimated: if its source does not exist yet, the
line says `not recorded yet`, so the gap stays visible.

Put the report in the README between `<!-- progress -->` and
`<!-- /progress -->`, inside a code block, and keep it current with a
pre-commit hook at `<tools>/hooks/pre-commit` that reruns the script, rewrites
the block and stages `README.md`. Say how to enable it under the block:
`git config core.hooksPath <tools>/hooks`, once per clone. If the trace is not
tracked and is missing, the hook leaves the block as it is and the commit goes
ahead.

## Rules that apply throughout

* **A constant appears in more than one place.** On the reference game a single
  logical value existed in seven separate sites. Assume duplicates until a test
  proves otherwise. Data duplicates by context too: the racing game held its
  first stage's palette twice, once for the race start and once in the stage
  table, and a patch to one copy showed up only seconds into the race.
* **A short absolute address can be RAM.** On the 68000 a `.w` absolute address
  sign-extends, so `$8000` to `$FFFF` mean `$FF8000` to `$FFFFFF`. `lea $B600.w`
  is a RAM table built at runtime, not ROM at `$00B600`.
* **List the palette slots the code writes directly.** A colour written straight
  to CRAM each frame (a flashing light, a cycling stripe) is not a free slot,
  however unused the palette data makes it look. Anything painted in it flashes
  too.
* **An immediate byte is the last byte of the instruction**, not the address the
  disassembler prints for it. Getting this wrong points you at the high half of
  an immediate word, which reads `$00` and silently does nothing.
* **Runs of `$00` inside the program area are not free space** unless
  cross-checked against the trace.
* **Check whether boot verifies the header checksum; do not assume either way.**
  Game 1 verified it and hung on mismatch. Game 2 did not verify it at runtime,
  and a released translation patch for it leaves the field stale with no visible
  effect. Read the boot code before deciding whether a checksum matters.
* **An incomplete decoder invents findings.** If results look like a pattern of
  failures in the data, suspect your own tables first. On the reference game, a
  scan reported 47 fields a translation had "missed"; 46 of them were three
  glyphs missing from the font map.
* **Prefer facts the ROM confirms at runtime** over conclusions from reading
  alone. Reading code produced wrong answers three separate times where a
  runtime measurement was right first try. Running an emulator or any other
  program on the operator's machine is their call: ask first, or work from the
  screenshots they choose to send.
* **Verify against observable behaviour**, not against the artifact you
  inspected. Data being correct in a table does not mean it is what the screen
  is drawing.
* **Know which ROM every artifact was made from.** A listing, a facts module and
  a tool can each have been built against a different regional release. Before
  using an address from one of them, compare its ROM hash with the one you are
  reading. If they differ, carry the finding over by signature (step 11), never
  by address. On the reference game, addresses from a European listing were
  decoded against the Japanese ROM and produced garbage; the loader's byte
  signature found the right code immediately.

## Scripts

| script | what it does |
|---|---|
| `trace.py` | recursive-descent 68000 tracer, resolves known dispatch idioms, takes manual seeds |
| `emit.py` | labelled, symbolised listing plus a structure map from a trace |
| `listing.py` | dump one address range from an existing trace |
| `mapdump.py` | coarse entropy and decodability map of a whole ROM |
| `xref.py` | find self-relative words pointing at an address |
| `ips.py` | summarise which regions a patch writes |
| `ips_apply.py` | apply a patch, so the analysis can be re-run on the result |
| `ips_make.py` | write a patch from a base and a modified ROM |
| `tiles.py` | render a range as 4bpp tiles to a PNG, to look at art |

They need Python 3 and `capstone` (`pip install capstone`).

## When the ROM does something not described here

That is the expected case. Record it in `log/` as a short note: what the shape
was, how you recognised it, what it turned out to be. If it is a dispatch idiom,
add it to `references/idioms.md` and to `trace.py`, because that is what makes
the next ROM cheaper.
