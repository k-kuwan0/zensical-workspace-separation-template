---
title: 執筆
---

# 執筆

## 新しいページを追加する

1. `docs/` 配下に Markdown ファイルを配置する（例: `docs/guides/new-page.md`）
2. `docs/sitemap.md` を編集し、対応する位置に `- [ラベル](guides/new-page.md)` を追加する
3. プレビューをリロードすると、サイドバーに反映される

`zensical serve` / `zensical build` を実行する際に、`docs/sitemap.md` から `zensical.toml` の `nav` が自動生成されるため、`nav` を手書きで更新する必要はありません。

## 下書き

書きかけのページは `docs/drafts/` に置きます。プレビューでは表示されますが、本番のサイトには出力されません。書き方と公開の手順は `docs/drafts/README.md` を見てください。

公開ページから下書きへのリンクは張らないでください。本番では下書きが存在しないため、リンク切れになります。

## front matter

各 Markdown ファイル冒頭に以下を書けます。

```yaml
---
title: 任意のページタイトル
---
```

`title` を指定するとサイドバーの表示名として使われます。指定がなければ `# 見出し` から自動抽出されます。

## Zensical の Markdown 拡張

Admonition・タブ・折りたたみなど、[Zensical 公式ドキュメント](https://zensical.org/docs/authoring/markdown/) の記法がそのまま利用できます。
