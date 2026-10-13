#!/usr/bin/env python3
"""The shape of a facts module: tools/facts.py in a disassembly repo.

Every value below is made up for illustration; none of it describes a real game. Copy the
structure, never the numbers. One module per game, the single source of truth: the listing,
the rebuild and the progress report read it, and prose may cite an address only if it is here.
"""

# ---- identity (step 1) ----------------------------------------------------------------------
ROM_SIZE = 0x200000
KNOWN = {                    # every ROM used: release -> (size, SHA-1, what it is used for)
    'Example Game (Europe)': (0x200000, '0' * 40, 'the trace target: every address below'),
}

# ---- what you measured (keep the evidence next to the number) --------------------------------
MODE_VAR = 0xFFE000          # game mode, dispatched through the bra.w table at $400.
                             # MEASURED at runtime: reading the table alone gave a wrong value.

# ---- names (step 11): routines, labels, RAM variables, data ------------------------------------
NAMES = {
    0x000200: 'EntryPoint',
    0x000400: 'GameModeTable',       # bra.w slots, one per mode
    0x001000: 'ReadJoypads',         # read: both pads into Joypad1/2
    0x002000: 'DecompressToVram',    # a0 = stream, a1 = VRAM address
    0xFFE000: 'GameMode',
    0xFFE002: 'Joypad1',
    0xFFE003: 'Joypad2',
}

# ---- the region map: (start, end inclusive, what, confidence) ---------------------------------
# confidence: solid (read and confirmed), likely (strong structural evidence), guess.
REGIONS = [
    (0x000200, 0x0003FF, 'boot: TMSS, checksum, RAM clear', 'solid'),
    (0x040000, 0x05FFFF, 'compressed art, contiguous streams', 'likely'),
]

# ---- the rebuild (step 12) -----------------------------------------------------------------------
# (start, end inclusive, name, format): each checked whole against the decoder that reads it.
BLOCKS = [
    (0x040000, 0x0412FF, 'title_screen_art', 'compressed_tiles'),
    (0x041300, 0x04131F, 'title_screen_palette', 'palette'),
]
# Tables of absolute longs into the ROM, written as labels.
PTR_TABLES = [
    (0x030000, 0x03001F, 'StageArtTable'),
]
# Instructions whose immediate is a ROM address (it becomes a label).
POINTERS = {0x001234}
# Instructions whose immediate falls in the ROM's range but is a number.
CONSTANTS = {0x001240}       # move.w #$8F02,(VDP_CTRL).l: a VDP register write
# Ranges the trace took for code that are data.
NOT_CODE = [
    (0x00C000, 0x00C0FF),    # a table the walk read past its end
]

# ---- anchors (step 11): masked byte signatures that survive other releases ----------------------
SIGS = {
    'ReadJoypads': '41F9 00A1 0003 ?? ?? 4E75',
}
