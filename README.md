# genesis-disasm-kickoff

A Claude skill that starts a disassembly of a Sega Mega Drive family game (Mega Drive, Genesis,
Pico) from your own ROM.

You get a repo that:

* rebuilds the ROM **byte for byte** from source: one assembly file per routine, every branch and
  reference a label, the data between them as files, assembled with AS;
* has the engine mapped: the code traced through the game's own dispatch idioms, the tables, the
  text encoding and the art, each recorded in a facts module with how sure it is;
* measures how far along it is with one main number, `done: equivalent source`: the share of the
  ROM that is named, symbolic code and named, decoded data, in a build that still matches;
* describes the loop for naming and decoding the rest, with the build checking every step;
* contains **no game code or data**: everything game-derived is generated from your ROM.

What the skill did on each game it has been run on is in
[`references/evidence.md`](references/evidence.md).

## Install

The skill is a folder: `SKILL.md` plus the `scripts/`, `template/` and `references/` it runs.
Install the whole folder, not `SKILL.md` alone.

* **Claude (claude.ai or the desktop app):** build the zip, then upload it as a skill (Settings,
  Capabilities, Skills):
  ```
  git clone https://github.com/consolesplayingconsoles/genesis-disasm-kickoff
  bash genesis-disasm-kickoff/zip.sh
  ```
  It writes `genesis-disasm-kickoff/dist/genesis-disasm-kickoff.zip`. Then ask Claude to start a
  disassembly of your game. The work runs in Claude's own workspace, so you upload your ROM there
  when it asks.
* **Claude Code:** clone it into your skills folder, then ask Claude to start a disassembly of your
  game:
  ```
  git clone https://github.com/consolesplayingconsoles/genesis-disasm-kickoff ~/.claude/skills/genesis-disasm-kickoff
  ```
  The work runs on your machine, with your ROM where it already is.

If only `SKILL.md` got installed, the skill fetches its own tools from this repo before starting.

**What you provide:** your ROM, and any other release or patch of the game you have (each one is
worth a lot: the skill says why). You also need Python 3 with `capstone`, and AS, Alfred Arnold's
macro assembler, wherever it runs.

## Third-party sources

The procedure can use reference disassemblies of other games and third-party patches. The
repositories named in the skill are identified solely as examples of the type of material that
helps. We have no affiliation with, and make no representation regarding, those repositories,
their contents, or their licensing. Nothing is retrieved without your confirmation, and you are
solely responsible for determining whether you are entitled to obtain and use any such material.

## Where this comes from

It came out of real work on Consoles Playing Consoles. See what Pluto has helped me build:

- 📸 **Instagram:** [@consolesplayingconsoles](https://www.instagram.com/consolesplayingconsoles/)
- 🔗 **Everything else:** [beacons.ai/consolesplayingconsoles](https://beacons.ai/consolesplayingconsoles)

## License

© 2026 consolesplayingconsoles. Licensed under **Creative Commons Attribution-ShareAlike 4.0 International** ([CC BY-SA 4.0](LICENSE)): use it, share it, adapt it, as long as you credit the project and share what you build on it under the same licence.
