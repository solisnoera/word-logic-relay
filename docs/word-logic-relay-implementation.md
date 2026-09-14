# WORD LOGIC RELAY v2 — Implementation Specification

> Status: implementation-ready handoff document for ChatGPT Work / Codex
> Scope: rebuild the supplied single-file HTML game as a fully self-contained ChatGPT Site with no external API/runtime dependency.

## 1. Product goal

Rebuild **WORD LOGIC RELAY** as a browser-only five-letter word game that keeps the current core play loop and special modes, but removes Datamuse and all other runtime external dependencies.

This is primarily a game, not a study app. Unknown or unusual words are acceptable and desirable in HARD mode, provided they are legitimate modern English words and not so obscure that play becomes arbitrary.

The finished implementation must be usable on iPhone, iPad, and Mac, with Safari treated as a first-class target.

## 2. Source to migrate

The source supplied in the originating ChatGPT conversation is a single HTML file titled `WORD LOGIC RELAY`. It already contains:

- title screen
- EASY / HARD difficulty selector
- NORMAL modes: SOLO / DUO / TRIO / FOUR / FIVE / SIX
- SPECIAL modes: BOSS / BLIND / TIME / DAILY
- responsive board sizing
- onscreen QWERTY keyboard and physical keyboard input
- Wordle-style result judging
- audio feedback using Web Audio
- result overlay
- date-seeded DAILY mode
- current local word arrays
- Datamuse-backed HARD word fetching and unknown-guess verification

The implementation should preserve working game behavior unless this document explicitly changes it.

## 3. Non-negotiable runtime constraints

The finished Site must use **no runtime external dependency**.

Do not use:

- Datamuse
- OpenAI API
- Google APIs
- dictionary APIs
- external JSON
- CDN-hosted JS/CSS
- external fonts
- remote word lists
- runtime `fetch()` for game data

All game data and logic must ship with the Site itself.

The Site host itself obviously requires a network connection to load the page. After the app bundle has loaded, gameplay must require no further network request.

## 4. Word model

Use one canonical embedded dictionary.

Recommended data shape:

```js
const WORDS = [
  {
    word: "APPLE",
    level: "easy",
    pos: "noun",
    ja: ["りんご"]
  },
  {
    word: "QUAFF",
    level: "hard",
    pos: "verb",
    ja: ["がぶがぶ飲む", "一気に飲む"]
  }
];
```

Equivalent compact structures are acceptable if they reduce bundle size or simplify lookup, but there must be one source of truth.

### 4.1 Valid guesses

Every word in `WORDS` is a valid guess.

There is no separate guess-only dictionary.

Formally:

```text
VALID_GUESSES = EASY_WORDS ∪ HARD_WORDS
```

Every valid guess is also an answer candidate in its own difficulty pool.

### 4.2 EASY

EASY answers must be selected only from words marked `easy`.

Typical character:

- common everyday English
- familiar school-level vocabulary
- visually recognizable five-letter words
- fair for casual players

Examples of intended character:

`APPLE`, `HOUSE`, `WORLD`, `LIGHT`, `TRAIN`, `BRAIN`, `MUSIC`

### 4.3 HARD

HARD answers must be selected **only** from words marked `hard`.

EASY words must never appear as HARD answers.

HARD is not an educational level such as Eiken Grade Pre-1. It is a game difficulty pool and may deliberately contain uncommon, odd, literary, zoological, botanical, archaic-looking, or otherwise surprising words.

Good HARD character includes words like:

`ACRID`, `GUILE`, `KNAVE`, `MIDGE`, `QUAFF`, `SEDGE`, `SHREW`, `VIXEN`, `WHELP`

This list is illustrative, not exhaustive.

Exclude or strongly avoid:

- proper nouns
- abbreviations and initialisms
- obvious typos / variant garbage
- words whose legitimacy depends on highly specialist jargon with essentially no general dictionary presence
- ultra-obsolete forms that would feel random rather than difficult
- slurs / hateful epithets
- explicit sexual vocabulary unsuitable for a general casual game

The goal is **interesting obscurity**, not arbitrary dictionary debris.

## 5. Japanese meaning data

Every dictionary entry must include a concise Japanese gloss.

Requirements:

