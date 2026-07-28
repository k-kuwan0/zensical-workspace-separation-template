#!/usr/bin/env python3
"""docs/sitemap.md を source of truth として zensical.toml の nav を生成する。

背景・設計判断:

- サイドバー（左メニュー）は zensical.toml の `nav` が制御する。docs/sitemap.md は
  「人間が読む目次ページ」で Zensical は nav 生成に使わない。両者を手書きで二重管理
  するとズレが生じるため、本スクリプトが sitemap.md から nav を機械生成する。

抽出ルール（sitemap.md → nav）:
- H1  `# ...`            : ページタイトル。無視。
- H2+ `## ...` / `### …` : セクション。日本語名=見出しテキスト。見出しレベルでネスト。
- `- [ラベル](path)`     : ページ。直近セクション配下に出現順で追加。ラベルは捨てる
                           （ページ名は各 md の H1 / front matter title から Zensical が
                           自動取得するため、nav にラベルを持たせない）。
- 見出しより前のトップレベル箇条書き : ルート直下ページ（README/HISTORY/sitemap）。

書き換え範囲:
- zensical.toml の `# ### SITEMAP BEGIN ###` 〜 `# ### SITEMAP END ###` の間だけを
  生成した `nav = [...]` で置換する。他の設定行には一切触れない。

孤児検出:
- docs/ 配下の実 .md のうち sitemap.md に未掲載のものを警告する（ORPHAN_EXCLUDE を除く）。
  ビルドは止めない（警告のみ）。

使い方:
    python scripts/gen_nav.py --check   # 生成結果と現行 nav の差分を表示（書き換えない / CI 向け）
    python scripts/gen_nav.py --write   # zensical.toml を実際に書き換える
"""

from __future__ import annotations

import argparse
import os
import re
import sys

# --- パス（このスクリプトはリポジトリルート /ssg 直下の scripts/ にある想定）---
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(ROOT, "docs")
SITEMAP = os.path.join(DOCS_DIR, "sitemap.md")
TOML = os.path.join(ROOT, "zensical.toml")

BEGIN_MARKER = "# ### SITEMAP BEGIN ###"
END_MARKER = "# ### SITEMAP END ###"

# 孤児検出から除外するトップレベルディレクトリ（意図的に nav 外に置くもの）。
ORPHAN_EXCLUDE = {"drafts"}

# 孤児検出から除外する個別ファイル（docs/ からの相対パス）。
# 「実在するが意図的にサイドバー/目次から外しているページ」をここに登録する。
# ここに無い未掲載 md は警告される（取りこぼし検出）。
ORPHAN_EXCLUDE_FILES: set[str] = set()

INDENT = "  "

_heading_re = re.compile(r"^(#{1,6})\s+(.*)$")
_link_re = re.compile(r"^\s*-\s*\[([^\]]*)\]\(([^)]+)\)")


# ---------------------------------------------------------------------------
# sitemap.md のパース → nav ネスト構造
# ---------------------------------------------------------------------------
# nav の内部表現は zensical.toml と同じ:
#   ページ     = "path"（str）
#   セクション = {"日本語名": [子, ...]}
def parse_sitemap(path: str) -> tuple[list, list[str]]:
    """sitemap.md を読み、(nav構造, 掲載パス一覧) を返す。"""
    root: list = []
    # stack[i] = (見出しレベル, その階層の子リスト)。ルートは level=1 相当。
    stack: list[tuple[int, list]] = [(1, root)]
    listed: list[str] = []

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")

            m = _heading_re.match(line)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                if level == 1:
                    continue  # H1 はページタイトル。無視。
                # 同レベル以浅の見出しが来たらその分だけ畳む
                while len(stack) > 1 and stack[-1][0] >= level:
                    stack.pop()
                children: list = []
                stack[-1][1].append({title: children})
                stack.append((level, children))
                continue

            m = _link_re.match(line)
            if m:
                page = os.path.normpath(m.group(2).strip()).replace(os.sep, "/")
                stack[-1][1].append(page)
                listed.append(page)

    return root, listed


# ---------------------------------------------------------------------------
# nav ネスト構造 → TOML テキスト
# ---------------------------------------------------------------------------
def _toml_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def render_nav(nav: list) -> str:
    """nav 構造を zensical.toml の `nav = [...]` テキスト（末尾改行なし）に整形する。

    トップレベル要素（ルート直下）のセクションの前に空行を 1 つ入れる（可読性のため）。
    """
    lines: list[str] = ["nav = ["]

    def walk(items: list, depth: int) -> None:
        pad = INDENT * depth
        for it in items:
            if isinstance(it, str):
                lines.append(f'{pad}"{_toml_escape(it)}",')
            elif isinstance(it, dict):
                # トップレベル（depth==1）のセクションの前に空行を入れる
                if depth == 1:
                    lines.append("")
                for title, children in it.items():
                    lines.append(f'{pad}{{ "{_toml_escape(title)}" = [')
                    walk(children, depth + 1)
                    lines.append(f"{pad}] }},")

    walk(nav, 1)
    lines.append("]")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 孤児検出
