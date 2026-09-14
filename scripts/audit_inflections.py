#!/usr/bin/env python3
"""Audit inflectional forms in the shipped five-letter dictionary."""
from __future__ import annotations

import json
import re
from pathlib import Path

from lemminflect import getInflection, getLemma

ROOT = Path(__file__).resolve().parents[1]
WORDS_PATH = ROOT / "dist" / "assets" / "words.js"


def load_words() -> list[str]:
    source = WORDS_PATH.read_text()
    match = re.search(r"window\.WORD_DATA=(\[[\s\S]*\]);", source)
    if not match:
        raise RuntimeError("Dictionary payload not found")
    return [entry[0].lower() for entry in json.loads(match.group(1))]


def regular_plural(lemma: str) -> set[str]:
    if re.search(r"[^aeiou]y$", lemma):
        return {lemma[:-1] + "ies"}
    if re.search(r"(?:s|x|z|ch|sh)$", lemma):
        return {lemma + "es"}
    return {lemma + "s"}


def regular_past(lemma: str) -> set[str]:
    if lemma.endswith("e"):
        return {lemma + "d"}
    if re.search(r"[^aeiou]y$", lemma):
        return {lemma[:-1] + "ied"}
    return {lemma + "ed"}


def classify(words: list[str]) -> dict[str, list[tuple[str, str]]]:
    regular_plurals: list[tuple[str, str]] = []
    irregular_plurals: list[tuple[str, str]] = []
    regular_pasts: list[tuple[str, str]] = []
    irregular_pasts: list[tuple[str, str]] = []
    ing_forms: list[tuple[str, str]] = []

    for word in words:
        noun_lemmas = getLemma(word, upos="NOUN") or ()
        for lemma in noun_lemmas:
            generated = set(getInflection(lemma, tag="NNS") or ())
            if word != lemma and word in generated:
                target = regular_plurals if word in regular_plural(lemma) else irregular_plurals
                pair = (word.upper(), lemma.upper())
                if pair not in target:
                    target.append(pair)
                break

        verb_lemmas = getLemma(word, upos="VERB") or ()
        for lemma in verb_lemmas:
            past_generated = set(getInflection(lemma, tag="VBD") or ()) | set(getInflection(lemma, tag="VBN") or ())
            if word != lemma and word in past_generated:
                target = regular_pasts if word in regular_past(lemma) else irregular_pasts
                pair = (word.upper(), lemma.upper())
                if pair not in target:
                    target.append(pair)
                break
        for lemma in verb_lemmas:
            generated = set(getInflection(lemma, tag="VBG") or ())
            if word != lemma and word in generated:
                pair = (word.upper(), lemma.upper())
                if pair not in ing_forms:
                    ing_forms.append(pair)
                break

    return {
        "regular_plurals": regular_plurals,
        "irregular_plurals": irregular_plurals,
        "regular_pasts": regular_pasts,
        "irregular_pasts": irregular_pasts,
        "ing_forms": ing_forms,
    }


def main() -> None:
    words = load_words()
    groups = classify(words)
    simple_union = {
        word
        for key in ("regular_plurals", "regular_pasts", "ing_forms")
        for word, _ in groups[key]
    }
    print(json.dumps({
        "dictionary_total": len(words),
        "regular_plural_count": len(groups["regular_plurals"]),
        "irregular_plural_count": len(groups["irregular_plurals"]),
        "regular_past_or_participle_count": len(groups["regular_pasts"]),
        "irregular_past_or_participle_count": len(groups["irregular_pasts"]),
        "ing_count": len(groups["ing_forms"]),
        "unique_simple_inflected_count": len(simple_union),
        **groups,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
