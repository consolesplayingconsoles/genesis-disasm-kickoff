# Diffs as documentation

## Other releases

**Measure the divergence before planning around it.** Diff every pair and look
at what fraction of the ROM differs:

* a few percent, a revision: offsets mostly transfer and the diff is a precise
  map of what changed
* nearly everything: a separate compile. Seen at 98% between two releases four
  months apart, which also differed in frame rate and had a password system in
  one and not the other. Nothing transfers, and the diff tells you nothing
  about the text

In the second case the third-party patches below become the primary tool rather
than a supplement, because each is a diff against a single fixed base.

Then merge the differing byte ranges into regions. Then classify each region by whether its words decode as glyphs:

* mostly decodable, and the two versions read as the same sentence in different
  languages: **script**
* not decodable: **art the other version redrew**

Both answers are useful. The second is how you find where a screen's graphics
live without touching the graphics code.

Watch for releases that are not just translations. On the reference game, the
Japanese and European builds differed across 500 KiB and every engine anchor
sat at a different address, so offsets from one did not transfer to the other.
Verify that before assuming a finding carries over.

## Third-party patches

An IPS or BPS patch is a labelled dataset: someone else already found the thing
they changed, and the offsets say where it is.

Summarise the regions with `scripts/ips.py`. Then read the patch's own
description and attach that meaning to those offsets. On the reference game
this identified, without any code reading:

| patch's stated purpose | what its offsets marked |
|---|---|
| colour hack | the palette tables |
| character sprite replacement | the sprite art region, and the frame/hitbox tables |
| voice hack | the sound driver and PCM, and that ROM expansion is viable |
| new character select | the screen's code, and that it built new code into `$FF` filler |

Apply patches with `scripts/ips_apply.py` and re-run your own analysis on the
result. Comparing a structural fact before and after (a table's entry count, a
bound, a layout) answers questions about the patch far faster than reading it.

Watch what patches do about the header checksum, and read it as evidence rather
than as a rule. In game 1 every patch disabled the boot checksum, which told us
the check existed and where. In game 2 a released patch simply leaves the
checksum field stale, which tells you the opposite: that build does not verify
it at runtime.
