#!/usr/bin/env python3
"""Expand WORD LOGIC RELAY's embedded five-letter dictionary.

Development-time network sources are used only by this build script. The shipped
Site remains fully local and performs no runtime dictionary/network lookups.
"""
from __future__ import annotations

import io
import json
import re
import string
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORDS_PATH = ROOT / "dist" / "assets" / "words.js"
REPORT_PATH = ROOT / "docs" / "dictionary-expansion-report.md"
TARGET_TOTAL = 2800

TAB_URL = "https://raw.githubusercontent.com/tabatkins/wordle-list/main/words"
ALEX_URL = "https://raw.githubusercontent.com/alex1770/wordle/main/wordlist_hidden"
EJ_SRC = "https://raw.githubusercontent.com/kujirahand/EJDict/master/src/{letter}.txt"
EJ_FREQ = "https://raw.githubusercontent.com/kujirahand/EJDict/master/frequency/2000.txt"
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
    "ちんこ", "チンコ", "まんこ", "マンコ", "淫乱",
)


def request_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "word-logic-relay-dictionary-builder/2.1"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def request_text(url: str) -> str:
    return request_bytes(url).decode("utf-8")


def five_letter_words(text: str) -> list[str]:
    return [w.upper() for w in text.split() if re.fullmatch(r"[A-Za-z]{5}", w)]


def load_base_entries() -> list[list[str]]:
    text = WORDS_PATH.read_text()
    m = re.search(r"window\.WORD_DATA=(\[[\s\S]*\]);", text)
    if not m:
        raise RuntimeError("Canonical dictionary payload not found")
    entries = json.loads(m.group(1))
    if len(entries) != len({entry[0] for entry in entries}):
        raise RuntimeError("Duplicate in baseline dictionary")
    return entries


def load_ejdict() -> dict[str, str]:
    result: dict[str, str] = {}
    for letter in string.ascii_lowercase:
        text = request_text(EJ_SRC.format(letter=letter))
        for line in text.splitlines():
            if "\t" not in line:
                continue
            head, meaning = line.split("\t", 1)
            for variant in head.split(","):
                word = variant.strip().lower()
                if re.fullmatch(r"[a-z]{5}", word):
                    result.setdefault(word, meaning.strip())
    return result


def clean_ej_meaning(raw: str) -> str | None:
    if not raw or raw.startswith("=") or "《差別的表現》" in raw:
        return None
    text = raw.split(" / ", 1)[0].strip()
    text = re.sub(r"《[^》]*》", "", text)
    text = re.sub(r"〈[^〉]*〉", "", text)
    text = re.sub(r"\{[^}]*\}", "", text)
    text = text.replace("『", "").replace("』", "").strip()
    text = re.sub(r"^[（(][^）)]{0,24}[）)]", "", text).strip()
    text = re.sub(r"[（(][^）)]{5,}[）)]", "", text).strip()
    text = text.split(";", 1)[0].strip()
    if "," in text:
        parts = [part.strip() for part in text.split(",") if part.strip()]
        text = "／".join(parts[:2])
    text = re.sub(r"\s+", "", text)
    if not text or len(text) > 28 or not re.search(r"[ぁ-んァ-ヶ一-龯々]", text):
        return None
    if any(fragment in text for fragment in JP_BAD):
        return None
    return text


def load_jmdict_common() -> dict:
    release = json.loads(request_text(JMDICT_RELEASE_URL))
    assets = release.get("assets", [])
    matches = [a for a in assets if a.get("name", "").startswith("jmdict-eng-common-") and a.get("name", "").endswith(".json.zip")]
    if not matches:
        raise RuntimeError("Could not locate latest jmdict-eng-common JSON zip")
    raw = request_bytes(matches[0]["browser_download_url"])
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = [name for name in archive.namelist() if name.endswith(".json")]
        if len(members) != 1:
            raise RuntimeError(f"Unexpected JMdict archive contents: {members[:5]}")
        return json.loads(archive.read(members[0]).decode("utf-8"))


def pos_category(tags: list[str]) -> str | None:
    joined = " ".join(str(tag).lower() for tag in tags)
    categories: list[str] = []
    if "adj" in joined: categories.append("adjective")
    if "adv" in joined: categories.append("adverb")
    if "verb" in joined or re.search(r"\bv[15skrtinuz]", joined): categories.append("verb")
    if "noun" in joined or re.search(r"(^|\s)n($|\s|-)", joined): categories.append("noun")
    if "conj" in joined: categories.append("conjunction")
    if not categories:
        return None
    return "/".join(dict.fromkeys(categories))


