# プロジェクトガイド

## ワークスペースの前提

あなたは Zensical ワークスペース分離テンプレートの Dev Container 内で作業している。

### ディレクトリ配置

| コンテナ内パス | 役割 | ホスト側の対応 |
|---|---|---|
| `/ssg` | ワークスペースルート。Zensical 設定・テーマ・アセット・管理者向けドキュメントを集約 | `zensical-test/ssg/` |
| `/ssg/zensical.toml` | サイトのメイン設定 | `zensical-test/ssg/zensical.toml` |
| `/ssg/overrides/` | Zensical テンプレートオーバーライド | `zensical-test/ssg/overrides/` |
| `/ssg/docs/` | 執筆コンテンツ（Markdown と画像） | `zensical-test/docs/`（bind mount） |
| `/ssg/docs/stylesheets/` | サイトの CSS。実体は `assets` 側 | `zensical-test/ssg/assets/stylesheets/`（オーバーレイマウント） |
| `/ssg/docs/javascripts/` | サイトの JS。実体は `assets` 側 | `zensical-test/ssg/assets/javascripts/`（オーバーレイマウント） |
| `/ssg/notes/` | 管理者向けドキュメント | `zensical-test/ssg/notes/` |
| `/ssg/.venv/` | uv が管理する Python 仮想環境（名前付きボリューム） | ホストには露出しない |
| `/ssg/site/` | Zensical ビルド成果物 | `zensical-test/ssg/site/`（bind mount） |

### 触ってよい / 触ってはいけない領域

- **触ってよい**: `/ssg/` 配下の Zensical 設定、`overrides/`、`assets/`（`/ssg/docs/stylesheets/` `/ssg/docs/javascripts/` として見える）、`notes/`。
- **原則触らない**: `/ssg/docs/` 配下の Markdown コンテンツは執筆者の領域。内容編集は依頼されたときのみ。
  - front matter の追加やテンプレート由来の修正（コンテンツの意味を変えない範囲）は許可される。
- **アセット（CSS/JS）は `docs/stylesheets/`, `docs/javascripts/` に見えるがオーバーレイマウントであり、実体はホスト側 `ssg/assets/`**。編集内容はホスト側にも反映される。

### 参照すべきドキュメント

- [README.md](README.md) — セットアップ手順・プレビュー起動
- [notes/](notes/) — 設計判断・運用メモ
- [notes/zensical-upgrade.md](notes/zensical-upgrade.md) — Zensical のアップグレード記録（手順はリポジトリ直下の `.claude/skills/zensical-upgrade/`）

## ナビゲーション（サイドバー / nav）の管理方針

サイドバーは `zensical.toml` の `nav` が制御するが、**`nav` は `docs/sitemap.md` から自動生成する派生物**であり、直接編集しない。

- **source of truth は `docs/sitemap.md`**（人間が読む目次ページ）。
  見出し（`##` / `###`）＝セクション、箇条書き（`- [ラベル](path)`）の順＝表示順。
- `zensical serve` / `zensical build` 実行時に、コンテナ内の `zensical` ラッパー
  （`/usr/local/bin/zensical`、Dockerfile で配置）が `scripts/gen_nav.py --write` を呼び、
  `docs/sitemap.md` から `zensical.toml` の `# ### SITEMAP BEGIN/END ###` マーカー間の
  `nav = [...]` を再生成する。
- **`zensical.toml` の `nav` を手書きしない。** 変更したいときは `docs/sitemap.md` を編集する。
- ページの表示名（ラベル）は各 Markdown の H1 / front matter `title:` から Zensical が
  自動取得する。`nav` はパスだけを持ち、ラベルは持たない（`sitemap.md` のラベルは目次表示用）。

### 実装ファイル

| ファイル | 役割 |
|---|---|
| `docs/sitemap.md` | nav の source of truth（＋公開される目次ページ） |
| `scripts/gen_nav.py` | sitemap.md → nav 生成本体（Python・標準ライブラリのみ）。`--write` / `--check` |
| `scripts/zensical` | `zensical` の sh ラッパー。serve/build 前に nav 生成を挟む。Dockerfile で `/usr/local/bin/zensical` に配置 |

- `docs/` に存在するが `sitemap.md` に未掲載の Markdown は、`gen_nav.py` が**警告**する
  （サイドバー未掲載の取りこぼし検出）。意図的に nav 外に置くものは `gen_nav.py` の
  `ORPHAN_EXCLUDE`（ディレクトリ単位・現状 `drafts`）または `ORPHAN_EXCLUDE_FILES`
  （ファイル単位）に追加する。

## Zensical 固有の注意点

- テーマは Zensical（MkDocs Material 由来）。テンプレートエンジンは **Jinja2**。
- テンプレートの上書きは [overrides/](overrides/) 配下。
- 検索プラグインのキーは Zensical では `search`（Material 時代の `material/search` ではない）。
  overrides で検索バーを制御する場合は条件式に注意する。
- **Zensical の "modern" テーマは従来の MkDocs Material と CSS 変数の使われ方が異なる**。
  色が効かないときは、配信中の `assets/stylesheets/modern/main.*.min.css` で実際の適用先変数を確認する。
- Zensical 0.0.46 では `docs_dir` に `..` を含むパスや絶対パスの指定ができない
  （[Issue #68](https://github.com/zensical/zensical/issues/68)）。
  現状は Docker Compose のマウント設計で回避している。
