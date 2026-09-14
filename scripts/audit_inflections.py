#!/usr/bin/env python3
"""Audit simple inflectional forms in the shipped five-letter dictionary."""
from __future__ import annotations

import json
import re
import string
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORDS_PATH = ROOT / "dist" / "assets" / "words.js"
EJDICT_REV = "5e1a630bfabb2791a78d14e4e356d85bb6437e34"
EJ_SRC = f"https://raw.githubusercontent.com/kujirahand/EJDict/{EJDICT_REV}/src/{{letter}}.txt"


def request_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "word-logic-relay-inflection-audit/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read().decode("utf-8")


def load_words() -> list[str]:
    source = WORDS_PATH.read_text()
    match = re.search(r"window\.WORD_DATA=(\[[\s\S]*\]);", source)
    if not match:
        raise RuntimeError("Dictionary payload not found")
    return [entry[0].lower() for entry in json.loads(match.group(1))]


def load_ejdict_heads() -> set[str]:
    heads: set[str] = set()
    for letter in string.ascii_lowercase:
        for line in request_text(EJ_SRC.format(letter=letter)).splitlines():
            if "\t" not in line:
                continue
            head, _ = line.split("\t", 1)
            for variant in head.split(","):
                word = variant.strip().lower()
                if re.fullmatch(r"[a-z]+", word):
                    heads.add(word)
    return heads


def plural_base(word: str, lexicon: set[str]) -> str | None:
    # Prefer plain -s first: SHOES -> SHOE, WEEKS -> WEEK.
    if word.endswith("s") and not word.endswith("ss") and word[:-1] in lexicon:
        return word[:-1]
    # -es after sibilants etc.: BOXES -> BOX, BUSES -> BUS.
    if word.endswith("es") and word[:-2] in lexicon:
        return word[:-2]
    # consonant+y -> -ies: FLIES -> FLY.
    if word.endswith("ies") and (word[:-3] + "y") in lexicon:
        return word[:-3] + "y"
    # common f/fe -> ves spelling alternation.
    if word.endswith("ves"):
        for base in (word[:-3] + "f", word[:-3] + "fe"):
            if base in lexicon:
                return base
    return None


def past_base(word: str, lexicon: set[str]) -> str | None:
    # consonant+y -> -ied: TRIED -> TRY.
    if word.endswith("ied") and (word[:-3] + "y") in lexicon:
        return word[:-3] + "y"
    # verbs ending in e take -d: LOVED -> LOVE.
    if word.endswith("d") and word[:-1] in lexicon:
        return word[:-1]
    # ordinary -ed: ASKED -> ASK, ADDED -> ADD.
    if word.endswith("ed") and word[:-2] in lexicon:
        return word[:-2]
    return None


def ing_base(word: str, lexicon: set[str]) -> str | None:
    if not word.endswith("ing"):
        return None
    stem = word[:-3]
    if stem in lexicon:
        return stem
    # silent-e deletion: USING -> USE.
    if (stem + "e") in lexicon:
        return stem + "e"
    # ie -> y: DYING -> DIE, LYING -> LIE, TYING -> TIE.
    if word.endswith("ying") and (word[:-4] + "ie") in lexicon:
        return word[:-4] + "ie"
    # doubled final consonant, included for completeness.
    if len(stem) >= 2 and stem[-1] == stem[-2] and stem[:-1] in lexicon:
        return stem[:-1]
    return None


def main() -> None:
    words = load_words()
    lexicon = load_ejdict_heads()
    plural = [(w.upper(), b.upper()) for w in words if (b := plural_base(w, lexicon))]
    past = [(w.upper(), b.upper()) for w in words if (b := past_base(w, lexicon))]
    ing = [(w.upper(), b.upper()) for w in words if (b := ing_base(w, lexicon))]
    union = {w for w, _ in plural + past + ing}
    print(json.dumps({
        "dictionary_total": len(words),
        "plural_or_3sg_candidates": len(plural),
        "past_or_participle_candidates": len(past),
        "ing_candidates": len(ing),
        "unique_inflected_candidates": len(union),
        "plural_examples": plural[:80],
        "past_examples": past[:80],
        "ing_examples": ing[:80],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