def build_pos_index(data: dict) -> dict[str, str]:
    gathered: dict[str, list[str]] = {}
    for entry in data.get("words", []):
        for sense in entry.get("sense", []):
            for gloss in sense.get("gloss", []):
                key = str(gloss.get("text", "")).strip().lower()
                if re.fullmatch(r"[a-z]{5}", key):
                    gathered.setdefault(key, []).extend(sense.get("partOfSpeech", []))
    result = {}
    for word, tags in gathered.items():
        pos = pos_category(tags)
        if pos:
            result[word] = pos
    return result


def ejdict_pos(raw: str) -> str:
    categories: list[str] = []
    if "{形}" in raw: categories.append("adjective")
    if "{副}" in raw: categories.append("adverb")
    if "{動}" in raw: categories.append("verb")
    if "〈C〉" in raw or "〈U〉" in raw: categories.append("noun")
    return "/".join(dict.fromkeys(categories))


def main() -> None:
    baseline = load_base_entries()
    baseline_words = {entry[0] for entry in baseline}
    tab = set(five_letter_words(request_text(TAB_URL)))
    alex = set(five_letter_words(request_text(ALEX_URL)))
    frequency = set(five_letter_words(request_text(EJ_FREQ)))
    ejdict = load_ejdict()
    pos_index = build_pos_index(load_jmdict_common())

    candidates = (alex | (frequency & tab)) - baseline_words - REJECT
    additions: list[list[str]] = []
    rejected_no_meaning = 0
    optional_pos_missing = 0
    for word in sorted(candidates):
        raw = ejdict.get(word.lower(), "")
        meaning = clean_ej_meaning(raw)
        if not meaning:
            rejected_no_meaning += 1
            continue
        pos = pos_index.get(word.lower()) or ejdict_pos(raw)
        if not pos:
            optional_pos_missing += 1
            pos = ""
        level = "e" if word in frequency else "h"
        additions.append([word, level, pos, meaning])

    additions.sort(key=lambda entry: (0 if entry[1] == "e" else 1, entry[0]))
    additions = additions[: max(0, TARGET_TOTAL - len(baseline))]
    entries = baseline + additions

    if len(entries) < 2400:
        raise RuntimeError(f"Too few high-confidence additions: {len(entries)}")
    if len(entries) > TARGET_TOTAL:
        raise RuntimeError(f"Expansion exceeded target: {len(entries)}")
    words = [entry[0] for entry in entries]
    if len(words) != len(set(words)):
        raise RuntimeError("Expansion produced duplicates")

    WORDS_PATH.write_text(
        "/* Generated canonical dictionary. See docs/dictionary-audit.md. */\n"
        "window.WORD_DATA=" + json.dumps(entries, ensure_ascii=False, separators=(",", ":")) + ";\n"
    )

    easy_total = sum(1 for entry in entries if entry[1] == "e")
    hard_total = len(entries) - easy_total
    added_easy = sum(1 for entry in additions if entry[1] == "e")
    added_hard = len(additions) - added_easy
    easy_sample = ", ".join(entry[0] for entry in additions if entry[1] == "e")[:700]
    hard_sample = ", ".join(entry[0] for entry in additions if entry[1] == "h")[:700]

    REPORT_PATH.write_text(f"""# Dictionary expansion report

Generated by `scripts/expand_dictionary.py`.

- Baseline words preserved: {len(baseline)}
- Added words: {len(additions)}
- Expanded total: {len(entries)}
- EASY: {easy_total}
- HARD: {hard_total}
- Added EASY: {added_easy}
- Added HARD: {added_hard}
- Rejected for missing/unsafe concise EJDict meaning: {rejected_no_meaning}
- Added entries with optional POS omitted because it could not be resolved confidently: {optional_pos_missing}
- Target ceiling: {TARGET_TOTAL}

## Selection policy

- The existing 1,482-word baseline is preserved.
- `alex1770/wordle` hidden-answer list (MIT) is the main expansion candidate source.
- `tabatkins/wordle-list` (MIT) is used only to admit additional high-frequency valid guesses.
- EJDict (CC0/Public Domain) supplies direct English-to-Japanese glosses.
- EJDict's 2,000-word frequency list determines additional EASY candidates.
- JMdict common data and EJDict markers supply POS where they resolve cleanly; POS is intentionally optional rather than guessed.
- Entries without a concise school-safe Japanese gloss are skipped.
- Runtime remains fully local; no source is queried during gameplay.

## Samples

EASY additions: {easy_sample or 'none'}

HARD additions: {hard_sample or 'none'}
""")

    print(json.dumps({
        "baseline": len(baseline), "added": len(additions), "total": len(entries),
        "easy": easy_total, "hard": hard_total,
        "added_easy": added_easy, "added_hard": added_hard,
        "rejected_no_meaning": rejected_no_meaning,
        "optional_pos_missing": optional_pos_missing,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