- one or more representative meanings
- preserve genuinely common polysemy where useful
- do not attempt exhaustive dictionary definitions
- use natural Japanese
- meaning text should be short enough for a result card
- part of speech may be stored even if not always displayed

Examples:

```js
{ word: "CRANE", level: "easy", pos: "noun", ja: ["ツル", "クレーン"] }
{ word: "LIGHT", level: "easy", pos: "noun/adjective", ja: ["光", "明るい", "軽い"] }
{ word: "MIDGE", level: "hard", pos: "noun", ja: ["小さな羽虫"] }
```

Meaning data must be embedded locally and available instantly with no API lookup.

## 6. Result / definition interaction

During play, do not reveal Japanese meanings.

After the run ends, show all answer words.

Default result view should remain compact. The preferred interaction is:

1. show answer words as cards/chips
2. tap/click a word
3. expand or open a small definition panel containing the Japanese gloss and optionally part of speech

Example:

```text
CLEAR
8 / 11

[ QUAFF ] [ MIDGE ] [ VIXEN ] ...

Tap QUAFF
→ QUAFF
  verb
  がぶがぶ飲む／一気に飲む
```

Do not add persistent REVIEW, favorites, streaks, word history, or other features that require dependable localStorage persistence.

## 7. Persistence

The core game must not depend on `localStorage`, IndexedDB, D1, cookies, or account state.

No gameplay-critical information should need to survive a page reload.

DAILY remains deterministic from the date and embedded dictionary, so it does not need storage.

Transient in-memory state is sufficient.

## 8. Modes to preserve

### NORMAL RUN

Preserve:

- SOLO — 1 answer / 6 guesses
- DUO — 2 answers / 7 guesses
- TRIO — 3 answers / 8 guesses
- FOUR — 4 answers / 9 guesses
- FIVE — 5 answers / 10 guesses
- SIX — 6 answers / 11 guesses

A submitted guess applies simultaneously to every unsolved board.

### BOSS

Preserve the existing six-board special run and existing shield / sealed-letter mechanic unless inspection finds a clear bug.

Target: 6 words / 12 guesses.

### BLIND

Preserve the existing behavior in which non-green information fades / is veiled after the guess animation.

Target: 4 words / 10 guesses.

### TIME

Preserve the current timed four-board mode and current bonus behavior for solved boards unless inspection finds a clear bug.

Target: 4 words / 9-row board.

Current source starts at 180 seconds and adds 10 seconds per board solved; keep this unless a concrete usability reason emerges during testing.

### DAILY

Preserve a deterministic four-word run based on the Japan date.

DAILY must always use the EASY answer pool.

Same Japan calendar day + same shipped dictionary version => same answers for all users.

Target: 4 words / 9 guesses.

## 9. Word judging

Keep standard Wordle-style duplicate-letter accounting:

1. mark exact-position matches first
2. consume those target letters
3. then mark present-but-wrong-position matches only while unused instances remain
4. mark remaining letters absent

Add tests for repeated letters, e.g. targets / guesses containing duplicated vowels or consonants.

## 10. Input validation

Submission rules:

1. exactly five A-Z letters required
2. uppercase internally
3. accept only if the word exists in the canonical embedded dictionary
4. otherwise reject instantly with `Not in word list.` or equivalent

There must be no async network validation and no artificial loading state.

## 11. Remove old API architecture

Delete or replace all logic corresponding to:

- Datamuse URL construction
- `fetch()` word calls
- HARD cache population from Datamuse
- unknown-word API verification
- network error fallback state
- `localOnly`
- `VERIFY_UNKNOWN_GUESSES_WITH_API`
- `buildPatterns()` used for Datamuse retrieval
- `warmPrepareWords()` if it has no remaining purpose
- `prepareWords()` async fetching architecture if it has no remaining purpose
- `hardAnswerCache` as a network cache
- UI strings containing `Datamuse`, `API`, `local fallback`, `HARD unavailable`, or `Checking word...`

Where possible, simplify `startGame()` and `submitGuess()` back to synchronous local operations.

## 12. UI redesign permission

The current wood / brass / dark game identity may be retained, but UI is explicitly allowed to change when usability improves.

Priorities, in order:

1. board readability
2. touch target size
3. keyboard usability
4. immediate understanding of current mode / remaining guesses
5. responsive fit on iPhone and iPad
6. visual style

