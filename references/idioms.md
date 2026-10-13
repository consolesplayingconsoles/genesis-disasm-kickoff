# Dispatch idioms

A first trace stalls wherever control flow goes through data. Each shape below,
once taught to the tracer, converts a whole class of dead ends into coverage.

**Observed in three games so far**, by different developers. Only one shape
appeared in both, which is the point: expect shapes not listed here. The
recognition method at the bottom matters more than the list.

## 1. bra.w slot table

```
move.w  var, d0
andi.w  #$fffc, d0
jsr     table(pc, d0.w)
...
table:  bra.w  case_0
        bra.w  case_1
```

Four bytes per slot, each a `bra.w` (`$6000`). Walk slots while the opcode is
`$6000` and the target lands in ROM. The base may point a slot or two before
the first entry, so scan forward for the first `$6000`.

Used for top-level game modes on the reference game.

## 1b. Computed jump into unrolled code

Looks identical to a trampoline table at the call site:

```
        <index in dn, doubled>
        jmp     base(pc,dn.w)
base:   move.l  (a0)+,(a2)+     ; the same instruction, written out N times
        move.l  (a0)+,(a2)+
        ...
        rts
```

`base` is **not a table, it is code**: an unrolled copy or fill loop. Jumping
partway in skips the first k iterations, which is how you get a variable-length
copy with no loop overhead.

Mistaking this for a table produces garbage entries and false code. The test is
cheap: if the first word at `base` is not the table idiom's own signature
(`$6000` for a trampoline table), it is ordinary code. Let linear decode run
through it and move on.

Seen twice in one game, for a block copy (`move.l (a0)+,(a2)+`) and a block
fill (`move.l d7,(a1)+`, with the pattern preloaded by the caller).

## 2. Self-relative word table

```
lea     base(pc, d0.w), a0
adda.w  (a0), a0
jsr     (a0)
```

Each entry is a signed word. **The origin varies and must be read off the
code**: in one game the target was the entry's own address plus the word, and
in another it was the table's base address plus the word:

```
        lea     table,a0
        adda.w  (a0,dn.w),a0    ; target = table_base + sign16(word)
        jmp     (a0)
```

Both are "self-relative word tables" and they resolve differently. Take the
origin from the instruction that performs the addition, never from the shape of
the data.

Where the origin is the entry, entries of `$0000` are unused slots, not the end of the table. Stop on
a run of entries whose targets fail a plausibility check, not on the first.

This was the dominant idiom on the reference game, in both code and data. It is
worth checking for first: resolving it took coverage from 0.2% to nearly all
the code.

Variants seen:
* `lea base(pc), a0` then `adda.w d0, a0` then `adda.w (a0), a0`
* `lea base.l, a0` (absolute long) with the same tail
* an intermediate byte table: `move.b (a0,d0.w), d0` gives a slot number that
  then indexes the word table

## 3. Longword pointer table

```
movea.l table(pc, d0.w), a0
jsr     (a0)
```

Plain 32-bit pointers. Read while entries are even and inside the ROM. A zero
entry can mean "this slot is disabled" rather than end of table; check how the
caller treats it before trusting either reading.

## 3b. Keyed table

```
lea     table(pc), a0
loop:   addq.w #4, a0 ; move.w (a0), d1 ; bmi done   ; negative key ends it
        ...           ; match when 0 <= value - key < k
addq.w  #2, a0
adda.w  (a0), a0
jsr     (a0)
```

`[key.w][self-relative offset.w]` pairs: the handler is the offset word's own
address plus its value.

## 3c. Fetch-then-add word table

```
lea     table(pc, d0.w), a2
move.w  (a2), d0
lea     table(pc), a2
adda.l  d0, a2
jsr     (a2)
```

Idiom 2 measured from the base, with the add coming from a data register.

## Where a table ends

A table cannot run into its own handlers: stop at the first address an entry
already points at. A `nop ; rts` (`$4E714E75`) slot in a `bra.w` table, and a
handler that is a lone `rts`, are empty entries, not the end.

## Bounding a table's length

Almost never stored. Two approaches, in order of reliability:

1. **Recover the index range from the code that built it.** The `andi.w #mask`
   instructions that clamp the index give you the bound directly: OR the masks
   together and divide by the entry stride. This is the only sound method when
   the index is built from two fields, such as a state in the high bits and an
   event in the low bits.
2. **Read entries while they still match the idiom's signature.** Fine for a
   trampoline table, where every entry must begin `$6000`. Weak for raw
   displacement tables, where plausible-looking values continue past the end.

## Recognising a new one

The tracer should print every `jsr`/`jmp` it could not resolve. For each:

1. Disassemble backwards about 8 instructions from the site.
2. Look for what loaded the address register: a `lea` of a table, an index
   computed from a variable, an `adda` chain.
3. The scale factor tells you the entry size: `add.w d0,d0` means words,
   `lsl.w #2` means longs, `mulu #18` means an 18-byte record.
4. Confirm by walking the table and checking every target decodes as plausible
   code before adding it to the tracer.

Do not seed speculatively. False code is worse than a gap, because it
contaminates every later pass.
