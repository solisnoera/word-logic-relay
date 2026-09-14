# Project instructions

- Treat GitHub `main` in `solisnoera/word-logic-relay` as the single source of truth.
- Never make an authoritative change directly in the ChatGPT Site checkout. Apply and commit it here first.
- Publish in this order: GitHub `main` -> existing Site project -> production smoke test.
- Reuse the `project_id` in `.openai/hosting.json`; never create a replacement Site for routine updates.
- Before deployment, verify that the Site source commit and the intended GitHub `main` tree contain the same release files.
- Treat the copied files in `docs/` as the product specification.
- Keep `reference/original-word-logic-relay.html` unchanged.
- The published game must remain fully self-contained: no fetch, XHR, WebSocket, external fonts, scripts, styles, images, or APIs at runtime.
- Run `node scripts/validate.mjs` after dictionary or game logic changes.
- Preserve EASY/HARD disjointness and Japanese gloss coverage.
