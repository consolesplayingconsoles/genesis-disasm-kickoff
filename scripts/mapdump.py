#!/usr/bin/env python3
"""Coarse ROM content map: 4 KiB blocks classed by entropy, 68k decodability and zero fill,
collapsed into runs, each printed with its class, size and mean entropy (bits per byte).
"""
import sys, math, collections
from capstone import *
ROM=open(sys.argv[1],'rb').read(); N=len(ROM); B=0x1000
md=Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN|CS_MODE_M68K_000)

def ent(b):
    c=collections.Counter(b); n=len(b)
    return -sum(v/n*math.log2(v/n) for v in c.values())

def decodable(b, base):
    """fraction of bytes covered by a clean linear 68k sweep from offset 0"""
    ok=0; pc=0
    while pc < len(b)-16:
        try: ins=next(md.disasm(b[pc:pc+16], base+pc, count=1))
        except StopIteration: pc+=2; continue
        ok+=ins.size; pc+=ins.size
    return ok/len(b)

rows=[]
for off in range(0,N,B):
    blk=ROM[off:off+B]
    rows.append((off, ent(blk), decodable(blk,off), blk.count(0)/len(blk)))

# collapse into runs by class
def cls(e,d,z):
    if z>0.9 or e<0.5: return 'empty'   # zeros, or one byte repeated ($FF fill)
    if e>7.4: return 'packed'      # compressed / dense art
    if d>0.985 and e<7.0: return 'code?'
    return 'data'
prev=None; start=0; es=[]
def show(a, b, c):
    print('%06X-%06X  %-7s %4d KiB  entropy %.2f'%(a,b,c,(b+1-a)//1024,sum(es)/len(es)))
for i,(off,e,d,z) in enumerate(rows):
    c=cls(e,d,z)
    if c!=prev:
        if prev is not None: show(start,off-1,prev)
        prev=c; start=off; es=[]
    es.append(e)
show(start,N-1,prev)
