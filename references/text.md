# Working out the text encoding

## First, rule out the free case

Grep for plain ASCII before assuming anything custom. One of the two games so
far stored its entire script as uppercase 7-bit ASCII with no glyph table,
readable directly in a hex dump. That is a five-second check that can end this
whole step.

Also check the framing once you find text: in that game each line was delimited
by literal quote marks and preceded by a short binary header, and no pointer
table referenced the region by absolute address. Text can be found without the
mechanism that reads it being obvious.

## The fastest path: two languages

If two releases of the same game exist in different languages, diff them. The
differing regions are the text. Decode the same address in both, and the pair
tells you what each tile means, because you know what the sentence says in one
of them.

On game 1 this gave the entire script map in minutes: 43 KiB of differences in
40 tight regions.

**This fails when the releases are separate compiles.** In game 2, the European
and American builds differed across 98% of the ROM, so the version diff carried
no signal at all. Fall back to fan translation patches: each is a diff against
one base, so it isolates exactly the strings. Two independent translations
landing on the same span is strong confirmation, and that is what located that
game's ~44 KiB script region.

## Shapes to expect

Text was stored as **raw VDP tilemap words**, one word per glyph, `$FFFF`
terminated. Consequences worth knowing before you start editing anything:

* A stored string is a pre-rendered line. Trailing spaces pad it to the width
  of its box, so a field has a fixed width and a replacement must fit it.
  **Both games so far worked this way**, custom glyphs or plain ASCII alike: in
  game 2 only ~12.5 KiB of the 44 KiB script span actually changed between
  languages, the rest being shared framing and padding. Fixed-size slots with
  translators padding or truncating to fit look like the norm rather than the
  exception.
* The alphabet is **not contiguous**. It ran `a..k` from one base and `l..z`
  from another, because the glyphs wrap a tile-row boundary. Solve both halves
  separately or you get plausible-looking nonsense.
* Glyphs can be **proportional**: wide letters occupied two tiles, the second
  being a continuation that decodes to nothing.
* Upper and lower case were separate blocks, far apart.
* Digits and punctuation sit outside the letter runs and have to be identified
  individually, usually from context (see below).
* Each word carries **attribute bits** above the tile index (palette, priority).
  These differed between the Japanese and European builds of the same game, so
  do not hardcode them; take them from the data.

## Identifying punctuation

Collect every unmapped tile that appears *inside* a run of known letters, with
a few characters of context either side, and sort by frequency. The context
usually names the glyph outright: a tile appearing in `under_estimated`,
`warm_up` and `ill_chosen` is a hyphen; one appearing in `N_1` is a degree
sign; a frequent one at clause boundaries is a comma.

Do this before reporting anything about the data's quality. An incomplete font
map produces confident false findings.

## Before concluding "this is not text"

Words visible on screen are often drawn art, not encoded text. Test all five,
in this order, and only then call it art:

1. exact tilemap words
2. the same tile pattern shifted by a constant, which finds another tile bank
3. letter-spacing deltas, which survive a different alphabet base
4. raw bytes, for labels stored as byte tile indices
5. bytes at any constant offset

On the reference game, menu labels, the in-game HUD names and the character
grid all failed all five: they were pixel art, while a parallel set of names in
the tables was real text. Both existed at once, for the same characters.
