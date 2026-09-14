#!/usr/bin/env python3
"""Build the embedded WORD LOGIC RELAY dictionary from licensed/reference data.

Development inputs are intentionally outside the shipped Site. The generated
asset is self-contained and validated separately by validate.mjs.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent / "work"
REFERENCE = ROOT / "reference" / "original-word-logic-relay.html"

GOOGLE = WORK / "google-10000-english-no-swears.txt"  # audit only
TAB = WORK / "tabatkins-wordle-list.txt"
ALEX = WORK / "alex1770-wordle-list.txt"
JMDICT = WORK / "jmdict-eng-common-3.6.2.json"

# Proper names, brands, abbreviations, slurs and explicit/general-audience rejects.
REJECT = set("""
BITCH BOOBS BOOBY BONER DICKS DILDO DYKEE FAGOT FANNY FUCKS HANDY HORNY HYMEN
INCEL JAMES JAPAN JESUS JIHAD JIMMY LINUX MECCA MENSA PETER PUBIC PUBIS PUSSY
QURAN RALPH ROMAN SHIVA SMITH SPAIN SPERM TEXAS TITAN TONGA TORAH TRUMP VULVA
WHORE XEROX YAHOO CHINA INDIA PARIS BIBLE KORAN VEGAS JONES LOUIS HARRY KELLY
HENRY INTEL CISCO ADOBE DEVEL
""".split())

# Common words missed by exact reverse-JMdict matching, plus wording fixes for
# places where an exact English gloss maps to an awkward secondary Japanese sense.
OVERRIDE = {
    "ABOUT": ("prep/adv", "〜について／およそ"), "ADAPT": ("verb", "適応する／合わせる"),
    "ADMIT": ("verb", "認める／入場を許す"), "ADOPT": ("verb", "採用する／養子にする"),
    "AGREE": ("verb", "同意する／一致する"), "ALIVE": ("adjective", "生きている"),
    "ALLOW": ("verb", "許す"), "ALONE": ("adjective/adverb", "一人で／単独の"),
    "ALTER": ("verb", "変える"), "ANGRY": ("adjective", "怒っている"),
    "APPLE": ("noun", "りんご"), "APPLY": ("verb", "申し込む／当てはまる"),
    "ARGUE": ("verb", "議論する／主張する"), "ARISE": ("verb", "生じる／立ち上がる"),
    "AVOID": ("verb", "避ける"), "AWAKE": ("adjective/verb", "目覚めて／目を覚ます"),
    "BEGIN": ("verb", "始める"), "BOOST": ("verb/noun", "高める／後押し"),
    "BRING": ("verb", "持ってくる"), "BURST": ("verb/noun", "破裂する／爆発"),
    "CARVE": ("verb", "彫る／切り分ける"), "CLICK": ("verb/noun", "クリックする／カチッという音"),
    "CRANE": ("noun", "ツル／クレーン"), "CRAWL": ("verb", "はう／ゆっくり進む"),
    "DAIRY": ("noun/adjective", "乳製品店／乳製品の"), "DRONE": ("noun/verb", "無人機／低くうなる"),
    "DROWN": ("verb", "溺れる／水没させる"), "ENJOY": ("verb", "楽しむ"),
    "EXIST": ("verb", "存在する"), "FETCH": ("verb", "取ってくる"),
    "FIFTH": ("number", "5番目"), "FLEET": ("noun", "艦隊／車両群"),
    "FORTH": ("adverb", "前へ／外へ"), "FOUND": ("verb", "設立する"),
    "GIVEN": ("adjective/preposition", "与えられた／〜を考慮すると"), "GOOSE": ("noun", "ガチョウ"),
    "GREET": ("verb", "あいさつする／迎える"), "GROWN": ("adjective", "成長した／大人の"),
    "INNER": ("adjective", "内側の／内面の"), "ITEMS": ("noun", "項目／品物"),
    "LEARN": ("verb", "学ぶ／知る"), "LOWER": ("verb/adjective", "下げる／より低い"),
    "LYRIC": ("noun/adjective", "歌詞／叙情的な"), "PATCH": ("noun/verb", "つぎ当て／修正する"),
    "PIANO": ("noun", "ピアノ"), "POLAR": ("adjective", "極地の／正反対の"),
    "POUND": ("noun/verb", "ポンド／強く打つ"), "PROVE": ("verb", "証明する／判明する"),
    "RAISE": ("verb", "上げる／育てる"), "REACH": ("verb/noun", "届く／範囲"),
    "RELAX": ("verb", "くつろぐ／緩める"), "RESET": ("verb/noun", "リセットする／再設定"),
    "SHIRT": ("noun", "シャツ"), "SOLVE": ("verb", "解決する／解く"),
    "SPEAK": ("verb", "話す"), "SPOIL": ("verb", "台無しにする／甘やかす"),
    "STEER": ("verb", "操縦する／導く"), "STUCK": ("adjective", "動けない／行き詰まった"),
    "TAKEN": ("adjective", "取られた／使用中の"), "TIGER": ("noun", "トラ"),
    "UNITE": ("verb", "結びつける／団結する"), "UPSET": ("verb/adjective", "動揺させる／取り乱した"),
    "VOCAL": ("adjective/noun", "声の／歌唱"), "WEIGH": ("verb", "重さを量る／よく考える"),
    "WHALE": ("noun", "クジラ"), "WORSE": ("adjective/adverb", "より悪い"),
    "WOULD": ("verb", "〜だろう／〜したものだ"), "WRECK": ("noun/verb", "残骸／破壊する"),
    "WRITE": ("verb", "書く"), "ZEBRA": ("noun", "シマウマ"),
    "ACRID": ("adjective", "刺激臭のある／辛辣な"), "GUILE": ("noun", "ずる賢さ／策略"),
    "KNAVE": ("noun", "悪党／ならず者"), "MIDGE": ("noun", "小さな羽虫"),
    "QUAFF": ("verb", "がぶがぶ飲む／一気に飲む"), "SEDGE": ("noun", "スゲ（湿地の草）"),
    "SHREW": ("noun", "トガリネズミ"), "VIXEN": ("noun", "雌ギツネ"),
    "WHELP": ("noun", "獣の子"),
    "THEIR": ("determiner", "彼らの／それらの"), "THERE": ("adverb", "そこに／そこで"),
    "THESE": ("determiner", "これらの"), "EMAIL": ("noun/verb", "電子メール／メールする"),
    "BOOKS": ("noun/verb", "本／予約する"), "LINKS": ("noun/verb", "つながり／結ぶ"),
    "YEARS": ("noun", "年／歳月"), "GAMES": ("noun", "ゲーム／試合"),
    "COULD": ("verb", "〜できた／〜かもしれない"), "GREAT": ("adjective", "すばらしい／大きな"),
    "STORE": ("noun/verb", "店／保管する"), "TERMS": ("noun", "用語／条件"),
    "RIGHT": ("adjective/noun", "正しい／右"), "THOSE": ("determiner", "それらの"),
    "USING": ("verb", "使っている"), "FORUM": ("noun", "公開討論の場／掲示板"),
    "BASED": ("adjective", "基づいた"), "BEING": ("noun/verb", "存在／〜であること"),
    "WOMEN": ("noun", "女性たち"), "TODAY": ("noun/adverb", "今日"),
    "PAGES": ("noun", "ページ"), "THREE": ("number", "3／3つ"),
    "THINK": ("verb", "考える／思う"), "POSTS": ("noun/verb", "投稿／柱"),
    "TIMES": ("noun", "回数／時代"), "SITES": ("noun", "場所／ウェブサイト"),
    "HOURS": ("noun", "時間"), "SHALL": ("verb", "〜するものとする"),
    "TOOLS": ("noun", "道具"), "PRESS": ("verb/noun", "押す／報道機関"),
    "SALES": ("noun", "販売／売上"), "START": ("verb/noun", "始める／開始"),
    "GOING": ("verb/noun", "行くこと／進行"), "USERS": ("noun", "利用者"),
    "LOGIN": ("noun", "ログイン"), "RATES": ("noun/verb", "率／評価する"),
    "GIRLS": ("noun", "女の子たち"), "FILES": ("noun/verb", "ファイル／提出する"),
    "NEEDS": ("noun/verb", "必要／必要とする"), "MONTH": ("noun", "月（期間）"),
    "AREAS": ("noun", "地域／領域"), "CARDS": ("noun", "カード"),
    "ADDED": ("verb", "加えた"), "UNTIL": ("preposition", "〜まで"),
    "CLOSE": ("verb/adjective", "閉じる／近い"), "MEANS": ("noun/verb", "手段／意味する"),
    "COSTS": ("noun/verb", "費用／費用がかかる"), "PARTS": ("noun", "部分／部品"),
    "MILES": ("noun", "マイル"), "WORKS": ("verb/noun", "働く／作品"),
    "RULES": ("noun/verb", "規則／支配する"), "THING": ("noun", "物／こと"),
    "THIRD": ("number", "3番目"), "GIFTS": ("noun", "贈り物／才能"),
    "OFTEN": ("adverb", "しばしば"), "DEALS": ("noun/verb", "取引／対処する"),
    "WORDS": ("noun", "単語／言葉"), "MAKES": ("verb", "作る／〜にする"),
    "KNOWN": ("adjective", "知られている"), "CASES": ("noun", "場合／事例"),
    "SHOWS": ("verb/noun", "示す／番組"), "DEATH": ("noun", "死"),
    "STUFF": ("noun/verb", "物／詰め込む"), "DOING": ("verb/noun", "している／行為"),
    "LOANS": ("noun", "貸付／ローン"), "SHOES": ("noun", "靴"),
    "NOTES": ("noun/verb", "メモ／注記する"), "VIEWS": ("noun/verb", "眺め／見なす"),
    "PLANS": ("noun/verb", "計画／計画する"), "TYPES": ("noun/verb", "種類／入力する"),
    "LINES": ("noun", "線／列"), "ASKED": ("verb", "尋ねた／頼んだ"),
    "WEEKS": ("noun", "週"), "NAMES": ("noun/verb", "名前／名づける"),
    "TEENS": ("noun", "10代"), "SHOWN": ("verb", "示された"),
    "FLASH": ("noun/verb", "閃光／ひらめく"), "IDEAS": ("noun", "考え／アイデア"),
    "HOMES": ("noun", "家／家庭"), "ROOMS": ("noun", "部屋／余地"),
    "COMES": ("verb", "来る"), "FORMS": ("noun/verb", "形／形成する"),
    "HAPPY": ("adjective", "幸せな／うれしい"), "THANK": ("verb", "感謝する"),
    "PRIOR": ("adjective", "前の／優先する"), "BUILT": ("verb/adjective", "建てた／造られた"),
    "BASIS": ("noun", "基礎／根拠"), "AWARD": ("noun/verb", "賞／授与する"),
    "RATED": ("verb/adjective", "評価された／等級づけされた"), "STARS": ("noun", "星／スター"),
    "LISTS": ("noun/verb", "一覧／列挙する"), "TAKES": ("verb", "取る／要する"),
    "UNITS": ("noun", "単位／装置"), "WROTE": ("verb", "書いた"),
    "SHIPS": ("noun/verb", "船／発送する"), "FUNDS": ("noun/verb", "資金／資金提供する"),
    "SEEMS": ("verb", "〜のように見える"), "SENSE": ("noun/verb", "感覚／察する"),
    "GOODS": ("noun", "商品"), "MAYBE": ("adverb", "たぶん"),
    "CIVIL": ("adjective", "市民の／礼儀正しい"), "SONGS": ("noun", "歌"),
    "HANDS": ("noun", "手／作業員"), "FULLY": ("adverb", "完全に"),
    "GRANT": ("verb/noun", "認める／助成金"), "BLOGS": ("noun/verb", "ブログ／ブログを書く"),
    "GIVES": ("verb", "与える"), "HEARD": ("verb", "聞いた"),
    "CELLS": ("noun", "細胞／小部屋"), "CALLS": ("noun/verb", "電話／呼ぶ"),
    "WHOSE": ("determiner", "誰の／その人の"), "LIVES": ("noun/verb", "命／暮らす"),
    "TESTS": ("noun/verb", "試験／検査する"), "CANON": ("noun", "規範／正典"),
    "DATES": ("noun/verb", "日付／交際する"), "BEGAN": ("verb", "始めた"),
    "SHOPS": ("noun/verb", "店／買い物をする"), "TOURS": ("noun/verb", "旅行／見学する"),
    "ADMIN": ("noun", "管理／管理者"), "MOVED": ("verb", "動いた／感動した"),
    "FILMS": ("noun/verb", "映画／撮影する"), "OWNED": ("verb", "所有した"),
    "CLUBS": ("noun", "クラブ／こん棒"), "CODES": ("noun/verb", "規則／符号化する"),
    "KINDS": ("noun", "種類"), "TEAMS": ("noun/verb", "チーム／組む"),
    "TRIED": ("verb/adjective", "試した／疲れた"), "FALLS": ("verb/noun", "落ちる／滝"),
    "STATS": ("noun", "統計"), "CLIPS": ("noun/verb", "留め具／切り取る"),
    "ENDED": ("verb", "終わった"), "VOTES": ("noun/verb", "票／投票する"),
    "FEEDS": ("verb/noun", "食べさせる／配信"), "BYTES": ("noun", "バイト（情報単位）"),
    "FILED": ("verb", "提出した／整理した"), "BANKS": ("noun/verb", "銀行／土手"),
    "LEADS": ("verb/noun", "導く／手がかり"), "SPENT": ("verb/adjective", "使った／疲れ果てた"),
    "HELPS": ("verb/noun", "助ける／助け"), "RINGS": ("noun/verb", "指輪／鳴る"),
    "TREES": ("noun", "木々"), "REFER": ("verb", "言及する／参照する"),
    "BABES": ("noun", "赤ん坊たち"), "SPEND": ("verb", "使う／過ごす"),
    "SPECS": ("noun", "仕様／眼鏡"), "PARKS": ("noun/verb", "公園／駐車する"),
    "BOXES": ("noun/verb", "箱／ボクシングをする"), "HILLS": ("noun", "丘"),
    "FIRMS": ("noun/verb", "会社／固める"), "TEACH": ("verb", "教える"),
}

def read_words(path: Path) -> list[str]:
    return [w.upper() for w in path.read_text().split() if re.fullmatch(r"[A-Za-z]{5}", w)]

def extract_reference(name: str, quote: str) -> list[str]:
    text = REFERENCE.read_text()
    if quote == '"':
        m = re.search(rf'const {name} = "([^"]+)"\.split', text)
    else:
        m = re.search(rf'const {name} = `([\s\S]*?)`\.trim', text)
    if not m:
        raise RuntimeError(f"Could not extract {name}")
    return [w for w in m.group(1).split() if re.fullmatch(r"[A-Z]{5}", w)]

def build_jmdict_index():
    data = json.loads(JMDICT.read_text())
    index: dict[str, list[tuple[str, list[str]]]] = {}
    for entry in data["words"]:
        preferred = [x["text"] for x in entry["kanji"] if x.get("common")]
        if not preferred:
            preferred = [x["text"] for x in entry["kana"] if x.get("common")]
        if not preferred:
            preferred = [x["text"] for x in entry["kanji"]] or [x["text"] for x in entry["kana"]]
        if not preferred:
            continue
        for sense in entry["sense"]:
            for gloss in sense["gloss"]:
                key = gloss["text"].lower().strip()
                index.setdefault(key, []).append((preferred[0], sense["partOfSpeech"]))
    return index, data

def coarse_pos(tags: list[str]) -> str:
    joined = " ".join(tags)
    if "adj" in joined: return "adjective"
    if "adv" in joined: return "adverb"
    if "v" in joined: return "verb"
    if "n" in joined: return "noun"
    return "word"

def gloss(word: str, index) -> tuple[str, str] | None:
    if word in OVERRIDE:
        return OVERRIDE[word]
    hits = index.get(word.lower(), [])
    if not hits:
        return None
    ja = []
    tags = []
    for text, pos in hits:
        if text not in ja and len(text) <= 8:
            ja.append(text)
        tags.extend(pos)
        if len(ja) == 2:
            break
    if not ja:
        return None
    return coarse_pos(tags), "／".join(ja)

def main():
    for path in (GOOGLE, TAB, ALEX, JMDICT, REFERENCE):
        if not path.exists():
            raise SystemExit(f"Missing input: {path}")

    common_original = extract_reference("COMMON_ANSWER_WORDS", '"')
    hard_original = extract_reference("HARD_ANSWER_WORDS", '`')
    tab = set(read_words(TAB))
    alex = set(read_words(ALEX))
    google_lines = [w.strip().upper() for w in GOOGLE.read_text().splitlines()]
    google_top_3000 = [w for w in google_lines[:3000] if re.fullmatch(r"[A-Z]{5}", w)]
    index, jmdict = build_jmdict_index()

    # Initial EASY pool is the supplied curated list. The independent audit adds
    # common, general-audience candidates that are accepted by a Wordle source.
    easy = set(common_original)
    easy.update("APPLE HOUSE WORLD LIGHT TRAIN BRAIN MUSIC MONEY WATER BEACH PHONE WRITE DRINK LEARN TEACH SPEAK DRIVE HAPPY SMALL BLACK WHITE CLEAN SWEET".split())
    for word in google_top_3000:
        if word in REJECT or word in easy or word not in tab | alex:
            continue
        if gloss(word, index):
            easy.add(word)

    # HARD is built from the existing extended answer list and both MIT Wordle
    # sources. Retain entries with a local Japanese gloss, then force the nine
    # specification examples (covered by reviewed overrides).
    hard_candidates = (set(hard_original) & (tab | alex)) - easy - REJECT
    hard = {w for w in hard_candidates if gloss(w, index)}
    hard.update({"ACRID", "GUILE", "KNAVE", "MIDGE", "QUAFF", "SEDGE", "SHREW", "VIXEN", "WHELP"})
    hard -= easy

    entries = []
    for level, words in (("easy", sorted(easy)), ("hard", sorted(hard))):
        for word in words:
            value = gloss(word, index)
            if not value:
                raise RuntimeError(f"Missing gloss: {word}")
            pos, ja = value
            entries.append([word, "e" if level == "easy" else "h", pos, ja])

    out = ROOT / "dist" / "assets" / "words.js"
    out.write_text(
        "/* Generated canonical dictionary. See docs/dictionary-audit.md. */\n"
        "window.WORD_DATA=" + json.dumps(entries, ensure_ascii=False, separators=(",", ":")) + ";\n"
    )

    game = {e[0] for e in entries}
    missing = [w for w in google_top_3000 if w not in game]
    reviewed_rejects = [w for w in missing if w in REJECT]
    unsupported = [w for w in missing if w not in tab | alex]
    unresolved = [w for w in missing if w not in REJECT and w in tab | alex]
    audit = f"""# Dictionary construction and coverage audit

