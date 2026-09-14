#!/usr/bin/env python3
"""Expand the embedded WORD LOGIC RELAY dictionary using development-time sources.

Runtime remains fully local. This script fetches candidate/reference data only while
building the shipped dictionary.
"""
from __future__ import annotations

import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORDS_PATH = ROOT / "dist" / "assets" / "words.js"
REPORT_PATH = ROOT / "docs" / "dictionary-expansion-report.md"
TARGET_TOTAL = 2800
EASY_GOOGLE_RANK = 6500

GOOGLE_URL = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-no-swears.txt"
TAB_URL = "https://raw.githubusercontent.com/tabatkins/wordle-list/main/words"
ALEX_URL = "https://raw.githubusercontent.com/alex1770/wordle/main/wordlist_hidden"
JMDICT_RELEASE_URL = "https://api.github.com/repos/scriptin/jmdict-simplified/releases/latest"

REJECT = set("""
BITCH BOOBS BOOBY BONER DICKS DILDO DYKEE FAGOT FANNY FUCKS HANDY HORNY HYMEN
INCEL JAMES JAPAN JESUS JIHAD JIMMY LINUX MECCA MENSA PETER PUBIC PUBIS PUSSY
QURAN RALPH ROMAN SHIVA SMITH SPAIN SPERM TEXAS TITAN TONGA TORAH TRUMP VULVA
WHORE XEROX YAHOO CHINA INDIA PARIS BIBLE KORAN VEGAS JONES LOUIS HARRY KELLY
HENRY INTEL CISCO ADOBE DEVEL
""".split())

JP_BAD = (
    "気違い", "うんこ", "エロ", "エッチ", "デブ", "百姓", "馬鹿", "禿",
    "ちんこ", "チンコ", "まんこ", "マンコ", "売春", "淫乱",
)


def request_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "word-logic-relay-dictionary-builder/1.0"})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()


def request_text(url: str) -> str:
    return request_bytes(url).decode("utf-8")


def load_base_entries() -> list[list[str]]:
    text = WORDS_PATH.read_text()
    m = re.search(r"window\.WORD_DATA=(\[[\s\S]*\]);", text)
    if not m:
        raise RuntimeError("Canonical dictionary payload not found")
    entries = json.loads(m.group(1))
    if not isinstance(entries, list):
        raise RuntimeError("Bad canonical dictionary payload")
    return entries


def load_jmdict_common() -> dict:
    release = json.loads(request_text(JMDICT_RELEASE_URL))
    assets = release.get("assets", [])
    candidates = [a for a in assets if a.get("name", "").startswith("jmdict-eng-common-") and a.get("name", "").endswith(".json.zip")]
    if not candidates:
        raise RuntimeError("Could not locate latest jmdict-eng-common JSON zip")
    raw = request_bytes(candidates[0]["browser_download_url"])
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = [name for name in archive.namelist() if name.endswith(".json")]
        if len(members) != 1:
            raise RuntimeError(f"Unexpected JMdict archive contents: {members[:5]}")
        return json.loads(archive.read(members[0]).decode("utf-8"))


def normalize_pos(tags: list[str]) -> str | None:
    cats: list[str] = []
    lowered = [str(tag).lower() for tag in tags]
    if any(tag.startswith("adj") or "adjective" in tag for tag in lowered): cats.append("adjective")
    if any(tag.startswith("adv") or "adverb" in tag for tag in lowered): cats.append("adverb")
    if any(tag.startswith("v") or "verb" in tag for tag in lowered): cats.append("verb")
    if any(tag == "n" or tag.startswith("n-") or "noun" in tag for tag in lowered): cats.append("noun")
    if any(tag.startswith("pn") or "pronoun" in tag for tag in lowered): cats.append("pronoun")
    if any(tag.startswith("conj") or "conjunction" in tag for tag in lowered): cats.append("conjunction")
    if any(tag.startswith("prt") or "particle" in tag for tag in lowered): cats.append("particle")
    if any(tag.startswith("aux") or "auxiliary" in tag for tag in lowered): cats.append("auxiliary")
    if not cats:
        return None
    ordered = []
    for cat in cats:
        if cat not in ordered:
            ordered.append(cat)
    return "/".join(ordered[:2])


def build_reverse_index(data: dict) -> dict[str, list[tuple[int, str, str]]]:
    index: dict[str, list[tuple[int, str, str]]] = {}
    for entry in data.get("words", []):
        kanji = entry.get("kanji", [])
        kana = entry.get("kana", [])
        surfaces: list[tuple[str, bool]] = []
        for item in kanji + kana:
            text = item.get("text", "")
            if text:
                surfaces.append((text, bool(item.get("common"))))
        if not surfaces:
            continue
        for sense in entry.get("sense", []):
            pos = normalize_pos(sense.get("partOfSpeech", []))
            if not pos:
                continue
            for gloss in sense.get("gloss", []):
                key = str(gloss.get("text", "")).strip().lower()
                if not key:
                    continue
                for surface, common in surfaces:
                    score = 4 if common else 0
                    if len(surface) <= 6: score += 2
                    if not re.search(r"[A-Za-z0-9]", surface): score += 2
                    index.setdefault(key, []).append((score, pos, surface))
    return index


