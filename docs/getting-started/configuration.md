---
title: 設定
---

# 設定

サイト固有の設定は `ssg/zensical.toml` に集約されます。
執筆者はこのファイルを直接編集する必要はありません。管理者が変更を担当します。

## 主な設定項目

| 項目 | 説明 |
|---|---|
| `site_name` | サイト名（ヘッダー・タイトル表示） |
| `site_description` | HTML meta description |
| `site_url` | 本番の公開 URL |
| `nav` | サイドバー構造（`docs/sitemap.md` から自動生成される） |
| `extra_css` / `extra_javascript` | 追加アセットの読み込み定義 |

詳細は Zensical 公式ドキュメント（<https://zensical.org/docs/setup/basics/>）を参照してください。
