#!/usr/bin/env python3
"""Build the answer-exclusion list for transparent inflectional forms.

All dictionary entries remain valid guesses. Regular plural/3sg, regular past/
participle, and -ing forms are excluded from answer pools unless EJDict lists
that exact lowercase form as an independent lexical headword with a semantic
sense rather than only an inflection/cross-reference note.
"""
from __future__ import annotations

import json
import re
import string
import urllib.request
from pathlib import Path

from audit_inflections import classify, load_words

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "dist" / "assets" / "answer-exclusions.js"
REPORT_PATH = ROOT / "docs" / "answer-policy-report.md"
EJDICT_REV = "5e1a630bfabb2791a78d14e4e356d85bb6437e34"
EJ_SRC = f"https://raw.githubusercontent.com/kujirahand/EJDict/{EJDICT_REV}/src/{{letter}}.txt"

MORPH_ONLY = (
    "の複数形", "複数形", "の過去形", "過去形", "の過去・過去分詞", "過去・過去分詞",
    "の過去分詞", "過去分詞", "の現在分詞", "現在分詞", "の動名詞", "動名詞",
    "三人称単数", "3人称単数", "三単現",
)


def request_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "word-logic-relay-answer-policy/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read().decode("utf-8")


def load_exact_ejdict() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for letter in string.ascii_lowercase:
        for line in request_text(EJ_SRC.format(letter=letter)).splitlines():
            if "\t" not in line:
                continue
            head, meaning = line.split("\t", 1)
            for variant in head.split(","):
                token = variant.strip()
                # Lowercase-only matters: uppercase proper names/acronyms do not
                # make a transparent inflection an independent general word.
                if re.fullmatch(r"[a-z]+", token):
                    result.setdefault(token, []).append(meaning.strip())
    return result


def independent_semantic_sense(meanings: list[str]) -> bool:
    for raw in meanings:
        for segment in re.split(r"\s+/\s+", raw):
            text = segment.strip()
            if not text or text.startswith("="):
                continue
            if any(marker in text for marker in MORPH_ONLY):
                continue
            # A genuine semantic segment normally contains Japanese text. This
            # rejects bare redirects and morphology labels while keeping entries
            # such as goods, pants, tired, being, icing, etc.
            if re.search(r"[ぁ-んァ-ヶ一-龯々]", text):
                return True
    return False


def main() -> None:
    words = load_words()
    groups = classify(words)
    simple_pairs: dict[str, list[tuple[str, str]]] = {}
    for category in ("regular_plurals", "regular_pasts", "ing_forms"):
        for word, lemma in groups[category]:
            simple_pairs.setdefault(word, []).append((category, lemma))

    ejdict = load_exact_ejdict()
    kept_independent: list[str] = []
    excluded: list[str] = []
    for word in sorted(simple_pairs):
        meanings = ejdict.get(word.lower(), [])
        if independent_semantic_sense(meanings):
            kept_independent.append(word)
        else:
            excluded.append(word)

    OUT_PATH.write_text(
        "/* Generated answer exclusions: valid guesses, not answer candidates. */\n"
        "window.ANSWER_EXCLUSIONS=" + json.dumps(excluded, ensure_ascii=False, separators=(",", ":")) + ";\n"
    )

    def fmt(items: list[str]) -> str:
        return ", ".join(items) if items else "none"

    REPORT_PATH.write_text(f"""# Answer eligibility policy

All {len(words):,} embedded words remain valid guesses.

Transparent inflectional forms are not used as answer candidates unless the exact lowercase form has an independent semantic headword in pinned EJDict `{EJDICT_REV}`.

- Simple inflection candidates inspected: {len(simple_pairs)}
- Excluded from answer pools: {len(excluded)}
- Retained as independent lexical headwords: {len(kept_independent)}
- Irregular plurals and irregular past/participle forms: not filtered by this policy

## Excluded (guess-only)

{fmt(excluded)}

## Retained despite inflectional analysis

{fmt(kept_independent)}

## Policy

- Regular plural / third-person `-s/-es` forms: guess-only unless independently lexicalized.
- Regular past / participle `-ed` forms: guess-only unless independently lexicalized.
- `-ing` forms: guess-only unless independently lexicalized.
- Exact lowercase EJDict headword plus a direct semantic gloss is required to retain an otherwise transparent inflection as an answer.
- Uppercase proper-name or acronym entries do not qualify as independent general-word headwords.
""")

    print(json.dumps({
        "dictionary_total": len(words),
        "simple_inflection_candidates": len(simple_pairs),
        "answer_excluded": len(excluded),
        "retained_independent": len(kept_independent),
        "excluded": excluded,
        "retained": kept_independent,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
