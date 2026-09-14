# Dictionary construction and coverage audit

Generated from deterministic set operations on 2026-09-14 and revised by a curated metadata quality pass on 2026-09-15.

## Shipped dictionary

- EASY: 769
- HARD: 713
- Total valid guesses / answer candidates: 1482
- Every entry has an embedded Japanese gloss and part-of-speech label.
- The word set itself remains unchanged from the published 1482-word baseline.

## Construction sources

- Existing game vocabulary in the preserved reference snapshot.
- `tabatkins/wordle-list` (MIT) as a validity candidate source.
- `alex1770/wordle` hidden-answer list (MIT) as a validity candidate source.
- JMdict common English subset via `scriptin/jmdict-simplified` for development-time Japanese-gloss candidates (CC BY-SA 4.0 / EDRDG terms).

The sources above are development inputs only. The Site ships local dictionary assets and performs no runtime lookups.

## Curated metadata quality pass

The original reverse-JMdict generation occasionally selected an awkward secondary sense or an incorrect part of speech. The release now loads `dist/assets/metadata-fixes.js` after the generated `words.js` and before `game.js`.

This correction layer:

- repairs 372 entries with clearly wrong, misleading, awkward, or school-inappropriate POS/Japanese glosses;
- moves 64 obvious school/general vocabulary items from HARD to EASY without changing valid-guess coverage;
- removes generic `word` POS labels from the corrected release data;
- replaces inappropriate result-screen glosses such as slangy or insulting Japanese where a neutral definition is available;
- keeps the complete 1482-word valid-guess set unchanged.

Examples of corrected metadata include `CHEEK = 頬`, `DIRTY = 汚い／汚れた`, `ENTER = verb / 入る・入力する`, `QUEEN = 女王`, `SHEEP = 羊`, `TRASH = ごみ／捨てる`, and `WEIRD = 奇妙な／変な`.

## Independent common-word coverage audit

The first 3,000 entries of `first20hours/google-10000-english`'s no-swear list were filtered to exactly five A-Z letters and compared against the game dictionary. This source is used as an audit reference only; it is not redistributed. Its own license warns against commercial redistribution.

- Five-letter audit reference entries: 480
- Covered after audit: 439
- Reviewed explicit exclusions (proper names, brands, unsuitable vocabulary): 23
- Not present in either Wordle validity source: 18
- Remaining plausible/valid candidates not added: 0

Remaining candidates: none

## Invariants

The release validator evaluates the final post-correction dictionary and verifies uppercase five-letter spelling, unique keys, exact EASY/HARD classification, non-empty Japanese glosses, disjoint answer pools, dictionary-derived valid guesses, total dictionary size, required common coverage, required HARD examples, representative metadata corrections, school-safe gloss checks, correction-asset load order, duplicate-letter judging, TIME bonuses, and zero runtime external calls.