### 12.1 Title screen

Recommended hierarchy:

```text
WORD LOGIC
FIVE LETTER RELAY

DIFFICULTY
[ EASY ] [ HARD ]

NORMAL
[ SOLO ] [ DUO ] [ TRIO ]
[ FOUR ] [ FIVE ] [ SIX ]

SPECIAL
[ BOSS ] [ BLIND ] [ TIME ] [ DAILY ]
```

Remove implementation-detail text from the player UI.

Difficulty subtitles can be concise, e.g.:

- EASY — COMMON WORDS
- HARD — OBSCURE WORDS

Avoid long explanatory copy on the main screen.

### 12.2 Game screen

The board area should receive as much vertical space as possible.

Remove nonessential side-panel implementation status such as word-cache counts.

Keep only player-relevant information such as:

- difficulty + mode
- try count / timer
- short message feedback
- board(s)
- keyboard
- title/quit control

### 12.3 Responsive behavior

Must be deliberately tested at least at representative sizes for:

- small iPhone portrait
- modern iPhone portrait
- iPhone landscape if practical
- 11-inch iPad portrait
- 11-inch iPad landscape
- Mac desktop browser

For 5- and 6-board modes, prioritize legibility. Controlled board-area scrolling is acceptable if fitting everything would make tiles unreasonably small.

Do not allow the virtual keyboard to become unusably tiny merely to force all boards into one viewport.

### 12.4 Result screen

Provide at least:

- CLEAR / FAILED / TIME UP as appropriate
- guesses used or run result
- all target words
- tap/click definition interaction
- `PLAY AGAIN`
- `CHANGE MODE` or equivalent route back to selection
- `TITLE`

The exact button naming may change for clearer UX.

## 13. Loading behavior

Remove the current word-gathering loading overlay from ordinary game start.

Starting a mode should be effectively immediate because all data is local.

If the framework/Site build itself needs an initial render state, it must not imply that remote words are being fetched.

## 14. Audio

Keep the current lightweight Web Audio feedback if it works reliably on Safari.

Requirements:

- audio must unlock only after a user gesture as required by Safari
- audio failure must never block gameplay
- do not add remote audio assets

## 15. Accessibility / interaction quality

At minimum:

- buttons need readable labels
- sufficient contrast in the existing dark theme
- keyboard/touch targets should be comfortably tappable
- color must not be the only mechanism for critical controls
- animation must not prevent reading results
- do not rely on hover

No major accessibility framework is required; this is a compact game.

## 16. Suggested internal architecture

A single-file HTML implementation is acceptable and is the preferred baseline if ChatGPT Site packaging permits it cleanly.

Suggested logical sections:

```text
HTML
  title screen
  game screen
  result modal/panel

CSS
  tokens/theme
  title
  board
  keyboard
  result/definition
  responsive rules

JS
  WORDS data
  derived EASY/HARD maps/sets
  state
  game initialization
  answer selection
  daily seeded selection
  input
  validation
  judging
  board rendering
  special-mode mechanics
  result rendering
  definition interaction
  audio
  responsive sizing
```

Derived structures should be created once at boot, e.g.:

```js
const WORD_BY_TEXT = new Map(WORDS.map(item => [item.word, item]));
const EASY_WORDS = WORDS.filter(item => item.level === "easy");
const HARD_WORDS = WORDS.filter(item => item.level === "hard");
const VALID_WORDS = new Set(WORD_BY_TEXT.keys());
```

Never duplicate answer data across multiple manually-maintained arrays if it can be derived from `WORDS`.

## 17. Random answer selection

For non-DAILY modes:

- shuffle/select from the current difficulty pool
- no duplicate target within one run
- HARD selection must never fall back to EASY
- if the pool is somehow smaller than board count, fail loudly during development rather than silently duplicate answers

For DAILY:

- use EASY pool only
- seed from Japan date
- deterministic stable shuffle/select

## 18. Dictionary scale

Do not optimize prematurely for a tiny dictionary.

A few thousand five-letter words with short Japanese glosses are acceptable for an embedded Site bundle.

Prioritize dictionary quality over maximizing raw count.

Desired direction:

- EASY: curated common pool large enough to avoid obvious repetition
- HARD: substantial uncommon pool, including fun weird words
- total pool: enough that repeated play remains varied

