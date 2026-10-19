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

Watch for releases that are not just translations. Japanese and
European builds can differ across hundreds of KiB with every engine anchor at a
different address, so offsets from one do not transfer to the other.
Verify that before assuming a finding carries over.

## What else is worth comparing against

Anything built from the same code answers a question for free. In rough order of
what it buys you:

| source | what a diff against it gives | seen working |
|---|---|---|
| another language release | the script map: the differing regions **are** the text | yes |
| another region or revision | which offsets transfer, and what the revision changed | yes |
| a fan translation or hack patch | each patch labels the region it changes, by its own description | yes |
| **a prototype or pre-release build** | the biggest prize when it exists: pre-release builds are often less compressed, carry debug menus, and sometimes ship the linker's symbol table. A diff against the retail build separates "what the game is" from "what shipped" | not yet |
| another game by the same developer | shared engine code. Two unrelated games here had byte-identical boot and pad-read routines because both came from Sega's sample code | yes |
| a later port or compilation release | sometimes the identical ROM (so nothing), sometimes a rebuild with symbols. Check the hash before assuming either | not yet |
| an existing disassembly of the same game | not a diff, a reference. Building it tells you which revision you hold, and names everything it has already named | yes |

Prototypes and ports are the two this skill has not exercised yet. Note what you
find when you do.

## Third-party patches

An IPS or BPS patch is a labelled dataset: someone else already found the thing
they changed, and the offsets say where it is.

Summarise the regions with `scripts/ips.py`. Then read the patch's own
description and attach that meaning to those offsets. This can identify,
without any code reading:

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
than as a rule. A patch that disables the boot checksum tells you the check exists and where;
a patch that simply leaves the checksum field stale tells you the opposite:
that build does not verify it at runtime.

## Cheat databases

A cheat code is a labelled address: a human-readable description paired with a
location someone else already found. `libretro/libretro-database` publishes them
in `cht/`, one directory per system, fetchable without asking anyone:

```
cht/Sega - Mega Drive - Genesis/<game>.cht      ~2100 files
cht/Sega - Master System - Mark III/<game>.cht   ~720 files
```

On this platform the codes are **Game Genie, so they name ROM addresses**, not
RAM. "Start with 5 lives" points at the byte holding the starting lives, and the
value already in the ROM confirms you decoded it correctly. That is a labelled
pointer into code or data, for free, before reading an instruction.

Two limits, both measured rather than assumed:

* **Nothing about input handling.** Across 60 sampled Mega Drive files, "start"
  appeared 113 times and every one meant "start with max energy" or "start on
  mission 3". Actual input words were noise. For controller code, signatures
  beat this comfortably.
* **Per game.** A game with no file in the database gives you nothing, and plenty
  have none.

Treat it as a lead source to read, not something to build tooling around. The
decoding (Game Genie's bit permutation) is easy to get subtly wrong from memory;
take it from an emulator's source if you need it.
