import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { execFileSync } from "node:child_process";

const root = path.resolve(import.meta.dirname, "..");
const dist = path.join(root, "dist");
const wordsSource = fs.readFileSync(path.join(dist, "assets/words.js"), "utf8");
const fixesSource = fs.readFileSync(path.join(dist, "assets/metadata-fixes.js"), "utf8");
const exclusionsSource = fs.readFileSync(path.join(dist, "assets/answer-exclusions.js"), "utf8");
const gameSource = fs.readFileSync(path.join(dist, "assets/game.js"), "utf8");
const indexSource = fs.readFileSync(path.join(dist, "index.html"), "utf8");
const styleSource = fs.readFileSync(path.join(dist, "assets/styles.css"), "utf8");

const dictionaryContext = vm.createContext({ window: {} });
vm.runInContext(wordsSource, dictionaryContext);
vm.runInContext(fixesSource, dictionaryContext);
vm.runInContext(exclusionsSource, dictionaryContext);
const entries = dictionaryContext.window.WORD_DATA;
const exclusions = new Set(dictionaryContext.window.ANSWER_EXCLUSIONS || []);
if (!Array.isArray(entries)) throw new Error("Canonical dictionary payload not found");

const keys = new Set();
const easy = new Set();
const hard = new Set();
const byWord = new Map();
for (const entry of entries) {
  if (!Array.isArray(entry) || entry.length !== 4) throw new Error(`Bad entry: ${JSON.stringify(entry)}`);
  const [word, level, pos, ja] = entry;
  if (!/^[A-Z]{5}$/.test(word)) throw new Error(`Bad word: ${word}`);
  if (!/[eh]/.test(level) || level.length !== 1) throw new Error(`Bad level: ${word}`);
  if (keys.has(word)) throw new Error(`Duplicate: ${word}`);
  if (typeof pos !== "string" || typeof ja !== "string" || !ja.trim()) throw new Error(`Missing metadata: ${word}`);
  if (pos === "word") throw new Error(`Generic POS remains: ${word}`);
  keys.add(word);
  byWord.set(word, { level, pos, ja });
  (level === "e" ? easy : hard).add(word);
}
if (entries.length !== keys.size || keys.size !== easy.size + hard.size) throw new Error("Dictionary union invariant failed");
if (keys.size < 2400 || keys.size > 3000) throw new Error(`Expanded dictionary outside release range: ${keys.size}`);
if ([...easy].some((word) => hard.has(word))) throw new Error("EASY/HARD overlap");
for (const word of exclusions) if (!keys.has(word)) throw new Error(`Answer exclusion is not a valid word: ${word}`);

const easyAnswers = new Set([...easy].filter((word) => !exclusions.has(word)));
const hardAnswers = new Set([...hard].filter((word) => !exclusions.has(word)));
if (easyAnswers.size < 700 || hardAnswers.size < 1500) {
  throw new Error(`Filtered answer pools are below release threshold: EASY ${easyAnswers.size}, HARD ${hardAnswers.size}`);
}
if (!keys.has("WEEKS") || !exclusions.has("WEEKS")) throw new Error("WEEKS must remain a valid guess but not an answer candidate");

const commonRequired = "APPLE HOUSE WORLD LIGHT TRAIN BRAIN MUSIC MONEY WATER BEACH PHONE WRITE DRINK LEARN TEACH SPEAK DRIVE HAPPY SMALL BLACK WHITE CLEAN SWEET THEIR THERE THESE EMAIL BOOKS WOMEN TODAY THREE THINK GREAT RIGHT SHEEP SMELL PIZZA JUICE DIARY PANDA SALAD SUNNY RAINY LUCKY TIRED TOOTH TOWEL".split(" ");
const hardRequired = "ACRID GUILE KNAVE MIDGE QUAFF SEDGE SHREW VIXEN WHELP".split(" ");
for (const word of commonRequired) if (!keys.has(word)) throw new Error(`Missing common valid guess: ${word}`);
for (const word of hardRequired) if (!hardAnswers.has(word)) throw new Error(`Missing required HARD answer: ${word}`);