Generated from deterministic set operations on 2026-09-14.

## Shipped dictionary

- EASY: {len(easy)}
- HARD: {len(hard)}
- Total valid guesses / answer candidates: {len(entries)}
- Every entry has an embedded Japanese gloss and part-of-speech label.

## Construction sources

- Existing game vocabulary in the preserved reference snapshot.
- `tabatkins/wordle-list` (MIT) as a validity candidate source.
- `alex1770/wordle` hidden-answer list (MIT) as a validity candidate source.
- JMdict common English subset via `scriptin/jmdict-simplified` for development-time Japanese-gloss candidates (CC BY-SA 4.0 / EDRDG terms). Reviewed overrides improve common or ambiguous mappings. The derived gloss data is distributed under CC BY-SA 4.0.

The sources above are development inputs only. The Site ships one local generated dictionary and performs no runtime lookups.

## Independent common-word coverage audit

The first 3,000 entries of `first20hours/google-10000-english`'s no-swear list were filtered to exactly five A-Z letters and compared against the game dictionary. This source is used as an audit reference only; it is not redistributed. Its own license warns against commercial redistribution.

- Five-letter audit reference entries: {len(google_top_3000)}
- Covered after audit: {len(google_top_3000) - len(missing)}
- Reviewed explicit exclusions (proper names, brands, unsuitable vocabulary): {len(reviewed_rejects)}
- Not present in either Wordle validity source: {len(unsupported)}
- Remaining plausible/valid candidates not added: {len(unresolved)}

Remaining candidates: {', '.join(unresolved) if unresolved else 'none'}

## Invariants

The release validator verifies uppercase five-letter spelling, unique keys, exact EASY/HARD classification, non-empty Japanese glosses, disjoint answer pools, dictionary-derived valid guesses, dictionary size, required common coverage, and required HARD examples.
"""
    (ROOT / "docs" / "dictionary-audit.md").write_text(audit)
    print(json.dumps({"easy": len(easy), "hard": len(hard), "total": len(entries), "audit_missing": len(missing), "unresolved": unresolved}, ensure_ascii=False))

if __name__ == "__main__":
    main()