The exact counts may be chosen during implementation after inspecting bundle size and source quality.

## 19. Dictionary quality workflow

When expanding the current source lists:

1. normalize to A-Z five-letter uppercase entries
2. remove duplicates
3. remove proper nouns / abbreviations / junk
4. classify each retained word exactly once as EASY or HARD
5. attach concise Japanese gloss and optional part of speech
6. perform a consistency validation script/check before shipping

Required invariants:

```text
word.length === 5
word matches /^[A-Z]{5}$/
level is exactly easy or hard
ja exists and is non-empty
no duplicate word keys
EASY ∩ HARD = ∅
VALID = EASY ∪ HARD
```

## 20. Implementation validation

Before publishing, test at minimum:

### Core

- each NORMAL mode starts
- each SPECIAL mode starts
- EASY only draws EASY
- HARD only draws HARD
- any embedded EASY or HARD word is accepted as a guess
- non-dictionary 5-letter strings are rejected immediately
- duplicate-letter judging is correct
- solved boards stop accepting/rendering subsequent current-row input as intended
- all-board clear ends correctly
- exhaustion ends correctly

### Specials

- BOSS sealed letters activate at intended turns
- BLIND hides intended marks only
- TIME countdown and bonus work
- DAILY is stable across reloads on same Japan date

### Definitions

- every result answer has a Japanese gloss
- tapping a word opens the correct gloss
- multiple meanings render cleanly
- definition panel works with 1 through 6 answer words

### UI

- no overflow that hides essential controls
- virtual keyboard remains tappable
- physical keyboard works on desktop
- result controls remain visible
- screen rotation / resize does not corrupt board sizing

### Network

With browser network blocked after initial page load, start and complete runs successfully.

Inspect the built app and confirm there are no game-runtime calls to external APIs/CDNs.

## 21. Acceptance criteria

Implementation is complete only when all are true:

- no Datamuse dependency remains
- no game-runtime external API dependency exists
- EASY and HARD answer pools are fully local and disjoint
- HARD never serves an EASY answer
- every embedded word is a valid guess
- every embedded word carries a Japanese meaning
- result screen can reveal meanings without network access
- no persistent storage is required
- all existing core and special modes remain playable
- iPhone/iPad/Mac Safari layouts are usable
- game start is immediate, with no remote-word loading screen
- Site is published and the published URL is smoke-tested

## 22. Work / Codex execution order

Recommended implementation sequence:

1. obtain the original uploaded single HTML source from the originating conversation/workspace
2. create a new project/repo for WORD LOGIC RELAY rather than modifying the vocabulary app itself
3. preserve original source as a reference snapshot
4. remove Datamuse and network-dependent word handling
5. introduce canonical `WORDS` schema
6. migrate current curated/local words into EASY/HARD entries
7. expand dictionary and attach Japanese glosses
8. add automated consistency validation for dictionary data
9. simplify synchronous start/input/validation flow
10. redesign title/game layout for mobile/tablet usability
11. implement result definition cards
12. regression-test normal and special modes
13. test Safari responsive layouts
14. verify zero runtime third-party requests
15. publish as ChatGPT Site
16. smoke-test published Site
17. record any implementation decisions or discovered pitfalls in project docs (`AGENTS.md`, `DECISIONS.md`, or `LESSONS.md` as appropriate)

## 23. Important product decisions already settled

Do not reopen these unless implementation reveals a concrete blocker:

- external word APIs are removed
- all words are embedded
- answer candidates and valid guesses are the same canonical set
- EASY and HARD answer pools are disjoint
- HARD contains no EASY answers
- HARD may include genuinely odd/uncommon words
- extremely arbitrary/garbage obscurities should still be filtered out
- Japanese meanings are bundled locally
- meanings are shown after the run, not during guessing
- no persistent REVIEW feature
- no gameplay dependence on localStorage / IndexedDB / D1
- UI may be redesigned for usability
- existing game modes and identity should remain recognizable

## 24. Repository note

This document is temporarily stored in `solisnoera/vocabulary-app/docs/` only as a handoff location because the GitHub connector currently exposes no separate WORD LOGIC repository creation action. **Do not implement this game inside `vocabulary-app`.** Work should create or use a dedicated WORD LOGIC repository/project when it begins implementation, then move/copy this specification there.