const exactMetadata = {
  CHEEK: ["noun", "頬"],
  DIRTY: ["adjective", "汚い／汚れた"],
  ENTER: ["verb", "入る／入力する"],
  NEVER: ["adverb", "決して〜ない"],
  QUEEN: ["noun", "女王"],
  SHEEP: ["noun", "羊"],
  TRASH: ["noun/verb", "ごみ／捨てる"],
  USURY: ["noun", "高利貸し／高利"],
  WEIRD: ["adjective", "奇妙な／変な"]
};
for (const [word, [pos, ja]] of Object.entries(exactMetadata)) {
  const actual = byWord.get(word);
  if (!actual || actual.pos !== pos || actual.ja !== ja) throw new Error(`Metadata regression: ${word}`);
}
const schoolUnsafeFragments = ["気違い", "うんこ", "デブ", "百姓", "馬鹿", "禿", "ちんこ", "チンコ", "まんこ", "マンコ"];
for (const [word, data] of byWord) {
  for (const fragment of schoolUnsafeFragments) {
    if (data.ja.includes(fragment)) throw new Error(`School-unsafe gloss remains: ${word} -> ${data.ja}`);
  }
}

const networkTokens = [/\bfetch\s*\(/, /XMLHttpRequest/, /WebSocket/, /EventSource/, /datamuse/i, /https?:\/\//];
for (const [name, source] of [
  ["index.html", indexSource], ["styles.css", styleSource], ["game.js", gameSource],
  ["words.js", wordsSource], ["metadata-fixes.js", fixesSource], ["answer-exclusions.js", exclusionsSource]
]) {
  for (const token of networkTokens) if (token.test(source)) throw new Error(`Runtime network token ${token} in ${name}`);
}
for (const ref of [...indexSource.matchAll(/(?:src|href)="([^"]+)"/g)].map((item) => item[1])) {
  if (ref.startsWith("data:")) continue;
  if (/^(?:https?:)?\/\//.test(ref)) throw new Error(`External asset reference: ${ref}`);
  const target = path.resolve(dist, ref.split("#")[0]);
  if (!fs.existsSync(target)) throw new Error(`Missing local asset: ${ref}`);
}
const loadOrder = ["assets/words.js", "assets/metadata-fixes.js", "assets/answer-exclusions.js", "assets/game.js"].map((name) => indexSource.indexOf(name));
if (loadOrder.some((index) => index < 0) || !(loadOrder[0] < loadOrder[1] && loadOrder[1] < loadOrder[2] && loadOrder[2] < loadOrder[3])) {
  throw new Error("Dictionary/answer-policy asset load order is invalid");
}

execFileSync(process.execPath, ["--check", path.join(dist, "assets/game.js")], { stdio: "inherit" });
execFileSync(process.execPath, ["--check", path.join(dist, "assets/metadata-fixes.js")], { stdio: "inherit" });
execFileSync(process.execPath, ["--check", path.join(dist, "assets/answer-exclusions.js")], { stdio: "inherit" });
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
if (!audit.includes("Remaining candidates: none")) throw new Error("Coverage audit is unresolved");
const expansionReport = path.join(root, "docs/dictionary-expansion-report.md");
if (!fs.existsSync(expansionReport)) throw new Error("Dictionary expansion report missing");
const answerPolicyReport = path.join(root, "docs/answer-policy-report.md");
if (!fs.existsSync(answerPolicyReport)) throw new Error("Answer policy report missing");

console.log(JSON.stringify({
  status: "ok", total: keys.size, easy: easy.size, hard: hard.size,
  easyAnswers: easyAnswers.size, hardAnswers: hardAnswers.size, answerExcluded: exclusions.size,
  duplicateLetterCases: cases.length, runtimeExternalCalls: 0,
  metadataFixLayer: true, optionalPos: true, expansionReport: true, answerPolicyReport: true
}));
