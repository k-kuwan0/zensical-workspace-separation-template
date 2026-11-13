---
title: 下書き
---

# 下書き

`docs/drafts/` に置いたページは**下書き**として扱われます。

- プレビュー（`zensical serve`）では、タイトルの上に「DRAFT」のバッジが付いて表示されます
- 本番のビルド（`zensical build`）では出力されません。サイト、検索、`sitemap.xml` のどこにも出ません
- サイドバーには表示されません。プレビューでは URL を直接開いて確認します（例: `docs/drafts/sample.md` → `http://localhost:8001/drafts/sample/`）

[サンプル](sample.md)も置いてあります。

## 下書きを書く

1. `docs/drafts/` に Markdown ファイルを作る（例: `docs/drafts/new-page.md`）
2. プレビューで `http://localhost:8001/drafts/new-page/` を開いて確認する

`docs/sitemap.md` にはまだ追加しません。

## 下書きを公開する

1. ファイルを公開したい場所に移す（例: `git mv docs/drafts/new-page.md docs/guides/new-page.md`）
2. `docs/sitemap.md` に `- [ラベル](guides/new-page.md)` を追加する

`docs/sitemap.md` に `drafts/` のページを追加すると、本番ではリンク切れになります（サイドバーに 404 になる項目が出ます）。先にファイルを移してください。

## 注意

- 下書きもリポジトリにはコミットされます。本番のサイトには出ませんが、リポジトリを読める人には見えます。リポジトリにも置けない内容は、ここに置かないでください
- 書きかけの状態で PR を出して、内容のレビューを受けられます
