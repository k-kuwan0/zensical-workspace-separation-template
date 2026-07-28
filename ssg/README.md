# SSG (Zensical Workspace Separation Template)

Zensical プロジェクトとして構築される静的サイトの管理領域。

## 前提

- Docker Desktop / OrbStack など Docker Compose 対応環境
- VSCode + [Dev Containers 拡張機能](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

## セットアップ

### 1. コンテナイメージのビルド

初回のみ、リポジトリルートで実行する。

```bash
docker compose build ssg
```

### 2. コンテナの起動

```bash
docker compose up -d ssg
```

### 3. Dev Container で開く

1. VSCode でリポジトリを開く
2. `Cmd+Shift+P` → `Dev Containers: Reopen in Container`
3. `ssg` サービスに接続され、`/ssg` がワークスペースルートとして開かれる

初回接続時、`Zensical: serve` などを実行すると `uv run` が `.venv` を自動セットアップする（数十秒かかる）。

## プレビュー起動（Dev Container 内）

`.vscode/tasks.json` の `Zensical: serve` タスクを実行する。

1. `Cmd+Shift+P` → `Tasks: Run Task` → `Zensical: serve` を選択
   （または `Terminal` メニュー → `Run Task...`）
2. コンテナ内で `zensical serve`（デフォルト `localhost:8000`）が起動
3. VSCode が自動で `8000` をホストにフォワード
4. ブラウザで `http://localhost:8000` を開く
5. `docs/` の Markdown を編集するとホットリロード

## ビルド

`Zensical: build` タスクを実行する。生成物は `ssg/site/` に出力される。

## ナビゲーション（サイドバー）の管理

サイドバーの構成は **`docs/sitemap.md`（目次ページ）を正（source of truth）** として管理する。

- 執筆者は **`docs/sitemap.md` だけ**を編集すればよい（見出し＝セクション、箇条書きの順＝表示順）。
- `zensical serve` / `zensical build` を実行すると、コンテナ内の `zensical` ラッパー
  （`/usr/local/bin/zensical`）が **`docs/sitemap.md` から `zensical.toml` の `nav` を自動再生成**する。
  そのため **`zensical.toml` の `nav` は手で編集しない**（自動生成される派生物）。
- nav だけを手動で再生成したいときは `Zensical: nav を再生成` タスク、または
  `python3 scripts/gen_nav.py --write` を実行する。CI 等で差分検査だけしたい場合は `--check`。

## 関連ドキュメント

- [CLAUDE.md](CLAUDE.md) — Dev Container 前提とワークスペース構造の説明
- [notes/](notes/) — 設計判断・運用メモ
