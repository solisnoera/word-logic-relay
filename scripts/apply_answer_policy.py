#!/usr/bin/env python3
"""Apply the generated answer-exclusion policy to the runtime game code."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "dist" / "assets" / "game.js"

OLD = '''  const WORD_BY_TEXT = new Map(WORDS.map((entry) => [entry.word, entry]));
  const EASY_WORDS = WORDS.filter((entry) => entry.level === "easy").map((entry) => entry.word);
  const HARD_WORDS = WORDS.filter((entry) => entry.level === "hard").map((entry) => entry.word);
  const VALID_WORDS = new Set(WORD_BY_TEXT.keys());
'''

NEW = '''  const WORD_BY_TEXT = new Map(WORDS.map((entry) => [entry.word, entry]));
  const ANSWER_EXCLUSIONS = new Set(window.ANSWER_EXCLUSIONS || []);
  const EASY_WORDS = WORDS.filter((entry) => entry.level === "easy" && !ANSWER_EXCLUSIONS.has(entry.word)).map((entry) => entry.word);
  const HARD_WORDS = WORDS.filter((entry) => entry.level === "hard" && !ANSWER_EXCLUSIONS.has(entry.word)).map((entry) => entry.word);
  const VALID_WORDS = new Set(WORD_BY_TEXT.keys());
'''

source = GAME.read_text()
if OLD in source:
    source = source.replace(OLD, NEW, 1)
elif NEW not in source:
    raise RuntimeError("game.js answer-pool block did not match expected source")

source = source.replace('WLR-DICT-3|${japanDateKey()}', 'WLR-DICT-4|${japanDateKey()}')
GAME.write_text(source)
