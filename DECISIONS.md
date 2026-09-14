# Decisions

- GitHub repository `solisnoera/word-logic-relay`, branch `main`, is the project single source of truth. The Site is a deployment target, not an editing source.
- Releases follow `GitHub main -> Site reflection -> post-deployment smoke test`. Fully automatic deployment is intentionally deferred until this manual path has proved reliable.
- The game is a plain static ChatGPT Site, matching the implementation spec's preferred single-file baseline and avoiding framework/runtime overhead.
- The original offline HTML is retained byte-for-byte as a reference snapshot and is not served.
- BOSS, BLIND, TIME, DAILY, duplicate-letter judging, Web Audio feedback, and responsive board mechanics were adapted from the reference.
- The canonical dictionary is generated at development time and embedded in the shipped bundle; gameplay never fetches data.
- Dictionary coverage and dictionary metadata are treated separately. The original 1,482-word baseline is pinned; the deterministic expansion pipeline builds the current 2,634-word dictionary from that baseline rather than growing cumulatively from the latest generated asset.
- EASY classification is deliberately conservative. Ordinary words classified as HARD remain valid guesses, because valid guesses are the union of EASY and HARD; a word should not be promoted into EASY merely to satisfy a count target.
- EJDict direct English-to-Japanese data is preferred for expansion glosses. Part of speech is optional when it cannot be resolved confidently; an omitted POS is preferable to a guessed or misleading one.
- `dist/assets/metadata-fixes.js` continues to apply reviewed baseline POS/Japanese-gloss corrections and obvious EASY/HARD classification fixes before game startup.
- School/general-audience result glosses should use neutral, representative Japanese. Awkward reverse-dictionary senses, insulting Japanese, or generic `word` POS labels are release regressions and are checked by `scripts/validate.mjs`.
- Expansion candidates without a concise school-safe Japanese gloss are skipped even when the English word itself is valid. Coverage quality has priority over reaching an arbitrary maximum word count.
- DAILY uses a dictionary-version seed; dictionary-content changes intentionally change the daily puzzle generation version.
- No gameplay-critical persistence is used. Daily answers derive from the Japan date and the shipped dictionary version.
