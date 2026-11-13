#!/usr/bin/env python3
"""Zensical のビルド出力（site/）を 2 つ比較し、アップグレードの影響を要約する。

Zensical のバージョンを上げる前後でビルド出力を比べ、「コンテンツに影響する差分が無いか」を
機械的に確認するためのスクリプト。手順全体はリポジトリ直下の
.claude/skills/zensical-upgrade/SKILL.md を参照（記録は notes/zensical-upgrade.md）。

確認する観点:
1. ファイル一覧   : ページ（.html）の増減。テーマアセットのハッシュ付きファイル名
                    （例: bundle.ee611ef6.min.js）はハッシュを除いて比較する。
2. サイドバー     : トップページの primary nav に並ぶ表示名（H1 / front matter title 由来）。
3. HTML 差分      : 全ページを正規化（アセットのハッシュ・generator のバージョン・相対パスの
                    深さ・スキップリンクの飛び先・空白を除去）した上で差分行を集計し、
                    出現回数の多い順に表示する。
                    全ページ共通で出る行はテーマ（UI）由来、少数ページだけの行はコンテンツ
                    由来の可能性が高いので重点的に見る。

使い方（コンテナ内 /ssg で実行）:
    python3 scripts/compare_build.py /tmp/site-before site
    python3 scripts/compare_build.py /tmp/site-before site --top 50   # 表示件数を増やす

終了コード:
    0 = ページ増減・サイドバー差分なし（HTML 差分はあっても 0。内容は目視で判断する）
    1 = ページ増減またはサイドバー差分あり
"""

from __future__ import annotations

import argparse
import collections
import os
import re
import sys

# テーマアセットのハッシュ（bundle.ee611ef6.min.js 等）。比較時は固定文字列に置換する。
_hash_re = re.compile(r"\.[0-9a-f]{8}(\.min\.(?:js|css))")
# <meta name="generator" content="zensical-0.1.0"> のバージョン部分。
_generator_re = re.compile(r"zensical-\d+\.\d+\.\d+")
# ページの階層で変わる相対パス（"../../.." 等）。テーマ由来の行をページ横断で集計するため揃える。
_relpath_re = re.compile(r"\.\.(?:/\.\.)*")
# スキップリンクの飛び先（ページ先頭の見出し ID）。ページごとに変わるため揃える。
_skip_re = re.compile(r'<a href="#[^"]*" class="md-skip">')
# primary nav（サイドバー）の範囲と、その中の表示名。
_nav_re = re.compile(r'<nav class="md-nav md-nav--primary".*?</nav>\s*</div>', re.S)
_label_re = re.compile(r'<span class="md-ellipsis">\s*(.*?)\s*</span>', re.S)


def normalize_name(path: str) -> str:
    return _hash_re.sub(r".HASH\1", path)


def list_files(root: str) -> set[str]:
    files = set()
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            files.add(normalize_name(rel))
    return files


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def nav_labels(site: str) -> list[str]:
    html = read(os.path.join(site, "index.html"))
    m = _nav_re.search(html)
    scope = m.group(0) if m else html
    return [re.sub(r"\s+", " ", t) for t in _label_re.findall(scope)]


def normalized_lines(path: str) -> list[str]:
    html = _hash_re.sub(r".HASH\1", read(path))
    html = _generator_re.sub("zensical-VERSION", html)
    html = _relpath_re.sub("..", html)
    html = _skip_re.sub('<a href="#SKIP" class="md-skip">', html)
    # タグ境界で改行し、行頭末の空白と空行を除く（テンプレートのインデント変更を無視するため）。
    lines = html.replace("><", ">\n<").splitlines()
    return [s for s in (line.strip() for line in lines) if s]


def diff_lines(a: list[str], b: list[str]) -> list[str]:
    """順序を無視した多重集合の差分（- は before のみ、+ は after のみ）。"""
    ca, cb = collections.Counter(a), collections.Counter(b)
    removed = [f"- {line}" for line in (ca - cb).elements()]
    added = [f"+ {line}" for line in (cb - ca).elements()]
    return removed + added


def shorten(line: str, width: int = 160) -> str:
    return line if len(line) <= width else line[: width - 1] + "…"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("before", help="アップグレード前の site ディレクトリ")
    parser.add_argument("after", help="アップグレード後の site ディレクトリ")
    parser.add_argument("--top", type=int, default=30, help="HTML 差分の表示件数（既定: 30）")
    args = parser.parse_args()

    for d in (args.before, args.after):
        if not os.path.isfile(os.path.join(d, "index.html")):
            print(f"error: {d} に index.html がありません", file=sys.stderr)
            return 2

    has_problem = False

    # 1. ファイル一覧
    before_files, after_files = list_files(args.before), list_files(args.after)
    before_pages = {f for f in before_files if f.endswith(".html")}
    after_pages = {f for f in after_files if f.endswith(".html")}
    print("## 1. ファイル一覧")
    print(f"ページ数: {len(before_pages)} -> {len(after_pages)}")
    for label, files in (("削除", before_files - after_files), ("追加", after_files - before_files)):
        for f in sorted(files):
            print(f"  {label}: {f}")
    if before_pages != after_pages:
        has_problem = True

    # 2. サイドバー
    before_nav, after_nav = nav_labels(args.before), nav_labels(args.after)
    print("\n## 2. サイドバーの表示名")
    print(f"項目数: {len(before_nav)} -> {len(after_nav)}")
    if before_nav == after_nav:
        print("  差分なし")
    else:
        has_problem = True
        for line in diff_lines(before_nav, after_nav):
            print(f"  {line}")

    # 3. HTML 差分（両方に存在するページのみ）
    counter: collections.Counter[str] = collections.Counter()
    changed_pages: dict[str, int] = {}
    for page in sorted(before_pages & after_pages):
        diff = diff_lines(
            normalized_lines(os.path.join(args.before, page)),
            normalized_lines(os.path.join(args.after, page)),
        )
        if diff:
            changed_pages[page] = len(diff)
            counter.update(set(diff))
    common = len(before_pages & after_pages)
    print("\n## 3. HTML 差分（正規化後）")
    print(f"差分のあるページ: {len(changed_pages)} / {common}")
    if counter:
        print(f"差分行（出現ページ数の多い順、上位 {args.top} 件）:")
        for line, n in counter.most_common(args.top):
            print(f"  {n:>4}  {shorten(line)}")
        # 全ページ共通ではない差分行 = コンテンツ由来の可能性があるもの
        partial = [(line, n) for line, n in counter.items() if n < common]
        print(f"\n一部のページだけに出る差分行: {len(partial)} 種類（コンテンツ由来の可能性があるため要確認）")
        for line, n in sorted(partial, key=lambda x: -x[1])[: args.top]:
            print(f"  {n:>4}  {shorten(line)}")

    return 1 if has_problem else 0


if __name__ == "__main__":
    sys.exit(main())
