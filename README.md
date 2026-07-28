# Zensical Workspace Separation Template

Zensical で静的サイトを構築する際に、**執筆者領域（コンテンツ）** と **管理者領域（サイト構築設定）** を Docker マウントで分離するためのテンプレート。

## ディレクトリの意味

| ディレクトリ | 責務 | 主な読者 |
|---|---|---|
| `docs/` | Markdown コンテンツ | 執筆者 |
| `ssg/` | Zensical 設定・テーマ・アセット・スクリプト | 管理者 |
| `dockerfiles/`, `docker-compose.yaml` | 開発コンテナ定義 | 管理者 |
| `.vscode/` | 執筆者向けの VSCode タスク | 執筆者 |

`ssg/assets/` 配下の CSS/JS は Docker Compose のオーバーレイマウントで `docs/stylesheets/`, `docs/javascripts/` としてコンテナ内から見える。執筆者は `docs/` 配下の Markdown だけを編集し、サイトのスタイルやスクリプトは管理者領域で完結する構成。

## 使い方

### 執筆者

VSCode でリポジトリを開き、`Cmd+Shift+P` → `Tasks: Run Task` から：

1. **コンテナビルド**（初回のみ）
2. **コンテナ起動**
3. **プレビュー起動** → ブラウザで `http://localhost:8001` を開く
4. `docs/` の Markdown を編集するとホットリロード

### 管理者（Dev Container 利用）

1. **コンテナ起動** タスクを実行
2. `Cmd+Shift+P` → `Dev Containers: Reopen in Container` で `ssg` サービスに接続
3. `/ssg` がワークスペースとして開かれる
4. 詳細は [ssg/README.md](ssg/README.md)

## 詳細

- 管理者領域のセットアップ・デバッグ手順: [ssg/README.md](ssg/README.md)
- Zensical 前提・ナビ運用ルール: [ssg/CLAUDE.md](ssg/CLAUDE.md)
- 設計判断・運用メモ: [ssg/notes/](ssg/notes/)
