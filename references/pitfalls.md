# Things that produced wrong answers

Each of these cost real time on the reference game. They are listed as
symptoms, because that is how they present.

**"The patch does nothing."**
The immediate byte of an instruction is its *last* byte, not the address the
disassembler prints. Patching the printed address hits the high half of an
immediate word, which reads `$00` and silently does nothing.

**"This constant is the limit."**
It is one of several. A single logical value existed in seven places on the
reference game: two cursor bounds on one screen, two on another, a modulo in
the CPU's random pick, and two more in a demo path. Search for every site that
compares against the same value before believing you have found the limit.

**"The data is wrong / the translation missed 47 fields."**
An incomplete decoder invents findings. 46 of those 47 were three glyphs
missing from the font map. When a scan reports a pattern of failures in the
data, suspect your own tables first.

**"The routine at this address belongs to that screen."**
Address ranges are not ownership. A routine sitting between two mode handlers
was assumed to belong to the earlier one; the correct owner was the later mode,
and the wrong guess disabled a feature silently.

**"There is 70 KiB of free space."**
Reach is the constraint, not space. Self-relative words and `lea d16(pc)` both
span about +/-32 KiB, so distant free space is unreachable without a
trampoline. Also, runs of `$00` inside the program area may be live data;
only regions cross-checked against the trace are known-free.

**"The table is correct, so it is fixed."**
Verify against observable behaviour, not the artifact you inspected. On the
reference game the name tables were provably correct while every name a player
sees came from art, so the correct data changed nothing on screen.

**"That input was broken, so I worked without it."**
Report every bad file and ask for a replacement, even when the analysis can
proceed. A `.zip` named for a Mega Drive game has contained a Game Boy ROM, and
an `.ips` has been a saved HTML page of a GitHub blob view. In the field an
agent flagged the first, got a corrected file, and quietly dropped the second:
the dropped one was a third translation, which is the single input the text
step benefits from most. Verify size, header and magic bytes on everything
before use.

**"Mid-entropy means code."**
Game-dependent. In one game the middle of the entropy range was mostly code; in
another, 45% of the ROM sat at entropy 3 to 5 and was uncompressed level and
tilemap data plus the script. Read the entropy map against your own trace
coverage, not against a remembered threshold.

**"The boot code checksums the ROM."**
One game did and hung on mismatch; another did not verify it at all. Read the
boot code rather than carrying the assumption between games.

**"Reading the code will tell me."**
Three times, reading gave a confidently wrong answer that one runtime
measurement corrected on the first attempt: which byte held the controller
buttons, which routine a screen actually calls, and which mode value a screen
runs under. When a fact is cheap to measure and expensive to infer, measure it.
