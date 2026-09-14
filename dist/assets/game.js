(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const WORDS = (window.WORD_DATA || []).map(([word, level, pos, ja]) => ({
    word, level: level === "e" ? "easy" : "hard", pos, ja: ja.split("／")
  }));
  const WORD_BY_TEXT = new Map(WORDS.map((entry) => [entry.word, entry]));
  const ANSWER_EXCLUSIONS = new Set(window.ANSWER_EXCLUSIONS || []);
  const EASY_WORDS = WORDS.filter((entry) => entry.level === "easy" && !ANSWER_EXCLUSIONS.has(entry.word)).map((entry) => entry.word);
  const HARD_WORDS = WORDS.filter((entry) => entry.level === "hard" && !ANSWER_EXCLUSIONS.has(entry.word)).map((entry) => entry.word);
  const VALID_WORDS = new Set(WORD_BY_TEXT.keys());
  const MODES = {
    normal: { name: ["", "SOLO", "DUO", "TRIO", "FOUR", "FIVE", "SIX"] },
    boss: { name: "BOSS", tries: 12 }, blind: { name: "BLIND", tries: 10 },
    time: { name: "TIME", tries: 9 }, daily: { name: "DAILY", tries: 9 }
  };

  const state = {
    difficulty: "easy", mode: 1, special: "normal", maxTries: 6, tries: 0,
    current: "", targets: [], solved: [], history: [], keyStatus: {}, over: true,
    busy: false, runId: 0, timerId: null, timeLeft: 0, timedOut: false,
    bossBan: "", audioContext: null, scheduled: []
  };

  function boot() {
    if (!WORDS.length) throw new Error("Dictionary unavailable");
    document.querySelectorAll(".difficulty").forEach((button) => {
      button.addEventListener("click", () => setDifficulty(button.dataset.difficulty));
    });
    document.querySelectorAll(".mode").forEach((button) => {
      button.addEventListener("click", () => startGame(Number(button.dataset.mode), button.dataset.special));
    });
    $("titleButton").addEventListener("click", showTitle);
    $("retryButton").addEventListener("click", () => startGame(state.mode, state.special));
    $("changeModeButton").addEventListener("click", showTitle);
    window.addEventListener("keydown", onPhysicalKey);
    window.addEventListener("resize", scheduleResize, { passive: true });
    buildKeyboard();
  }

  function setDifficulty(value) {
    state.difficulty = value === "hard" ? "hard" : "easy";
    document.querySelectorAll(".difficulty").forEach((button) => {
      const selected = button.dataset.difficulty === state.difficulty;
      button.classList.toggle("active", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
  }

  function modeLabel() {
    const name = state.special === "normal" ? MODES.normal.name[state.mode] : MODES[state.special].name;
    return `${state.difficulty.toUpperCase()} ${name}`;
  }

  function maxTries(mode, special) {
    return special === "normal" ? mode + 5 : MODES[special].tries;
  }

  function startGame(mode, special = "normal") {
    clearRun();
    if (special === "daily") setDifficulty("easy");
    state.runId += 1;
    state.mode = mode;
    state.special = special;
    state.maxTries = maxTries(mode, special);
    state.tries = 0;
    state.current = "";
    state.targets = special === "daily" ? pickDaily(mode) : pickRandom(mode);
    $("app").dataset.dailyPuzzle = special === "daily" ? hashString(state.targets.join("|")).toString(36) : "";
    state.solved = Array(mode).fill(false);
    state.history = [];
    state.keyStatus = {};
    state.over = false;
    state.busy = false;
    state.timedOut = false;
    state.timeLeft = special === "time" ? 180 : 0;

    $("titleScreen").hidden = true;
    $("gameScreen").hidden = false;
    $("resultVeil").hidden = true;
    $("modeName").textContent = modeLabel();
    clearKeyboard();
    buildBoards();
    setMessage(startMessage());
    prepareBossTurn();
    updateMeters();
    requestAnimationFrame(adjustBoardSize);
    if (special === "time") startTimer();
  }

  function showTitle() {
    clearRun();
    state.runId += 1;
    state.over = true;
    state.busy = false;
    $("resultVeil").hidden = true;
    $("gameScreen").hidden = true;
    $("titleScreen").hidden = false;
  }

  function clearRun() {
    stopTimer();
    state.scheduled.forEach(clearTimeout);
    state.scheduled = [];
    clearBossBan();
  }

  function startMessage() {
    if (state.special === "boss") return "BOSS — 3手ごとに2文字が封印されます。";
    if (state.special === "blind") return "BLIND — 緑以外の手がかりは消えていきます。";
    if (state.special === "time") return "TIME — 3分以内に4面を攻略。クリアごとに+10秒。";
    if (state.special === "daily") return `${japanDateKey()} — 今日の4ワード。`;
    return "5文字の英単語を入力してください。";
  }

  function answerPool() {
    return state.difficulty === "hard" ? HARD_WORDS : EASY_WORDS;
  }

  function pickRandom(count) {
    const pool = answerPool();
    if (pool.length < count) throw new Error("Answer pool is too small");
    return shuffle(pool).slice(0, count);
  }

  function pickDaily(count) {
    const seed = hashString(`WLR-DICT-4|${japanDateKey()}`);
    return seededShuffle(EASY_WORDS, seed).slice(0, count);
  }

  function japanDateKey(date = new Date()) {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Tokyo", year: "numeric", month: "2-digit", day: "2-digit"
    }).formatToParts(date);
    const byType = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return `${byType.year}-${byType.month}-${byType.day}`;
  }

  function hashString(text) {
    let hash = 2166136261;
    for (let i = 0; i < text.length; i += 1) {
      hash ^= text.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return hash >>> 0;
  }

  function seededShuffle(values, seed) {
    const array = [...values];
    let value = seed || 1;
    for (let i = array.length - 1; i > 0; i -= 1) {
      value = Math.imul(1664525, value) + 1013904223;
      const j = (value >>> 0) % (i + 1);
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }

  function shuffle(values) {
    const array = [...values];
    for (let i = array.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }

  function buildBoards() {
    const fragment = document.createDocumentFragment();
    $("boards").replaceChildren();
    for (let boardIndex = 0; boardIndex < state.mode; boardIndex += 1) {
      const board = document.createElement("section");
      board.className = "board";
      board.dataset.board = boardIndex;
      board.setAttribute("aria-label", `Board ${boardIndex + 1}`);
      for (let rowIndex = 0; rowIndex < state.maxTries; rowIndex += 1) {
        const row = document.createElement("div");
        row.className = "row";
        row.dataset.row = rowIndex;
        for (let column = 0; column < 5; column += 1) {
          const tile = document.createElement("span");
          tile.className = "tile";
          tile.dataset.column = column;
          row.appendChild(tile);
        }
        board.appendChild(row);
      }
      fragment.appendChild(board);
    }
    $("boards").appendChild(fragment);
  }

  function tileAt(board, row, column) {
    return document.querySelector(`.board[data-board="${board}"] .row[data-row="${row}"] .tile[data-column="${column}"]`);
  }

  function renderCurrent(bump = false) {
    for (let board = 0; board < state.mode; board += 1) {
      if (state.solved[board]) continue;
      for (let column = 0; column < 5; column += 1) {
        const tile = tileAt(board, state.tries, column);
        if (!tile) continue;
        tile.textContent = state.current[column] || "";
        tile.classList.toggle("filled", Boolean(state.current[column]));
        if (bump && column === state.current.length - 1) restartAnimation(tile, "bump");
      }
    }
  }

  function buildKeyboard() {
    const rows = [
      { className: "one", keys: [..."QWERTYUIOP", "BACK"] },
      { className: "two", keys: ["SPACER", ..."ASDFGHJKL", "ENTER", "SPACER"] },
      { className: "three", keys: ["SPACER", ..."ZXCVBNM", "SPACER"] }
    ];
    const fragment = document.createDocumentFragment();
    rows.forEach((definition) => {
      const row = document.createElement("div");
      row.className = `kb-row ${definition.className}`;
      definition.keys.forEach((key) => {
        if (key === "SPACER") {
          const spacer = document.createElement("span");
          spacer.setAttribute("aria-hidden", "true");
          row.appendChild(spacer);
          return;
        }
        const button = document.createElement("button");
        button.type = "button";
        button.className = `key${key.length > 1 ? " action" : ""}`;
        button.dataset.key = key;
        button.textContent = key === "BACK" ? "DEL" : key;
        if (key === "BACK") button.setAttribute("aria-label", "Delete");
        if (key === "ENTER") button.setAttribute("aria-label", "Enter guess");
        button.addEventListener("click", () => handleInput(key));
        row.appendChild(button);
      });
      fragment.appendChild(row);
    });
    $("keyboard").replaceChildren(fragment);
  }

  function onPhysicalKey(event) {
    if (event.ctrlKey || event.metaKey || event.altKey || $("gameScreen").hidden) return;
    if (event.key === "Enter") {
      event.preventDefault(); handleInput("ENTER");
    } else if (event.key === "Backspace" || event.key === "Delete") {
      event.preventDefault(); handleInput("BACK");
    } else if (/^[a-zA-Z]$/.test(event.key)) {
      handleInput(event.key.toUpperCase());
    }
  }

  function handleInput(key) {
    if (state.over || state.busy) return;
    unlockAudio();
    if (key === "ENTER") return submitGuess();
    if (key === "BACK") {
      state.current = state.current.slice(0, -1);
      renderCurrent();
      tone(132, .035, "square", .025);
      return;
    }
    if (!/^[A-Z]$/.test(key) || state.current.length >= 5) return;
    if (state.bossBan.includes(key)) {
      reject(`${key} はこの手では封印されています。`);
      return;
    }
    state.current += key;
    renderCurrent(true);
    tone(210 + state.current.length * 18, .025, "square", .018);
  }

  function submitGuess() {
    if (state.current.length !== 5) return reject("5文字入力してください。");
    if (!VALID_WORDS.has(state.current)) return reject("Not in word list.");
    state.busy = true;
    const run = state.runId;
    const guess = state.current;
    const results = Array(state.mode).fill(null);
    let solvedNow = 0;

    clearBossBan();
    for (let board = 0; board < state.mode; board += 1) {
      if (state.solved[board]) continue;
      const result = judge(guess, state.targets[board]);
      results[board] = result;
      result.forEach((mark, column) => {
        const tile = tileAt(board, state.tries, column);
        schedule(() => {
          if (run !== state.runId || !tile) return;
          tile.classList.add("flip");
          schedule(() => {
            if (run !== state.runId || !tile) return;
            tile.classList.add(mark);
            if (state.special !== "blind" || mark === "correct") updateKey(guess[column], mark);
            if (state.special === "blind" && mark !== "correct") schedule(() => tile.classList.add("veiled"), 500);
          }, 150);
        }, column * 55);
      });
      if (guess === state.targets[board]) {
        state.solved[board] = true;
        solvedNow += 1;
        schedule(() => document.querySelector(`.board[data-board="${board}"]`)?.classList.add("solved"), 420);
      }
    }
    state.history.push({ guess, results });

    schedule(() => {
      if (run !== state.runId) return;
      state.tries += 1;
      state.current = "";
      if (solvedNow) {
        if (state.special === "time") state.timeLeft = applyTimeBonus(state.timeLeft, solvedNow);
        flash(true);
        successTone();
        setMessage(solvedNow === 1 ? "1面クリア。" : `${solvedNow}面を同時クリア。`);
      } else {
        tone(98, .07, "sawtooth", .035);
        setMessage("手がかりを更新しました。");
      }
      updateMeters();
      const finished = checkEnd();
      if (!finished) prepareBossTurn();
      state.busy = false;
    }, 570);
  }

  function judge(guess, target) {
    const result = Array(5).fill("absent");
    const remainingTarget = target.split("");
    const remainingGuess = guess.split("");
    for (let i = 0; i < 5; i += 1) {
      if (remainingGuess[i] === remainingTarget[i]) {
        result[i] = "correct";
        remainingGuess[i] = null;
        remainingTarget[i] = null;
      }
    }
    for (let i = 0; i < 5; i += 1) {
      if (!remainingGuess[i]) continue;
      const match = remainingTarget.indexOf(remainingGuess[i]);
      if (match >= 0) {
        result[i] = "present";
        remainingTarget[match] = null;
      }
    }
    return result;
  }

  function updateKey(letter, mark) {
    const rank = { absent: 1, present: 2, correct: 3 };
    if ((rank[state.keyStatus[letter]] || 0) >= rank[mark]) return;
    state.keyStatus[letter] = mark;
    const key = document.querySelector(`.key[data-key="${letter}"]`);
    key?.classList.remove("absent", "present", "correct");
    key?.classList.add(mark);
  }

  function clearKeyboard() {
    document.querySelectorAll(".key").forEach((key) => key.classList.remove("absent", "present", "correct", "banned"));
  }

  function prepareBossTurn() {
    clearBossBan();
    if (state.special !== "boss" || state.over || (state.tries + 1) % 3 !== 0) return;
    const letters = [..."ETAOINSHRDLUCMFYWGPBVK"];
    state.bossBan = shuffle(letters).slice(0, 2).join("");
    [...state.bossBan].forEach((letter) => document.querySelector(`.key[data-key="${letter}"]`)?.classList.add("banned"));
    setMessage(`BOSS SHIELD — ${[...state.bossBan].join(" / ")} を封印。`);
    updateMeters();
  }

  function clearBossBan() {
    document.querySelectorAll(".key.banned").forEach((key) => key.classList.remove("banned"));
    state.bossBan = "";
  }

  function checkEnd() {
    const won = state.solved.every(Boolean);
    const exhausted = state.tries >= state.maxTries;
    if (!won && !exhausted) return false;
    state.over = true;
    state.busy = true;
    schedule(() => showResult(won), 350);
    return true;
  }

  function applyTimeBonus(seconds, solvedCount) {
    return seconds + solvedCount * 10;
  }

  function startTimer() {
    stopTimer();
    state.timerId = setInterval(() => {
      if (state.over) return;
      state.timeLeft -= 1;
      updateMeters();
      if (state.timeLeft <= 0) {
        state.timeLeft = 0;
        state.timedOut = true;
        state.over = true;
        state.busy = true;
        showResult(false);
      }
    }, 1000);
  }

  function stopTimer() {
    if (state.timerId) clearInterval(state.timerId);
    state.timerId = null;
  }

  function showResult(won) {
    stopTimer();
    $("resultMode").textContent = modeLabel();
    $("resultTitle").textContent = state.timedOut ? "TIME UP" : won ? "CLEAR" : "FAILED";
    $("resultScore").textContent = won ? `${state.tries} / ${state.maxTries}` : `${state.solved.filter(Boolean).length} / ${state.mode} SOLVED`;
    const list = document.createDocumentFragment();
    state.targets.forEach((word) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "answer-chip";
      button.textContent = word;
      button.setAttribute("aria-expanded", "false");
      button.addEventListener("click", () => showDefinition(word, button));
      list.appendChild(button);
    });
    $("answerList").replaceChildren(list);
    $("definition").innerHTML = '<span class="definition-empty">単語を選ぶと日本語の意味が表示されます。</span>';
    $("resultVeil").hidden = false;
    if (won) winTone();
    requestAnimationFrame(() => $("retryButton").focus({ preventScroll: true }));
  }

  function showDefinition(word, button) {
    const entry = WORD_BY_TEXT.get(word);
    document.querySelectorAll(".answer-chip").forEach((chip) => chip.setAttribute("aria-expanded", String(chip === button)));
    $("definition").replaceChildren();
    const title = document.createElement("strong");
    const meaning = document.createElement("span");
    title.textContent = entry.word;
    meaning.textContent = entry.ja.join("／");
    $("definition").append(title);
    if (entry.pos) {
      const pos = document.createElement("em");
      pos.textContent = entry.pos;
      $("definition").append(pos);
    }
    $("definition").append(meaning);
    $("definition").focus({ preventScroll: true });
  }

  function updateMeters() {
    $("turnMeter").textContent = `TRY ${Math.min(state.tries + 1, state.maxTries)} / ${state.maxTries}`;
    if (state.special === "time") {
      const minutes = Math.floor(state.timeLeft / 60);
      const seconds = String(state.timeLeft % 60).padStart(2, "0");
      $("smallStatus").textContent = `TIME ${minutes}:${seconds} · ${state.solved.filter(Boolean).length}/${state.mode}`;
    } else if (state.bossBan) {
      $("smallStatus").textContent = `${[...state.bossBan].join(" / ")} SEALED`;
    } else {
      $("smallStatus").textContent = `${state.solved.filter(Boolean).length} / ${state.mode} SOLVED`;
    }
  }

  function reject(message) {
    setMessage(message);
    document.querySelectorAll(`.row[data-row="${state.tries}"]`).forEach((row) => restartAnimation(row, "shake"));
    flash(false);
    tone(82, .1, "square", .045);
  }

  function setMessage(text) { $("message").textContent = text; }
  function restartAnimation(element, className) {
    element.classList.remove(className); void element.offsetWidth; element.classList.add(className);
  }
  function flash(good) {
    const zone = $("boardZone");
    restartAnimation(zone, good ? "good" : "bad");
  }

  function schedule(callback, delay) {
    const id = setTimeout(() => {
      state.scheduled = state.scheduled.filter((item) => item !== id);
      callback();
    }, delay);
    state.scheduled.push(id);
    return id;
  }

  let resizeFrame = 0;
  function scheduleResize() {
    cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(adjustBoardSize);
  }

  function adjustBoardSize() {
    if ($("gameScreen").hidden) return;
    const zone = $("boardZone");
    const width = Math.max(300, zone.clientWidth - 10);
    const height = Math.max(140, zone.clientHeight - 10);
    const narrow = width <= 720;
    const columns = state.mode >= 5 ? 3 : narrow && state.mode >= 3 ? 2 : state.mode;
    const boardRows = Math.ceil(state.mode / columns);
    const gap = width <= 390 ? 3 : 5;
    const horizontal = (width - Math.max(0, columns - 1) * 8) / columns;
    const vertical = (height - Math.max(0, boardRows - 1) * 8) / boardRows;
    const byWidth = (horizontal - 14 - gap * 4) / 5;
    const byHeight = (vertical - 14 - gap * (state.maxTries - 1)) / state.maxTries;
    const minimum = state.mode >= 5 ? 18 : 20;
    const tile = Math.floor(Math.min(46, byWidth, byHeight));
    const needsScroll = tile < minimum;
    document.documentElement.style.setProperty("--tile", `${Math.max(minimum, tile)}px`);
    document.documentElement.style.setProperty("--tile-gap", `${gap}px`);
    document.documentElement.style.setProperty("--board-cols", String(columns));
    zone.classList.toggle("scroll", needsScroll);
  }

  function unlockAudio() {
    try {
      if (!state.audioContext) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        state.audioContext = new AudioCtx();
      }
      if (state.audioContext.state === "suspended") state.audioContext.resume();
    } catch (_) { state.audioContext = null; }
  }

  function tone(frequency, duration, type = "square", gainValue = .025, delay = 0) {
    const ctx = state.audioContext;
    if (!ctx) return;
    try {
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.type = type; oscillator.frequency.value = frequency;
      gain.gain.setValueAtTime(gainValue, ctx.currentTime + delay);
      gain.gain.exponentialRampToValueAtTime(.0001, ctx.currentTime + delay + duration);
      oscillator.connect(gain).connect(ctx.destination);
      oscillator.start(ctx.currentTime + delay); oscillator.stop(ctx.currentTime + delay + duration);
    } catch (_) {}
  }

  function successTone() { tone(392, .08, "square", .025); tone(523, .1, "square", .025, .07); }
  function winTone() { [392, 494, 587, 784].forEach((frequency, index) => tone(frequency, .15, "triangle", .035, index * .09)); }

  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", boot) : boot();
})();
