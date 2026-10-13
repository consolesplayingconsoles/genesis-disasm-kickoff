# Working on this disassembly

This repo rebuilds the game's ROM byte for byte. Keep it that way: every change ends with
`bash build.sh` printing `MATCH`.

The disassembly is done when every byte of the ROM is source: code in **named routines with
symbolic operands** (no ROM address left as a number, so an edit that moves code still builds) and
data in **named blocks of a decoded format**. `python3 tools/progress.py` measures exactly that as
its first row, `done: equivalent source`. Nothing else counts toward it: a map of the ROM, traced
code or decoded art are progress, reported below it, not the goal.

## Layout
- `@FACTS@`: the source of truth. Every address, name and layout is recorded here, and the source
  is generated from it: you change the facts, never the generated files.
  - `NAMES`: address -> name, for routines, labels, RAM variables and data blocks
  - `BLOCKS`: `(start, end, name, format)` per data block; `format` is what decodes it
  - `POINTERS`: instructions whose immediate is a ROM address (it becomes a label)
  - `NOT_CODE`: ranges the trace took for code that are data
  - `PTR_TABLES`: tables of absolute longs into the ROM (written as `dc.l <label>`)
  - `CONSTANTS`: instructions whose immediate falls in the ROM's range but is a number
  - `FIELDS` / `FIELD_AT`: struct field names for displacements (`obVelX(a0)`, not `$10(a0)`)
  - `SEEDS`: hand seeds for the tracer (`python3 tools/trace.py build/rom.bin @TRACE@ @FACTS@`)
- `@TRACE@`: the trace (addresses only). Re-trace with `python3 tools/trace.py` and new seeds when
  you find code it missed.
- `build/src/`: the generated source (`main.asm`, `code/<routine>.asm`, `data/<block>.bin`). Yours,
  never committed: it holds the game.
- `@RECORD@`: what the last build emitted (addresses, names, formats; no game bytes). Committed:
  the progress report reads it.

## The loop
1. **Read a routine** in `build/src/code/`, with who calls it (`python3 tools/callers.py
   build/rom.bin @TRACE@ <addr>`: traced instructions naming it; `tools/xref.py` finds
   self-relative word tables pointing at it) and the notes in `log/notes.md`.
2. **Name it** in `NAMES` (and its RAM variables). A name is a claim about what it does: name only
   what you have read; leave `sub_<addr>` where you have not.
3. **Make it symbolic**: a routine that is not symbolic still has a ROM address as a number. Most
   are immediates loading a table or a handler (`move.l #$2392, ...`): add the instruction's
   address to `POINTERS`. An immediate that is a number (a count, a mask, a VDP command) goes in
   `CONSTANTS` instead. A RAM or hardware operand needs its name in `NAMES`, every label inside
   the routine a name too, and every displacement off an address register a field in `FIELDS`. A `dc.w` with a comment is an instruction AS encodes differently, or
   data the trace took for code (`NOT_CODE`).
4. **Data**: give each block between routines a name and a format in `BLOCKS`, once a tool here
   decodes it (compressed art, sprite frames, palettes, text, tables).
5. `bash build.sh`: `MATCH`, then `python3 tools/progress.py`. Commit; the pre-commit hook writes
   the report into the README.

A name or a format is evidence-backed or it is not there. Never name in bulk from guesses to move
the number: the number then measures nothing.
