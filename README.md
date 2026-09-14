# WORD LOGIC RELAY v2

Dedicated, self-contained implementation of the five-letter relay game. The source specification was copied from `solisnoera/vocabulary-app` Issue #24; that repository remains a handoff location only.

Published Site: https://word-logic-relay-v2.riyo-timid.chatgpt.site

- Runtime: static HTML/CSS/JavaScript
- Dictionary: 1482 embedded local valid words / answer candidates
- Current answer pools: EASY 770 / HARD 712
- Dictionary corrections: `dist/assets/metadata-fixes.js` repairs reviewed POS/Japanese glosses and obvious difficulty classifications without changing the word set
- External runtime calls: none
- Reference snapshot: `reference/original-word-logic-relay.html`

## Source of truth

The `main` branch of this repository is the single source of truth. Do not edit the ChatGPT Site directly. Make and verify changes here first, then publish the same committed revision to the existing Site.

The repository's root commit is the source revision used by the initial published Site version. See `PROJECT_MEMORY.md` for the baseline provenance and release checks, and `docs/dictionary-audit.md` for dictionary construction and metadata-quality details.

## Update and publish workflow

1. Start from the latest `main` and make the required change in this repository.
2. Run `node scripts/validate.mjs` and inspect the changed game flow locally.
3. Commit and push the verified revision to GitHub `main`.
4. In ChatGPT Work, open this repository and the existing Site project identified by `.openai/hosting.json`.
5. Push that exact GitHub `main` revision to the Site source repository, save a Site version from the same commit, and deploy it without changing the current audience.
6. After deployment, smoke-test the public URL: title screen, EASY/HARD selection, at least one normal mode, keyboard input, result display/definitions, and browser console/network errors.
7. Record any lasting design decision or deployment lesson in `DECISIONS.md` or `PROJECT_MEMORY.md`.

Run validation with:

```sh
node scripts/validate.mjs
```
