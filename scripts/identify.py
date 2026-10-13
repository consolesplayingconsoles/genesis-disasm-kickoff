#!/usr/bin/env python3
"""Step 1: say what this file is, before anything else runs.

    identify.py <rom, or a .zip holding it>

This skill covers the Mega Drive FAMILY: the same 68000 and VDP, whatever the
box was called. That is more than one console, and they are told apart by the
console string at $100, which every member carries in the same header layout:

    SEGA MEGA DRIVE / SEGA GENESIS   the console
    SEGA PICO / SEGA TOYS PICO       the Pico, same silicon, different I/O
    SEGA 32X                         Mega Drive plus two SH-2s: out of scope

Anything else is refused rather than guessed at. A Master System ROM is named
specifically, because it is the easy mistake to make from a shelf of Sega files
and it is a different CPU entirely (see master-system tooling, not this).
"""
import struct
import sys

FAMILY = [
    ("SEGA MEGA DRIVE", "mega-drive"),
    ("SEGA GENESIS",    "mega-drive"),
    ("SEGA TOYS PICO",  "pico"),
    ("SEGA PICO",       "pico"),
    ("SEGA SSF",        "mega-drive"),   # the SSF bank-switching mapper header: still a Mega Drive game
]
OUT_OF_SCOPE = {
    "SEGA 32X": "a 32X ROM: Mega Drive plus two SH-2s. The 68000 side traces, "
                "but the game's code is mostly SH-2 and this skill does not cover it.",
}


def text(rom, at, n):
    return "".join(chr(b) if 32 <= b < 127 else " " for b in rom[at:at + n]).strip()


def identify(rom):
    """-> (platform, header dict) or raises SystemExit with the reason."""
    if len(rom) >= 0x8000 and rom[0x7FF0:0x7FF8] == b"TMR SEGA":
        raise SystemExit("this is a Master System / Game Gear ROM (TMR SEGA at $7FF0).\n"
                         "Different CPU (Z80): use the Master System tooling, not this skill.")
    if len(rom) < 0x200:
        raise SystemExit("too small to hold a Mega Drive header.")
    console = text(rom, 0x100, 16)
    for name, reason in OUT_OF_SCOPE.items():
        if name in console:
            raise SystemExit("%s\n%s" % (console, reason))
    for name, platform in FAMILY:
        if name in console:
            break
    else:
        raise SystemExit("console string at $100 is %r.\n"
                         "Not a Mega Drive family ROM, so this skill does not apply."
                         % console)
    head = {
        "console":   console,
        "copyright": text(rom, 0x110, 16),
        "title":     text(rom, 0x120, 48),
        "overseas":  text(rom, 0x150, 48),
        "serial":    text(rom, 0x180, 14),
        "io":        text(rom, 0x190, 16),
        "region":    text(rom, 0x1F0, 3),
        "rom_end":   struct.unpack_from(">I", rom, 0x1A4)[0],
        "checksum":  struct.unpack_from(">H", rom, 0x18E)[0],
    }
    total = 0
    for a in range(0x200, len(rom) - 1, 2):
        total = (total + struct.unpack_from(">H", rom, a)[0]) & 0xFFFF
    head["checksum_ok"] = (total == head["checksum"])
    return platform, head


def load(path):
    """The ROM's bytes: from a .zip (its largest file), and de-interleaved if it is a .smd dump
    (512-byte copier header, then 16 KiB blocks of odd bytes then even bytes)."""
    if path.lower().endswith(".zip"):
        import zipfile
        z = zipfile.ZipFile(path)
        info = max(z.infolist(), key=lambda i: i.file_size)
        rom, path = z.read(info), info.filename
    else:
        rom = open(path, "rb").read()
    if len(rom) % 0x4000 == 0x200 and b"SEGA" not in rom[0x100:0x110]:
        body, out = rom[0x200:], bytearray()
        for b in range(0, len(body), 0x4000):
            blk = body[b:b + 0x4000]
            for i in range(0x2000):
                out += bytes((blk[0x2000 + i], blk[i]))
        print("(interleaved .smd dump: de-interleaved; convert it to a plain .bin before tracing)")
        rom = bytes(out)
    return rom


if __name__ == "__main__":
    rom = load(sys.argv[1])
    platform, h = identify(rom)
    print("platform   : %s" % platform)
    print("console    : %s" % h["console"])
    print("title      : %s" % h["title"])
    print("overseas   : %s" % h["overseas"])
    print("serial     : %s   region %s" % (h["serial"], h["region"]))
    print("I/O support: %s" % (h["io"] or "(blank)"))
    print("size       : %d KiB   header says ROM ends at %06X" % (len(rom) // 1024, h["rom_end"]))
    print("checksum   : %04X %s" % (h["checksum"], "ok" if h["checksum_ok"] else "MISMATCH"))
    if platform == "pico":
        print("\nPico: same 68000 and VDP, so the tracing steps apply unchanged.\n"
              "What differs is I/O (pen and page sensor instead of a pad) and sound.\n"
              "Find those the same way as any other hardware access: by what the code touches.")
