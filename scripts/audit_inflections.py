#!/usr/bin/env python3
"""Audit regular inflectional forms in the shipped five-letter dictionary."""
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
    req = urllib.request.Request(url, headers={"User-Agent": "word-logic-relay-inflection-audit/1.1"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read().decode("utf-8")


def load_words() -> list[str]:
    source = WORDS_PATH.read_text()
    match = re.search(r"window\.WORD_DATA=(\[[\s\S]*\]);", source)
    if not match:
        raise RuntimeError("Dictionary payload not found")
    return [entry[0].lower() for entry in json.loads(match.group(1))]


def load_ejdict_lexicon() -> tuple[set[str], set[str], set[str]]:
    heads: set[str] = set()
    countable_nouns: set[str] = set()
    verbs: set[str] = set()
    for letter in string.ascii_lowercase:
        for line in request_text(EJ_SRC.format(letter=letter)).splitlines():
            if "\t" not in line:
                continue
            head, meaning = line.split("\t", 1)
            for variant in head.split(","):
                word = variant.strip().lower()
                if not re.fullmatch(r"[a-z]+", word):
                    continue
                heads.add(word)
                if "〈C〉" in meaning:
                    countable_nouns.add(word)
                if "{動}" in meaning:
                    verbs.add(word)
    return heads, countable_nouns, verbs


def plural_base(word: str, nouns: set[str]) -> str | None:
    # spelling alternations first
    if word.endswith("ies") and (word[:-3] + "y") in nouns:
        return word[:-3] + "y"
    if word.endswith("ves"):
        for base in (word[:-3] + "f", word[:-3] + "fe"):
            if base in nouns:
                return base
    # plain -s: WEEKS -> WEEK, SHOES -> SHOE
    if word.endswith("s") and not word.endswith("ss") and word[:-1] in nouns:
        return word[:-1]
    # -es: BOXES -> BOX, BUSES -> BUS
    if word.endswith("es") and word[:-2] in nouns:
        return word[:-2]
    return None


def past_base(word: str, verbs: set[str]) -> str | None:
    if word.endswith("ied") and (word[:-3] + "y") in verbs:
        return word[:-3] + "y"
    if not word.endswith("ed"):
        return None
    # silent-e verbs take only -d: MOVED -> MOVE
    if word[:-1].endswith("e") and word[:-1] in verbs:
        return word[:-1]
    # ordinary -ed: ASKED -> ASK, ADDED -> ADD
    if word[:-2] in verbs:
        return word[:-2]
    return None


def ing_base(word: str, verbs: set[str]) -> str | None:
    if not word.endswith("ing"):
        return None
    stem = word[:-3]
    if stem in verbs:
        return stem
    # ie -> y must be checked before generic silent-e restoration.
    if word.endswith("ying") and (word[:-4] + "ie") in verbs:
        return word[:-4] + "ie"
    # silent-e deletion: USING -> USE, AGING -> AGE
    if (stem + "e") in verbs:
        return stem + "e"
    if len(stem) >= 2 and stem[-1] == stem[-2] and stem[:-1] in verbs:
        return stem[:-1]
    return None


def main() -> None:
    words = load_words()
    _, nouns, verbs = load_ejdict_lexicon()
    plural = [(w.upper(), b.upper()) for w in words if (b := plural_base(w, nouns))]
    past = [(w.upper(), b.upper()) for w in words if (b := past_base(w, verbs))]
    ing = [(w.upper(), b.upper()) for w in words if (b := ing_base(w, verbs))]
    union = {w for w, _ in plural + past + ing}
    print(json.dumps({
        "dictionary_total": len(words),
        "regular_plural_candidates": len(plural),
        "regular_past_or_participle_candidates": len(past),
        "ing_candidates": len(ing),
        "unique_inflected_candidates": len(union),
        "plural_forms": plural,
        "past_forms": past,
        "ing_forms": ing,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
