#!/usr/bin/env python3
"""Find code two ROMs share, so a labelled one can name an unlabelled one.

    shared.py <rom> <reference rom> [min-run]

Sega shipped the same parts to different studios, so an unknown ROM often
contains runs that are byte-identical to a game you already have a disassembly
for. Each shared run is a routine someone has already named.

What this finds and what it cannot:

* It matches EXACT bytes, so it catches position-independent code: sound driver
  ticks, maths, decompressors. A routine that references absolute addresses
  differs between games wherever it names data, so you get the middle of it and
  not the ends. Expect dozens of runs, not whole modules.
* Clustering is the signal, not any single run. Ten runs landing in one 4 KiB
  window of both ROMs is a shared module; one run on its own is a coincidence.
* Filler and flat data are skipped (a window needs 6 distinct byte values),
  otherwise runs of $00 and $FF drown everything.

To turn offsets into names, build the reference from its disassembly and keep
the symbol file, then look up the reference-side offset.
"""
import collections
import sys

W = 24                      # window: long enough to be meaningful, short enough to catch stubs


def shared_runs(a, b, window=W):
    """-> [(length, offset in a, offset in b)], longest first, deduplicated."""
    idx = {}
    for i in range(0, len(a) - window, 2):
        w = a[i:i + window]
        if len(set(w)) >= 6:
            idx.setdefault(w, i)
    runs = {}
    for j in range(0, len(b) - window, 2):
        i = idx.get(b[j:j + window])
        if i is None:
            continue
        k = window
        while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
            k += 1
        back = 0
        while i - back > 0 and j - back > 0 and a[i - back - 1] == b[j - back - 1]:
            back += 1
        key = (i - back, j - back)
        runs[key] = max(runs.get(key, 0), k + back)
    return sorted(((v, i, j) for (i, j), v in runs.items()), reverse=True)


if __name__ == '__main__':
    a = open(sys.argv[1], 'rb').read()
    b = open(sys.argv[2], 'rb').read()
    floor = int(sys.argv[3]) if len(sys.argv) > 3 else W
    runs = [r for r in shared_runs(a, b) if r[0] >= floor]
    total = sum(v for v, _, _ in runs)
    print('%d shared runs, %d bytes' % (len(runs), total))
    if not runs:
        print('nothing shared: different parts bin, or the reference is the wrong game')
        sys.exit(0)
    print('\nclusters (where a shared module lives):')
    cl = collections.Counter((i >> 12, j >> 12) for _, i, j in runs)
    for (pi, pj), c in cl.most_common(6):
        if c > 1:
            print('   %05X-ish  <->  %05X-ish   %d runs' % (pi << 12, pj << 12, c))
    print('\nlongest runs:')
    for v, i, j in runs[:8]:
        print('   %4d bytes   %06X  <->  %06X' % (v, i, j))
