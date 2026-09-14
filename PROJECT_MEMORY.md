# Project memory

## Baseline

- Public Site: https://word-logic-relay-v2.riyo-timid.chatgpt.site
- Site project: the existing project referenced by `.openai/hosting.json`
- Initial Site version: 1
- Initial Site source commit: `5f40fd154820907dd51df756225b46b7204435a6`
- Initial Site archive hash: `sha256:564ac9bddaf314dfff62d355f0b4415cffa93c090c1868a969a2edb7afe89e7e`
- Dictionary at baseline: 1,482 entries (EASY 705; HARD 777)

The initial Site source repository was cloned directly and its HEAD matched the commit recorded for published Site version 1. That root commit is retained as the immutable release baseline. Later documentation commits do not alter the files served from `dist/`.

## GitHub cutover

- GitHub repository: `solisnoera/word-logic-relay` (public)
- GitHub baseline commit: `169db1b1d84366593c0dd82d299169fd20db0ca9`
- GitHub expanded-source/workflow commit: `103d71b79ecf12f4dbec231ff307921f492fb7a4`
- Site version 2 was saved and deployed from commit `103d71b79ecf12f4dbec231ff307921f492fb7a4`.

The GitHub root commit stores the complete Site version 1 source as `baseline/word-logic-relay-v2-source.tar.gz.base64`. Decoding and extracting that file reproduces the 18-file source tree of Site version 1 exactly. The next commit expands the source into the normal repository layout and adds the GitHub-first workflow documentation. From the cutover onward, the exact GitHub `main` commit is pushed to the Site source repository before a Site version is saved.

Post-deployment comparison confirmed that the public `game.js`, `styles.css`, and `words.js` were byte-identical to GitHub `main`. The public `index.html` was identical after removing Cloudflare's response-time challenge script injection.

## Release invariants

- `dist/` is the deployed static directory.
- `dist/assets/words.js` is the canonical embedded runtime dictionary.
- `reference/original-word-logic-relay.html` remains unchanged.
- The runtime remains self-contained and performs no external network calls.
- A release is complete only after validation, deployment of the intended commit, and a public smoke test.

## Baseline release checksums

```text
806fa0ed8ecd44f0fc18e63f95c51ae01df992161fb8d91226826f51c8a13f3d  dist/index.html
e250971fc79aaa1b776d0a48427d9f1439fd3839d9aa91c8b446fb79bb253e24  dist/assets/game.js
387f650b3db79b746bc447b9036c2cb1a415230bd6a92ca285231234e9edc6f5  dist/assets/styles.css
aa53301bf80094d9593b02533ad47a86cf83f0c478239e192d6017662d80d7c6  dist/assets/words.js
3e6e56c8c65f20a6455ed55a5ca5a8ded73bedb536a72312ffd92aa67d8c3d51  .openai/hosting.json
```
