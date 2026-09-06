# Reference game: 2 MiB fighting game, 1994

The game this skill was extracted from. Disassembled from nothing in a day,
with three regional/translated builds and six third-party patches available.

## Numbers

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

## Engine shape

* Boot at the reset vector, checksum over `$000200` to the ROM end compared
  against a header field, hanging on mismatch.
* A main loop reading a mode variable and dispatching through a `bra.w` slot
  table.
* Everything below that dispatched through **self-relative word tables**, in
  both code and data. This one idiom was the difference between 0.2% and 5%.
* Data addressed exactly like code, so "what points here" is a scan for
  self-relative words.

## Text

Raw VDP tilemap words, `$FFFF` terminated, fixed-width pre-padded fields. Split
alphabet ranges, proportional glyphs with continuation tiles, separate case
blocks, and attribute bits that differed between the Japanese and European
builds of the same game.

Solved from two language versions of the same lines. Punctuation identified
afterwards from context, by frequency, inside runs of known letters.

A second, parallel set of the same names existed as **pixel art** for the HUD
and the character grid, while the tables held real text. Both were live at
once. Do not assume one representation.

## What the third-party patches gave up

Without reading any code: the palette tables, the sprite art region, the frame
and hitbox tables, the sound driver and PCM, and the character-select screen's
code. Also that ROM expansion past 2 MiB is viable for this platform, visible
in one patch's write offsets.

## Biggest time sinks

1. Inferring hardware facts from code instead of measuring them. Three separate
   wrong answers, each corrected by one runtime measurement.
2. Assuming a constant appeared once. It appeared in seven places.
3. Patching the address a disassembler printed rather than where the immediate
   byte sits.
4. Trusting an incomplete font map, which turned three missing glyphs into 46
   false findings about the data.

## Where this game's map lives

`example-facts.py` here is the per-game facts module that came out of it:
addresses, layouts, anchors as masked byte signatures, and a note on which
entries were measured rather than read. `example-text-codec.py` is its font.

Both are examples of the *shape* of a finished per-game artifact, not
something to reuse on another ROM.
