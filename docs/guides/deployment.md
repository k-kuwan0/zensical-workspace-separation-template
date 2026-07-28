---
title: デプロイ
---

# デプロイ

本テンプレートには特定のデプロイ先設定は含まれていません。

## ビルド

```bash
docker compose run --rm ssg zensical build
```

これにより `ssg/site/` に静的サイトが生成されます。ホスト側の `ssg/site/` にそのまま展開されるので、任意のホスティング先（S3・GitHub Pages・Cloudflare Pages 等）へアップロードしてください。

## CI/CD

GitHub Actions などから自動デプロイする場合は、上記の `docker compose run` を CI 上で実行し、`ssg/site/` の中身をデプロイ先へ同期する構成が典型的です。
