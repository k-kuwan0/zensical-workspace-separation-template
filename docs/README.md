---
title: ホーム
---

# Zensical Workspace Separation Template

このサイトは、Zensical で静的サイトを構築する際の**執筆者領域と管理者領域の分離**を実演するサンプルです。

## このサイトについて

執筆者は `docs/` 配下の Markdown ファイルだけを編集し、
サイトのスタイル・スクリプト・テーマ設定などは `ssg/` 配下（管理者領域）に閉じ込められています。

Docker Compose のマウント設計で「執筆者から見える構成」と「管理者から見える構成」を分けているため、
執筆者は Markdown 執筆に集中でき、管理者は執筆者の作業を妨げずにサイト構築を進められます。

## 目次

- [はじめに](getting-started/README.md)
- [ガイド](guides/README.md)
- [サイトマップ](sitemap.md)