def safe_metadata(word: str, index: dict[str, list[tuple[int, str, str]]]) -> tuple[str, str] | None:
    hits = index.get(word.lower(), [])
    cleaned: list[tuple[int, str, str]] = []
    seen = set()
    for score, pos, ja in hits:
        ja = ja.strip()
        if not ja or len(ja) > 8 or re.search(r"[A-Za-z0-9]", ja):
            continue
        if any(fragment in ja for fragment in JP_BAD):
            continue
        key = (pos, ja)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append((score, pos, ja))
    if not cleaned:
        return None
    cleaned.sort(key=lambda item: (-item[0], len(item[2]), item[2]))
    best = cleaned[0]
    # Ambiguous low-confidence reverse mappings caused most of the earlier bad glosses.
    # Only accept a weak candidate when it is unique; otherwise skip the word.
    if best[0] < 4 and len(cleaned) > 1:
        return None
    return best[1], best[2]


def five_letter_words(text: str) -> list[str]:
    return [w.upper() for w in text.split() if re.fullmatch(r"[A-Za-z]{5}", w)]


def main() -> None:
    base_entries = load_base_entries()
    base_words = {entry[0] for entry in base_entries}
    if len(base_words) != len(base_entries):
        raise RuntimeError("Duplicate in baseline dictionary")

    google_all = [line.strip().upper() for line in request_text(GOOGLE_URL).splitlines() if line.strip()]
    google_rank = {word: rank for rank, word in enumerate(google_all, 1) if re.fullmatch(r"[A-Z]{5}", word)}
    tab = set(five_letter_words(request_text(TAB_URL)))
    alex = set(five_letter_words(request_text(ALEX_URL)))
    jmdict = load_jmdict_common()
    index = build_reverse_index(jmdict)

    candidates = (alex | {w for w in google_rank if w in tab}) - base_words - REJECT
    accepted: list[tuple[str, str, str, str, int | None, str]] = []
    skipped_no_metadata = 0
    for word in candidates:
        metadata = safe_metadata(word, index)
        if not metadata:
            skipped_no_metadata += 1
            continue
        pos, ja = metadata
        rank = google_rank.get(word)
        if rank is not None and rank <= EASY_GOOGLE_RANK:
            level = "e"
            source = "common-frequency"
        elif word in alex:
            level = "h"
            source = "wordle-answer"
        else:
            level = "h"
            source = "valid-guess"
        accepted.append((word, level, pos, ja, rank, source))

    def priority(item: tuple[str, str, str, str, int | None, str]):
        word, level, _pos, _ja, rank, source = item
        if level == "e":
            return (0, rank if rank is not None else 999999, word)
        if source == "wordle-answer":
            return (1, rank if rank is not None else 999999, word)
        return (2, rank if rank is not None else 999999, word)

    accepted.sort(key=priority)
    slots = max(0, TARGET_TOTAL - len(base_entries))
    additions = accepted[:slots]
    entries = list(base_entries)
    entries.extend([[word, level, pos, ja] for word, level, pos, ja, _rank, _source in additions])

    words = [entry[0] for entry in entries]
    if len(words) != len(set(words)):
        raise RuntimeError("Expansion produced duplicates")
    if len(entries) < min(TARGET_TOTAL, 2400):
        raise RuntimeError(f"Too few high-confidence additions: {len(entries)}")

    WORDS_PATH.write_text(
        "/* Generated canonical dictionary. See docs/dictionary-audit.md. */\n"
        "window.WORD_DATA=" + json.dumps(entries, ensure_ascii=False, separators=(",", ":")) + ";\n"
    )

    added_easy = sum(1 for item in additions if item[1] == "e")
    added_hard = len(additions) - added_easy
    sample_easy = ", ".join(item[0] for item in additions if item[1] == "e")[:500]
    sample_hard = ", ".join(item[0] for item in additions if item[1] == "h")[:500]
    REPORT_PATH.write_text(f"""# Dictionary expansion report

Generated by `scripts/expand_dictionary.py`.

- Baseline words preserved: {len(base_entries)}
- Added words: {len(additions)}
- Expanded total: {len(entries)}
- Added EASY candidates: {added_easy}
- Added HARD candidates: {added_hard}
- Candidate words skipped because no high-confidence local Japanese metadata was found: {skipped_no_metadata}
- Target total: {TARGET_TOTAL}

## Selection policy

- Existing 1,482 words are preserved.
- `alex1770/wordle` hidden-answer words (MIT) are the main expansion source.
- `tabatkins/wordle-list` (MIT) is used to admit additional common valid guesses.
- `first20hours/google-10000-english` is used only for frequency ranking / EASY prioritization and is not redistributed as a source list.
- JMdict common data supplies development-time Japanese metadata; only high-confidence reverse mappings are accepted.
- Runtime remains fully local.

## Samples

EASY additions: {sample_easy or 'none'}

HARD additions: {sample_hard or 'none'}
""")
    print(json.dumps({
        "baseline": len(base_entries), "added": len(additions), "total": len(entries),
        "added_easy": added_easy, "added_hard": added_hard,
        "skipped_no_metadata": skipped_no_metadata,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
