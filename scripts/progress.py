#!/usr/bin/env python3
"""progress.py: the disassembly's state, in several measures, the main one first. Run from the
repository root; it reads tracked files only (no ROM), so any clone prints the same report.

  progress.py [<facts.py> <trace.json> [<rebuild.json>]]

With no arguments it reads DEFAULTS below, which the kick-off fills in when it copies this file
into a repository's tools/ (so the pre-commit hook can run it bare).

  source     the main metric, "done: equivalent source": the share of the ROM that the source
             rebuilds byte for byte AND reads as source (named code with symbolic operands,
             named data in a decoded format). Read from the rebuild record; 0.0% until one exists
  rom map    the facts module's REGIONS by confidence, and the bytes the solid and likely ones
             cover: what each byte is, which is not the same as having it as source
  game code  subroutines named and documented, RAM variables named, code traced, unresolved
             indirect calls

The facts module gives ROM_SIZE, NAMES (address -> name) and REGIONS ((start, end inclusive,
what, confidence) with solid/likely/guess, or HIGH/MED/LOW). The trace is scripts/trace.py's.

The rebuild record is written by whatever rebuilds the ROM from the source, and holds addresses,
names and formats only, no game bytes:

  {"identical": true|false,
   "blocks": [{"start": int, "end": int (inclusive), "kind": "code"|"data", "name": str,
               "symbolic": bool (code: no raw ROM address left in any operand),
               "format": str (data: what decodes it; "raw" when nothing does)}]}

A byte counts as done only when the whole rebuild is identical and its block is named (not an
auto label such as sub_/loc_/off_) and readable: code symbolic; data either a leaf asset kept as
a binary file in a decoded format (LEAF: art, compressed streams, palettes, samples, fill), or
written by the rebuild as source ("source": true, e.g. pointer tables as dc.l labels). Data with
structure inside it (tables, sprite mappings, frame layouts, scripts, text) counts only as source.

Layout: a section title at column 0, then indented rows "label  percent  detail", "-" where a
measure has no total. The main metric is the first row of the first section and keeps its
label: tools that show the report (a dashboard, a README badge) find it by that label.

It also writes badge.svg (the main metric as a bar and a number) for the top of the README; the pre-commit
hook stages it with the Progress block.
"""
import glob, importlib.util, json, os, re, sys

DEFAULTS = ['@FACTS@', '@TRACE@', '@RECORD@']
args = sys.argv[1:] or DEFAULTS
if len(args) < 2 or args[0].startswith('@'):
    sys.exit(__doc__)
sys.argv[1:] = args
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[1])))   # its own imports
spec = importlib.util.spec_from_file_location('facts', sys.argv[1])
facts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(facts)
trace = json.load(open(sys.argv[2]))
rebuild_path = sys.argv[3] if len(sys.argv) > 3 else None
SIZE = facts.ROM_SIZE

LEAF = {'tiles', 'rle_tiles', 'compressed_tiles', 'rnc', 'lzss', 'lzss_frames', 'nemesis', 'kosinski', 'palette',
        'samples', 'pcm', 'fill'}


def readable(b):
    return bool(b.get('source')) or b.get('format', 'raw') in LEAF


AUTO = re.compile(r'^(sub|loc|off|ram|unk|byte|word|dword|tbl|ptr|jt|mode|vec|bad|bin|data|code)_[0-9A-Fa-f]+$')


def pct(a, b):
    return '%5.1f%%' % (100.0 * a / b) if b else '-'


rows = []

# -- the main metric: equivalent source --
rb = None
if rebuild_path:
    try:
        rb = json.load(open(rebuild_path))
    except (OSError, ValueError):
        rb = None
main = ('  done: equivalent source', 'rebuilds byte-identical; named code with every label and operand named; named leaf assets, structured data as source')
if not rb:
    rows += [('SOURCE', '', 'no rebuild recorded yet'),
             (main[0], pct(0, SIZE), main[1]),
             ('  rebuilds byte-identical', '-', 'not recorded yet')]
else:
    named = lambda b: bool(b.get('name')) and not AUTO.match(b['name'])
    size = lambda b: b['end'] - b['start'] + 1
    code = [b for b in rb['blocks'] if b['kind'] == 'code']
    data = [b for b in rb['blocks'] if b['kind'] == 'data']
    code_ok = sum(size(b) for b in code if named(b) and b.get('symbolic')
                  and b.get('named_labels', 0) == b.get('labels', 0))
    data_ok = sum(size(b) for b in data if named(b) and readable(b))
    inner = sum(b.get('labels', 0) for b in code)
    inner_named = sum(b.get('named_labels', 0) for b in code)
    flds = sum(b.get('fields', 0) for b in code)
    flds_named = sum(b.get('named_fields', 0) for b in code)
    code_b, data_b = sum(size(b) for b in code), sum(size(b) for b in data)
    rows += [('SOURCE', '', '%d blocks: %d code, %d data' % (len(rb['blocks']), len(code), len(data))),
             (main[0], pct(code_ok + data_ok if rb.get('identical') else 0, SIZE), main[1]),
             ('  rebuilds byte-identical', '-', 'yes' if rb.get('identical') else 'NO: nothing counts until it does'),
             ('  code as source', pct(code_ok, code_b), '%d of %d code bytes: named routine, labels and operands (addresses, struct fields) named' % (code_ok, code_b)),
             ('  data as source', pct(data_ok, data_b), '%d of %d data bytes: named leaf asset, or written as source' % (data_ok, data_b)),
             ('  local labels named', pct(inner_named, inner), '%d of %d labels inside routines' % (inner_named, inner)),
            ('  struct fields named', pct(flds_named, flds), '%d of %d displacements off an address register' % (flds_named, flds)),
             ('  named constants', '-', 'not required: an ID and a count look alike')]