# ---------------------------------------------------------------------------
def find_orphans(listed: list[str]) -> list[str]:
    """docs/ 配下の実 .md のうち sitemap.md 未掲載のものを返す。

    ORPHAN_EXCLUDE（トップレベルディレクトリ）と ORPHAN_EXCLUDE_FILES（個別ファイル）に
    該当するものは「意図的に nav 外」とみなし警告対象から除く。
    """
    listed_set = set(listed)
    orphans: list[str] = []
    for dirpath, dirnames, filenames in os.walk(DOCS_DIR):
        # 除外ディレクトリは降りない
        dirnames[:] = [d for d in dirnames if d not in ORPHAN_EXCLUDE]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), DOCS_DIR)
            rel = os.path.normpath(rel).replace(os.sep, "/")
            top = rel.split("/", 1)[0]
            if top in ORPHAN_EXCLUDE:
                continue
            if rel in ORPHAN_EXCLUDE_FILES:
                continue
            if rel not in listed_set:
                orphans.append(rel)
    return sorted(orphans)


# ---------------------------------------------------------------------------
# zensical.toml の SITEMAP マーカー間を置換
# ---------------------------------------------------------------------------
def splice_into_toml(toml_text: str, nav_block: str) -> str:
    lines = toml_text.split("\n")
    try:
        begin = next(i for i, l in enumerate(lines) if l.strip() == BEGIN_MARKER)
        end = next(i for i, l in enumerate(lines) if l.strip() == END_MARKER)
    except StopIteration:
        raise SystemExit(
            f"エラー: zensical.toml に {BEGIN_MARKER} / {END_MARKER} マーカーが見つかりません。"
        )
    if end <= begin:
        raise SystemExit(
            "エラー: SITEMAP マーカーの並び順が不正です（BEGIN が END より後）。"
        )

    # BEGIN 行の直後の「コメント行群」は保持し、実際の nav = [ ... ] のブロックだけを差し替える。
    try:
        nav_start = next(
            i for i in range(begin + 1, end) if lines[i].lstrip().startswith("nav = [")
        )
    except StopIteration:
        raise SystemExit("エラー: SITEMAP マーカー間に `nav = [` が見つかりません。")

    head = lines[:nav_start]  # BEGIN とその後のコメントまで
    tail = lines[end:]  # END マーカー以降
    new_lines = head + nav_block.split("\n") + tail
    return "\n".join(new_lines)


# ---------------------------------------------------------------------------
# 現行 nav の抽出（--check 用）
# ---------------------------------------------------------------------------
def current_nav_block(toml_text: str) -> str:
    lines = toml_text.split("\n")
    begin = next(i for i, l in enumerate(lines) if l.strip() == BEGIN_MARKER)
    end = next(i for i, l in enumerate(lines) if l.strip() == END_MARKER)
    nav_start = next(
        i for i in range(begin + 1, end) if lines[i].lstrip().startswith("nav = [")
    )
    return "\n".join(lines[nav_start:end]).rstrip("\n")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description="sitemap.md から zensical.toml の nav を生成"
    )
    g = ap.add_mutually_exclusive_group()
    g.add_argument(
        "--write", action="store_true", help="zensical.toml を実際に書き換える"
    )
    g.add_argument(
        "--check",
        action="store_true",
        help="生成結果と現行 nav の差分のみ表示（書き換えない・CI 向け）",
    )
    args = ap.parse_args()

    nav, listed = parse_sitemap(SITEMAP)
    nav_block = render_nav(nav)

    # 孤児警告（常に実施）
    orphans = find_orphans(listed)
    if orphans:
        print(
            "警告: docs/ に存在するが sitemap.md に未掲載のページがあります:",
            file=sys.stderr,
        )
        for o in orphans:
            print(f"  - {o}", file=sys.stderr)
        print(
            "  → サイドバーに出したい場合は docs/sitemap.md に追記してください"
            f"（除外: {', '.join(sorted(ORPHAN_EXCLUDE))}）。",
            file=sys.stderr,
        )

    with open(TOML, encoding="utf-8") as f:
        toml_text = f.read()

    if args.check:
        current = current_nav_block(toml_text)
        if current.strip() == nav_block.strip():
            print("nav は sitemap.md と一致しています（更新不要）。")
            return 1 if orphans else 0
        print("差分あり: zensical.toml の nav は sitemap.md と一致していません。")
        print("`python scripts/gen_nav.py --write` で更新できます。")
        import difflib

        diff = difflib.unified_diff(
            current.splitlines(),
            nav_block.splitlines(),
            fromfile="zensical.toml (現行 nav)",
            tofile="sitemap.md から生成",
            lineterm="",
        )
        print("\n".join(diff))
        return 1

    new_text = splice_into_toml(toml_text, nav_block)
    if args.write:
        if new_text != toml_text:
            with open(TOML, "w", encoding="utf-8") as f:
                f.write(new_text)
            print("zensical.toml の nav を sitemap.md から再生成しました。")
        else:
            print("nav に変更はありませんでした（既に最新）。")
        return 0

    # モード未指定: 生成結果を標準出力に出すだけ（安全側）
    print(nav_block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
