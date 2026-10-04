# Third game: 1 MiB racing game, 1991

Mapped for a graphics mod: find the player car's driver and passenger sprites and
the roadside ground colours. Text and sound were not examined.

## What it contradicted

| | games 1 and 2 | game 3 |
|---|---|---|
| dispatch idioms | three each, the highest-leverage step | none needed: 3.63% coverage, 0 unresolved sites on the first trace |
| how assets are found | decompressor callers, level tables | one resource directory: `[id.w][pointer.l][size.w]`, 221 entries, one lookup routine |
| self-relative origin | the entry, or the table base | a sprite frame's tile offset counts from the frame's own header |

## What it added

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

## What cost the most time

* Treating sign-extended `.w` addresses as ROM.
* Assuming a screenshot showed the full screen. It was a crop at 12 pixels per
  console pixel; measuring the run lengths first would have matched on the first
  try.
* Scanning for palette-shaped data instead of following the CRAM write back.
