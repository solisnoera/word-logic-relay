import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { execFileSync } from "node:child_process";

const root = path.resolve(import.meta.dirname, "..");
const dist = path.join(root, "dist");
const wordsSource = fs.readFileSync(path.join(dist, "assets/words.js"), "utf8");
const gameSource = fs.readFileSync(path.join(dist, "assets/game.js"), "utf8");
const indexSource = fs.readFileSync(path.join(dist, "index.html"), "utf8");
const styleSource = fs.readFileSync(path.join(dist, "assets/styles.css"), "utf8");

const match = wordsSource.match(/window\.WORD_DATA=(\[[\s\S]*\]);/);
if (!match) throw new Error("Canonical dictionary payload not found");
const entries = JSON.parse(match[1]);
const keys = new Set();
const easy = new Set();
const hard = new Set();
for (const entry of entries) {
  if (!Array.isArray(entry) || entry.length !== 4) throw new Error(`Bad entry: ${JSON.stringify(entry)}`);
  const [word, level, pos, ja] = entry;
  if (!/^[A-Z]{5}$/.test(word)) throw new Error(`Bad word: ${word}`);
  if (!/[eh]/.test(level) || level.length !== 1) throw new Error(`Bad level: ${word}`);
  if (keys.has(word)) throw new Error(`Duplicate: ${word}`);
  if (!pos.trim() || !ja.trim()) throw new Error(`Missing metadata: ${word}`);
  keys.add(word); (level === "e" ? easy : hard).add(word);
}
if (entries.length !== keys.size || keys.size !== easy.size + hard.size) throw new Error("Dictionary union invariant failed");
if ([...easy].some((word) => hard.has(word))) throw new Error("EASY/HARD overlap");
if (easy.size < 650 || hard.size < 650) throw new Error("Answer pools are below release threshold");

const commonRequired = "APPLE HOUSE WORLD LIGHT TRAIN BRAIN MUSIC MONEY WATER BEACH PHONE WRITE DRINK LEARN TEACH SPEAK DRIVE HAPPY SMALL BLACK WHITE CLEAN SWEET THEIR THERE THESE EMAIL BOOKS WOMEN TODAY THREE THINK GREAT RIGHT".split(" ");
const hardRequired = "ACRID GUILE KNAVE MIDGE QUAFF SEDGE SHREW VIXEN WHELP".split(" ");
for (const word of commonRequired) if (!easy.has(word)) throw new Error(`Missing common EASY word: ${word}`);
for (const word of hardRequired) if (!hard.has(word)) throw new Error(`Missing required HARD word: ${word}`);

const networkTokens = [/\bfetch\s*\(/, /XMLHttpRequest/, /WebSocket/, /EventSource/, /datamuse/i, /https?:\/\//];
for (const [name, source] of [["index.html", indexSource], ["styles.css", styleSource], ["game.js", gameSource], ["words.js", wordsSource]]) {
  for (const token of networkTokens) if (token.test(source)) throw new Error(`Runtime network token ${token} in ${name}`);
}
for (const ref of [...indexSource.matchAll(/(?:src|href)="([^"]+)"/g)].map((item) => item[1])) {
  if (ref.startsWith("data:")) continue;
  if (/^(?:https?:)?\/\//.test(ref)) throw new Error(`External asset reference: ${ref}`);
  const target = path.resolve(dist, ref.split("#")[0]);
  if (!fs.existsSync(target)) throw new Error(`Missing local asset: ${ref}`);
}

execFileSync(process.execPath, ["--check", path.join(dist, "assets/game.js")], { stdio: "inherit" });
const judgeMatch = gameSource.match(/function judge\(guess, target\) \{[\s\S]*?\n  \}/);
if (!judgeMatch) throw new Error("Judge implementation not found");
const context = vm.createContext({});
vm.runInContext(`${judgeMatch[0]};globalThis.judge=judge;`, context);
const cases = [
  ["APPLE", "ALLEY", ["correct", "absent", "absent", "present", "present"]],
  ["ALLOT", "APPLE", ["correct", "present", "absent", "absent", "absent"]],
  ["GEESE", "EERIE", ["absent", "correct", "present", "absent", "correct"]]
];
for (const [guess, target, expected] of cases) {
  const actual = Array.from(context.judge(guess, target));
  if (JSON.stringify(actual) !== JSON.stringify(expected)) throw new Error(`Judge failed ${guess}/${target}: ${actual}`);
}
const bonusMatch = gameSource.match(/function applyTimeBonus\(seconds, solvedCount\) \{[\s\S]*?\n  \}/);
if (!bonusMatch) throw new Error("TIME bonus implementation not found");
vm.runInContext(`${bonusMatch[0]};globalThis.applyTimeBonus=applyTimeBonus;`, context);
if (context.applyTimeBonus(179, 1) !== 189 || context.applyTimeBonus(42, 3) !== 72) throw new Error("TIME bonus failed");

const audit = fs.readFileSync(path.join(root, "docs/dictionary-audit.md"), "utf8");
if (!audit.includes("Remaining plausible/valid candidates not added: 0")) throw new Error("Coverage audit is unresolved");
console.log(JSON.stringify({ status: "ok", total: keys.size, easy: easy.size, hard: hard.size, duplicateLetterCases: cases.length, runtimeExternalCalls: 0 }));
