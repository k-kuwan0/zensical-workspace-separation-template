#!/usr/bin/env node
// browser_check.mjs の新旧の出力から、スクリーンショットを左右に並べた比較画像を作る。
//
// PR に確認の根拠として貼るための画像を用意する。GitHub には画像を API で PR に添付する手段が無いため、
// できた画像は作成者がブラウザで PR のコメントにドラッグ＆ドロップする。手順全体はリポジトリ直下の
// .claude/skills/zensical-upgrade/SKILL.md を参照。外部パッケージは使わず、Chrome のヘッドレスモードの
// --screenshot で、2 枚の画像を並べた HTML を撮影する。
//
// 出力（OUT_DIR 配下）:
//   <元のファイル名>.png : 左に変更前、右に変更後を並べた画像（両方にある PNG ごとに 1 枚）
//
// 使い方（ホスト側で実行。コンテナにはブラウザが無い）:
//   node ssg/scripts/compare_shots.mjs <BEFORE_DIR> <AFTER_DIR> <OUT_DIR> [変更前の見出し] [変更後の見出し]
//   node ssg/scripts/compare_shots.mjs before after compare 0.0.46 0.1.0

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const [beforeDir, afterDir, outDir, beforeLabel = "変更前", afterLabel = "変更後"] = process.argv.slice(2);
if (!beforeDir || !afterDir || !outDir) {
  console.error("usage: node compare_shots.mjs <BEFORE_DIR> <AFTER_DIR> <OUT_DIR> [BEFORE_LABEL] [AFTER_LABEL]");
  process.exit(2);
}
mkdirSync(outDir, { recursive: true });

// PNG の幅と高さは IHDR チャンク（先頭から 16〜23 バイト目）にある
const size = (file) => {
  const buf = readFileSync(file);
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
};

const GAP = 20;
const HEADER = 40;
const work = mkdtempSync(join(tmpdir(), "compare-shots-"));
const files = readdirSync(beforeDir).filter((f) => f.endsWith(".png") && existsSync(join(afterDir, f))).sort();
if (files.length === 0) {
  console.error("error: 新旧の両方にある PNG がありません");
  process.exit(2);
}

for (const file of files) {
  const before = resolve(beforeDir, file);
  const after = resolve(afterDir, file);
  const a = size(before);
  const b = size(after);
  const width = a.width + b.width + GAP;
  const height = Math.max(a.height, b.height) + HEADER;
  const same = readFileSync(before).equals(readFileSync(after));
  const cell = (label, src) =>
    `<figure><figcaption>${label}</figcaption><img src="${pathToFileURL(src).href}"></figure>`;
  const html = `<!doctype html><meta charset="utf-8"><style>
    body { margin: 0; display: flex; gap: ${GAP}px; background: #888; font: bold 20px sans-serif; }
    figure { margin: 0; }
    figcaption { height: ${HEADER}px; line-height: ${HEADER}px; padding-left: 8px; color: #fff; }
    img { display: block; }
  </style>${cell(`${beforeLabel}  ${file}`, before)}${cell(`${afterLabel}  ${file}${same ? "（同一）" : ""}`, after)}`;
  const page = join(work, "page.html");
  writeFileSync(page, html);
  const out = resolve(outDir, file);
  const r = spawnSync(CHROME, [
    "--headless=new",
    `--user-data-dir=${join(work, "profile")}`,
    "--hide-scrollbars",
    "--allow-file-access-from-files",
    "--force-device-scale-factor=1",
    `--window-size=${width},${height}`,
    `--screenshot=${out}`,
    pathToFileURL(page).href,
  ], { stdio: "ignore" });
  if (r.status !== 0 || !existsSync(out)) {
    console.error(`error: ${file} の比較画像を作れません（${CHROME}）。CHROME 環境変数でパスを指定してください`);
    rmSync(work, { recursive: true, force: true });
    process.exit(2);
  }
  console.log(`${file}${same ? "（新旧で同一）" : ""}`);
}

rmSync(work, { recursive: true, force: true });
console.log(`出力: ${outDir}（${files.length} 枚）`);
