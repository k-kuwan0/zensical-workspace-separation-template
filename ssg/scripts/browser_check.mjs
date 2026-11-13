#!/usr/bin/env node
// プレビュー中のサイトをヘッドレス Chrome で開き、見た目と日本語検索を確認するための材料を保存する。
//
// Zensical のアップグレード前後で実行し、出力を見比べる。手順全体はリポジトリ直下の
// .claude/skills/zensical-upgrade/SKILL.md を参照。外部パッケージは使わず、Chrome DevTools
// Protocol（CDP）を Node 標準の fetch / WebSocket で直接操作する（Node 22 以降）。
//
// 確認するページ・検索語・自前 JS のテーブル確認の有無は browser_check.config.json で指定する。
// サイトの構成が変わったら（カスタマイズを追加したら）設定ファイルを更新する。
//
// 出力（OUT_DIR 配下）:
//   page-<名前>-<light|dark>.png : 各ページのスクリーンショット
//   search-<番号>.png            : 検索結果のスクリーンショット
//   result.json                  : 検索ごとのヒット件数と、検索 UI に表示された文言の抜粋、
//                                  自前 JS のテーブルソートが動いたか
//
// 使い方（ホスト側で実行。コンテナにはブラウザが無い）:
//   node ssg/scripts/browser_check.mjs http://localhost:8001 /tmp/check-before
//   CHROME=/path/to/chrome node ssg/scripts/browser_check.mjs <BASE_URL> <OUT_DIR>

import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const CONFIG_PATH = join(dirname(fileURLToPath(import.meta.url)), "browser_check.config.json");
const { pages: PAGES, queries: QUERIES, sortTable: SORT_TABLE } = JSON.parse(readFileSync(CONFIG_PATH, "utf-8"));

const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9333;
const [baseUrl, outDir] = process.argv.slice(2);
if (!baseUrl || !outDir) {
  console.error("usage: node browser_check.mjs <BASE_URL> <OUT_DIR>");
  process.exit(2);
}
mkdirSync(outDir, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const profile = mkdtempSync(join(tmpdir(), "browser-check-"));
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });

let targets;
for (let i = 0; i < 50 && !targets; i++) {
  try {
    targets = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
  } catch {
    await sleep(200);
  }
}
if (!targets) {
  console.error(`error: Chrome を起動できません（${CHROME}）。CHROME 環境変数でパスを指定してください`);
  chrome.kill();
  process.exit(2);
}

const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));
let seq = 0;
const pending = new Map();
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) {
    pending.get(m.id)(m.result);
    pending.delete(m.id);
  }
});
const send = (method, params = {}) =>
  new Promise((r) => {
    const id = ++seq;
    pending.set(id, r);
    ws.send(JSON.stringify({ id, method, params }));
  });
const evaluate = async (expression) =>
  (await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true }))?.result?.value;
const screenshot = async (file) => {
  const { data } = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(outDir, file), Buffer.from(data, "base64"));
};
// テーマ（ライト / ダーク）の選択は localStorage に保存され、prefers-color-scheme より優先される。
// 前のページの選択を引き継がないよう、毎回消してから読み直す。
const open = async (path) => {
  await send("Page.navigate", { url: new URL(path, baseUrl).href });
  await sleep(1000);
  await evaluate(`localStorage.clear()`);
  await send("Page.reload");
  await sleep(2500);
};

await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1400, height: 900, deviceScaleFactor: 1, mobile: false });

// 1. ページのスクリーンショット（ライト / ダーク）
for (const scheme of ["light", "dark"]) {
  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: scheme }] });
  for (const [name, { path, focus }] of Object.entries(PAGES)) {
    await open(path);
    if (focus) {
      await evaluate(`document.querySelector(${JSON.stringify(focus)})?.scrollIntoView({ block: "start" })`);
      await sleep(500);
    }
    await screenshot(`page-${name}-${scheme}.png`);
  }
}

// 2. 日本語検索。検索 UI は Shadow DOM 内に描画されるため、textContent から件数と文言を拾う。
await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: "light" }] });
const searches = [];
for (const [i, query] of QUERIES.entries()) {
  await open("/");
  await evaluate(`document.querySelector('.md-search__button')?.click()`);
  await sleep(1000);
  await send("Input.insertText", { text: query });
  await sleep(2500);
  const text = await evaluate(`(() => {
    const roots = [...document.querySelectorAll('*')].filter((e) => e.shadowRoot).map((e) => e.shadowRoot);
    const dialog = document.querySelector('.md-search__output, .md-search-result');
    return (dialog ? dialog.textContent : '') + roots.map((r) => r.textContent).join(' ');
  })()`);
  const clean = (text || "").replace(/\.[\w-]+\{[^}]*\}/g, "").replace(/\s+/g, " ").trim();
  const count = clean.match(/(\d+)\s*(?:results?|件)/);
  searches.push({ query, hits: count ? Number(count[1]) : null, excerpt: clean.slice(0, 300) });
  await screenshot(`search-${i + 1}.png`);
}

// 3. 自前 JS のテーブルソート（ssg/assets/javascripts/tablesort.js）。テーマの document$ に依存して初期化するため、
//    UI の更新で document$ の挙動が変わると動かなくなる。直接開いた場合と、インスタントナビゲーション
//    （サイドバーのリンクから遷移）した場合の両方で確かめる。
const checkSort = () =>
  evaluate(`(async () => {
    const th = document.querySelector('article table:not([class]) th');
    if (!th) return { error: 'article table:not([class]) th が見つからない' };
    th.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    await new Promise((r) => setTimeout(r, 300));
    const ariaSort = th.getAttribute('aria-sort');
    return { ariaSort, sortOk: ariaSort !== null };
  })()`);

const tables = {};
if (SORT_TABLE) {
  await open(SORT_TABLE);
  tables.direct = await checkSort();
  await open("/");
  await evaluate(`[...document.querySelectorAll('a.md-nav__link')].find((a) => a.href.endsWith(${JSON.stringify(SORT_TABLE)}))?.click()`);
  await sleep(2500);
  tables.instant = { url: await evaluate(`location.pathname`), ...(await checkSort()) };
}

writeFileSync(join(outDir, "result.json"), JSON.stringify({ baseUrl, pages: PAGES, searches, tables }, null, 2));
for (const s of searches) console.log(`検索「${s.query}」: ${s.hits ?? "件数不明"}`);
for (const [how, t] of Object.entries(tables)) {
  const label = how === "direct" ? "直接開いた場合" : "サイドバーから遷移した場合";
  console.log(`テーブル（${label}）: ソート ${t.sortOk ? "OK" : "NG"}${t.error ? `、${t.error}` : ""}`);
}
console.log(`出力: ${outDir}`);

ws.close();
chrome.kill();
rmSync(profile, { recursive: true, force: true });
process.exit(0);
