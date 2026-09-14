# Dictionary construction and coverage audit

Generated from deterministic set operations on 2026-09-14.

## Shipped dictionary

- EASY: 705
- HARD: 777
- Total valid guesses / answer candidates: 1482
- Every entry has an embedded Japanese gloss and part-of-speech label.

## Construction sources

- Existing game vocabulary in the preserved reference snapshot.
- `tabatkins/wordle-list` (MIT) as a validity candidate source.
- `alex1770/wordle` hidden-answer list (MIT) as a validity candidate source.
- JMdict common English subset via `scriptin/jmdict-simplified` for development-time Japanese-gloss candidates (CC BY-SA 4.0 / EDRDG terms). Reviewed overrides improve common or ambiguous mappings. The derived gloss data is distributed under CC BY-SA 4.0.

The sources above are development inputs only. The Site ships one local generated dictionary and performs no runtime lookups.

## Independent common-word coverage audit

The first 3,000 entries of `first20hours/google-10000-english`'s no-swear list were filtered to exactly five A-Z letters and compared against the game dictionary. This source is used as an audit reference only; it is not redistributed. Its own license warns against commercial redistribution.

- Five-letter audit reference entries: 480
- Covered after audit: 439
- Reviewed explicit exclusions (proper names, brands, unsuitable vocabulary): 23
- Not present in either Wordle validity source: 18
- Remaining plausible/valid candidates not added: 0

Remaining candidates: none

## Invariants

The release validator verifies uppercase five-letter spelling, unique keys, exact EASY/HARD classification, non-empty Japanese glosses, disjoint answer pools, dictionary-derived valid guesses, dictionary size, required common coverage, and required HARD examples.