# -- the ROM map --
level = {'solid': 'high', 'likely': 'medium', 'guess': 'low', 'HIGH': 'high', 'MED': 'medium', 'LOW': 'low'}
regions = getattr(facts, 'REGIONS', [])
conf = {'high': 0, 'medium': 0, 'low': 0}
covered = set()
for r in regions:
    c = level[r[3]]
    conf[c] += 1
    if c != 'low':
        covered.update(range(r[0], r[1] + 1))
for r in getattr(facts, 'BLOCKS', []):           # checked whole (rebuild.py): high confidence
    covered.update(range(r[0], r[1] + 1))
rows += [('ROM MAP', '', '%d regions: %d high, %d medium, %d low confidence' % (len(regions), conf['high'], conf['medium'], conf['low'])),
         ('  mapped, bytes', pct(len(covered), SIZE), 'high and medium confidence ranges, and the data blocks')]

# -- game code --
subs = {int(a, 16) for a, k in trace['labels'].items() if k == 'sub'}
ram = {int(a, 16) & 0xFFFFFF for a in trace['datarefs'] if int(a, 16) & 0xFFFFFF >= 0xFF0000}   # .w and .l alike
names = getattr(facts, 'NAMES', {})
named_subs = sum(1 for a in names if a in subs)
named_ram = sum(1 for a in names if a & 0xFFFFFF in ram)
docs = ''.join(open(p, encoding='utf-8', errors='replace').read() for p in sorted(glob.glob('*.md') + glob.glob('log/*.md')))
documented = sum(1 for a, n in names.items() if a in subs and n in docs)
code = SIZE - sum(e - s for s, e in trace.get('gaps', [])) if 'gaps' in trace else trace.get('coverage_bytes', 0)
unresolved = trace.get('unresolved', trace.get('num_unresolved_sites', []))
rows += [('GAME CODE (traced)', '', '%d subroutines, %d bytes of code' % (len(subs), code)),
         ('  named', pct(named_subs, len(subs)), '%d of %d subroutines' % (named_subs, len(subs))),
         ('  documented', pct(documented, len(subs)), '%d named subroutines in *.md' % documented),
         ('  named globals', '-', '%d of %d RAM variables referenced' % (named_ram, len(ram))),
         ('  traced code, of the ROM', pct(code, SIZE), 'the rest is art, audio and data'),
         ('  indirect calls unresolved', '-', '%d' % (unresolved if isinstance(unresolved, int) else len(unresolved)))]

def write_badge(rows, label, path='badge.svg'):
    """badge.svg beside the README: the label, a bar filled to the main metric ("done: ...") and its percentage, in
    Pluto's colours. One metric only; the number is always printed, so colour carries no meaning on its own."""
    done = 0.0
    for n, p, _ in rows:
        if n.strip().startswith('done:'):
            try:
                done = float(p.strip().rstrip('%'))
            except ValueError:
                done = 0.0
            break
    bar = 64
    wd = int(round(bar * min(done, 100.0) / 100.0))
    if done > 0 and wd < 2:
        wd = 2
    text = '%.1f%%' % done
    title = '%s: %s done' % (label, text)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="182" height="20" role="img" aria-label="%s">'
           '<title>%s</title><clipPath id="r"><rect width="182" height="20" rx="3"/></clipPath>'
           '<g clip-path="url(#r)"><rect width="52" height="20" fill="#1a2233"/><rect x="52" width="130" height="20" fill="#2a3347"/>'
           '<rect x="60" y="6" width="%d" height="8" rx="2" fill="#ecc9b9"/>'
           '<rect x="60" y="6" width="%d" height="8" rx="2" fill="#c87053"/></g>'
           '<g fill="#fff" font-family="Verdana,DejaVu Sans,sans-serif" font-size="11" text-anchor="middle">'
           '<text x="26" y="14">%s</text><text x="154" y="14">%s</text></g></svg>\n'
           % (title, title, bar, wd, label, text))
    try:
        open(path, 'w').write(svg)
    except OSError:
        pass
    # the README's badge link carries the number (badge.svg?p=40.3): a new number is a new address, so GitHub's image cache
    # never shows an old badge
    try:
        readme = open('README.md').read()
        fresh = re.sub(r'\(badge\.svg(\?p=[0-9.]*)?\)', '(badge.svg?p=%.1f)' % done, readme, count=1)
        if fresh != readme:
            open('README.md', 'w').write(fresh)
    except (IOError, OSError):
        pass


write_badge(rows, 'disasm')
for label, p, rest in rows:
    print(('%-30s %6s  %s' % (label, p, rest)).rstrip())
