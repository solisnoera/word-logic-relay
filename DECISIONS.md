# Decisions

- GitHub repository `solisnoera/word-logic-relay`, branch `main`, is the project single source of truth. The Site is a deployment target, not an editing source.
- Releases follow `GitHub main -> Site reflection -> post-deployment smoke test`. Fully automatic deployment is intentionally deferred until this manual path has proved reliable.
- The game is a plain static ChatGPT Site, matching the implementation spec's preferred single-file baseline and avoiding framework/runtime overhead.
- The original offline HTML is retained byte-for-byte as a reference snapshot and is not served.
- BOSS, BLIND, TIME, DAILY, duplicate-letter judging, Web Audio feedback, and responsive board mechanics were adapted from the reference.
- The canonical dictionary is generated at development time and embedded in the shipped bundle; gameplay never fetches data.
- No gameplay-critical persistence is used. Daily answers derive from the Japan date and the shipped dictionary version.
