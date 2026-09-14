# WORD LOGIC RELAY v2 — Dictionary Construction Strategy

This document supplements `docs/word-logic-relay-implementation.md` and should be treated as part of the implementation requirements.

## Goal

The dictionary must avoid the common failure mode where obscure or amusing words are accepted while ordinary five-letter words a high-school student would reasonably try are missing.

HARD may contain unusual words. That is intentional. However, ordinary/common vocabulary coverage is higher priority than maximizing obscurity.

## Core rule

Do not build the dictionary by asking an LLM to freely enumerate thousands of words from memory.

Instead:

1. gather multiple suitable public/reference English word lists during development
2. inspect licensing / usage conditions before incorporating data
3. normalize to uppercase A-Z
4. extract exactly five-letter entries by script
5. union these candidates with the existing game vocabulary
6. remove duplicates, proper nouns, abbreviations, junk, obvious variants, and unsuitable entries
7. classify every retained word exactly once as EASY or HARD
8. attach a concise Japanese gloss and optional part of speech
9. run automated consistency checks
10. run a separate common-word coverage audit before release

The finished game must embed its final dictionary locally and must not depend on any of these external sources at runtime.

## EASY coverage priority

EASY should contain ordinary words that a Japanese high-school student or casual English learner might plausibly think of while playing a five-letter word game.

Examples of categories that should be broadly covered:

- everyday nouns: HOUSE, MONEY, WATER, BEACH, PHONE, MUSIC
- basic verbs: WRITE, DRINK, LEARN, TEACH, SPEAK, DRIVE
- common adjectives: HAPPY, SMALL, BLACK, WHITE, CLEAN, SWEET
- common school / life vocabulary
- common animals, food, places, objects, actions, qualities

The exact list is not limited to these examples.

If a common legitimate five-letter word is absent without a deliberate reason, treat that as a dictionary defect.

## HARD policy

HARD should contain only `level: "hard"` entries and must never serve EASY entries as answers.

HARD may include:

- uncommon but legitimate modern words
- literary words
- old-fashioned but still recognizable dictionary words
- botanical / zoological words with some general dictionary presence
- unusual concrete nouns
- uncommon verbs and adjectives
- fun or surprising words

Examples of intended character include QUAFF, MIDGE, SEDGE, SHREW, VIXEN, WHELP, KNAVE, GUILE.

Do not fill HARD with arbitrary dictionary debris. Exclude ultra-obsolete forms, proper nouns, abbreviations, obvious spelling variants used only as artifacts, highly specialist notation, and words whose legitimacy is doubtful.

## Valid guesses

All embedded words are valid guesses.

```text
VALID = EASY ∪ HARD
EASY ∩ HARD = ∅
```

A player may use an EASY word as a guess while playing HARD and vice versa. Difficulty separation applies to answer selection, not input validation.

## Coverage audit

After the first dictionary is built, perform an independent coverage audit.

Do not simply ask the same model to 'think of anything missing'. Use at least one additional general/common English vocabulary reference that was not the sole basis of the initial EASY list.

By script, compute conceptually:

```text
COMMON_REFERENCE_5_LETTER_WORDS - GAME_WORDS
```

Review the resulting missing candidates.

For each plausible common word:

- add it unless there is a concrete reason not to
- classify it EASY or HARD
- attach Japanese meaning data

The purpose of this pass is specifically to catch words omitted because no model or source happened to mention them during initial construction.

## Japanese glosses

Every retained word must have a concise Japanese gloss.

Do not write full dictionary definitions. Use representative meanings suitable for the post-game answer screen.

Where common polysemy matters, include multiple short meanings.

Examples:

```js
{ word: "LIGHT", level: "easy", pos: "noun/adjective", ja: ["光", "明るい", "軽い"] }
{ word: "CRANE", level: "easy", pos: "noun", ja: ["ツル", "クレーン"] }
{ word: "QUAFF", level: "hard", pos: "verb", ja: ["がぶがぶ飲む", "一気に飲む"] }
```

## Efficiency / Work usage

Prefer deterministic tooling over repeated model work.

Use scripts for:

- five-letter filtering
- case normalization
- duplicate removal
- set differences
- EASY/HARD overlap detection
- missing Japanese gloss detection
- schema validation
- sorting / export formatting

Use model reasoning where judgment is useful:

- EASY vs HARD classification
- filtering borderline junk / over-obscure entries
- concise Japanese gloss selection
- reviewing coverage-audit candidates

Batch model work where possible rather than processing one word at a time.

External websites and public datasets may be used during development if they reduce cost or improve coverage, provided their usage terms are checked and the final Site remains runtime-independent.

## Acceptance checks

Before release, verify automatically:

```text
all words match /^[A-Z]{5}$/
no duplicate word keys
level is exactly easy or hard
EASY ∩ HARD = ∅
VALID = EASY ∪ HARD
all ja arrays are non-empty
all answer candidates exist in WORDS
```

Also verify manually / semi-automatically that:

- common five-letter words are not obviously missing
- HARD still contains enough interesting uncommon vocabulary
- there are no obvious proper nouns / abbreviations / junk entries
- the dictionary is large enough for repeated play without frequent repetition

## Priority order

When trade-offs occur, use this order:

1. ordinary-word coverage
2. correctness / legitimacy of entries
3. answer-pool variety
4. interesting HARD obscurity
5. raw dictionary size

A dictionary with 2,000 good words and strong common-word coverage is preferable to a 10,000-word list full of gaps and junk.

