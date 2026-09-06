# Game log

One file per ROM disassembled, recording what that game taught the skill.

The point is not to document each game for its own sake. It is that the
procedure in `SKILL.md` is general but the *patterns* are a growing list, and
the only way the list grows is if each new game's surprises get written down.

Most valuable of all is a game that **contradicts** an earlier one. The second
game here disagreed with the first about text encoding, entropy meaning,
checksums and cross-version diffing, and each disagreement turned a rule into a
game-dependent check. Record disagreements first.

When you finish a game, add a file here with:

* what the engine's dispatch idioms turned out to be, and whether they were
  already in `references/idioms.md`
* how text was encoded, and anything the text reference did not predict
* what cost you the most time, and what would have found it sooner
* which of this skill's claims turned out to be wrong for this game

Then fold the general parts back into `references/`, and add any new dispatch
idiom to `scripts/trace.py`.
