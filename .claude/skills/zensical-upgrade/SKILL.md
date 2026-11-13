---
name: zensical-upgrade
description: ssg/ の Zensical をバージョンアップする。リリースノートから破壊的変更・影響しうる変更・使えそうな新機能を洗い出し、Issue 作成、ブランチ作成、uv での更新、新旧ビルド出力の比較（ssg/scripts/compare_build.py）、ヘッドレス Chrome での見た目と日本語検索の比較（ssg/scripts/browser_check.mjs）、PR 本文の作成までを行う。「Zensical をアップグレード」「Zensical を上げたい」「zensical のバージョンアップ」で起動。
argument-hint: "[目標バージョン（省略時は最新リリース）]"
---

# Zensical アップグレード

`ssg/` の Zensical を目標バージョンに上げ、サイトへの影響が無いことを確認して PR にする。
引数で目標バージョン（例: `0.1.3`）を受け取る。省略時は最新リリースを目標にする。

## 前提

- **ホスト側のリポジトリルートから実行する。** コンテナには `.git` と `gh` が無いため、git / gh はホスト、
  uv / zensical はコンテナ（`docker compose exec -T ssg sh -c 'cd /ssg && ...'`）で実行する。
- Zensical のリリース情報は `gh ... -R zensical/zensical` で取得する。
- 記録は `ssg/notes/zensical-upgrade.md`、Issue テンプレートは `.github/ISSUE_TEMPLATE/Zensical_Upgrade.md`。
- 見た目の確認対象（ページ・検索語・自前 JS）は `ssg/scripts/browser_check.config.json` で管理する。

## 注意（ハマりやすい点）

- **`ssg/pyproject.toml` / `uv.lock` / `zensical.toml` / `CLAUDE.md` は単一ファイルの bind mount。**
  ホスト側でファイルを作り直す編集（macOS の `sed -i`、置き換え保存するエディタ等）をすると、コンテナから
  古いファイルが見え続ける。依存の更新はコンテナ内の `uv add` で行う（その場で書き換えるのでマウントは外れない）。
  ホスト側でこれらを編集した後は `docker compose restart ssg` してからビルドする。
  git の操作（コミット、rebase、ブランチ切り替え）でも同じことが起きるので、git 操作の後のビルド前にも再起動する。
- コンテナ内でも GNU `sed -i` はファイルを置き換えようとして `Device or resource busy` で失敗する。
- コンテナには `pkill` / `ps` が無い。バックグラウンドの `zensical serve` を止めるには `docker compose restart ssg`。
- `browser_check.mjs` はホストの Chrome と Node（22 以降）を使う。外部パッケージは不要（Node 標準の fetch / WebSocket のみ）。
  Chrome の場所が既定（macOS）と違う場合は `CHROME` 環境変数で指定する。
- `zensical serve` を止めると（コンテナ再起動を含む）`site/` が空になる。ベースラインはコンテナの `/tmp/site-before` に
  コピーしてから比較する。`/tmp` はコンテナの再起動では残るが、再作成（`docker compose up` での Recreate）では消える。
- `zensical` コマンドはラッパー（`ssg/scripts/zensical`）で、serve / build の前に nav を再生成する。
  nav の再生成で `zensical.toml` が変わった場合は、アップグレードとは別の差分なので切り分ける。
- ポート 8001 を別のプロジェクトが使っている場合は、`docker compose run -d -p <空きポート>:8001 ssg ...` で
  プレビューを起動し、`browser_check.mjs` にそのポートを渡す。

## 手順

### Step 1: バージョンを特定する

```bash
grep -A1 '^name = "zensical"' ssg/uv.lock          # 現在のバージョン
gh release list -R zensical/zensical -L 30          # 目標バージョンと対象リリース数
```

### Step 2: リリースノートを読み、影響を洗い出す

対象範囲（現在より新しく、目標以下）の全リリースを読む。省略せず全件読むこと。

```bash
gh api repos/zensical/zensical/releases --paginate \
  -q '.[] | "=== \(.tag_name) (\(.published_at))\n\(.body)\n"' > <scratchpad>/zensical-releases.txt
```

次の観点で影響を判断する。判断のため `ssg/zensical.toml`、`ssg/Dockerfile`、`ssg/overrides/`、`ssg/assets/` を実際に読む。

| 観点 | 気にする理由 |
|---|---|
| `Breaking changes` の見出し | 明示的な非互換 |
| Python の対応バージョン、配布 wheel の種類 | Dockerfile のベースイメージ（Debian / glibc）で動くか |
| `ui` の更新 | `overrides/` で partial を丸ごと置き換えている場合、上流テンプレートの構造変更に追従できない |
| テーマの JS API（`document$` 等） | `assets/javascripts/` の自前 JS が依存している場合、初期化されなくなる |
| ナビゲーション・タイトル解決 | nav をパスだけで書き、表示名を H1 / front matter `title:` から取っている場合に表示名が変わりうる |
| 設定の検証（validation） | `zensical.toml` が新しい検証に通るか |
| Markdown 拡張（SuperFences / tabbed / Mermaid 等） | 本文の描画が変わりうる |
| plugins 関連 | `zensical.toml` で設定している plugin に変更が無いか |

`ssg/notes/` に「Zensical の制約」「回避策」として書いたものがあれば、解消されていないかも確認する。
GitHub Issue が close されていても、コメントで「バックログ入り」とされているだけのことがあるので、本文とコメントまで読む。

**追加された機能も拾う。** 各リリースの `Features` を一覧にし、このサイトで使えそうなものを選ぶ。
選ぶ基準は「運用上の課題（`ssg/notes/` の課題、下書きの扱い、検索品質など）を解決するか」「MkDocs 時代に
使っていた機能の代わりになるか」。導入するかどうかは方針判断なので、このスキルの中では導入しない
（PR の「取り入れられるアップデート」に挙げ、レビューのときに次の動きとしてあわせて見てもらう）。

**ここでユーザーに報告する**: 明示的な破壊的変更とこのサイトへの影響、影響しうる動作変更、解消された制約、
使えそうな新機能（「〜が追加されました。〜に使えますが、導入しますか？」の形で）。
進めてよいか確認してから Step 3 へ。

### Step 3: Issue を作る

Issue には「なぜやるか・何をやるか」（バージョン、背景、リリースノートの確認結果）だけを書く。
作業内容・確認結果・既知の差分は PR に書くので、Issue には入れない。

`.github/ISSUE_TEMPLATE/Zensical_Upgrade.md` の構成で本文を作る。**作成前に本文をユーザーに見せて確認を取る**
（ユーザーが自分で作成する場合は、タイトルと本文をコピペできる形で渡す）。

```bash
gh issue create --title "Zensical を A.B.C から X.Y.Z にアップグレードする" --body-file <scratchpad>/issue.md
```

### Step 4: ブランチを作り、ベースラインを取る

```bash
# ホスト（既定ブランチから切る）
git switch main && git pull
git switch -c feature/zensical-X.Y.Z

# コンテナ（止まっていれば docker compose up -d ssg）。ホスト側の git 操作でマウントが外れていることがあるので再起動しておく
docker compose restart ssg
docker compose exec -T ssg sh -c 'cd /ssg && zensical build && rm -rf /tmp/site-before && cp -r site /tmp/site-before'

# 見た目と検索のベースライン（ホスト。ブラウザはホストの Chrome を使う）
docker compose exec -d ssg sh -c 'cd /ssg && zensical serve -a 0.0.0.0:8001 > /tmp/serve.log 2>&1'
node ssg/scripts/browser_check.mjs http://localhost:8001 <scratchpad>/check-before
```

ベースラインのビルドで警告が出ている場合は、内容を控えておく（アップグレード後に増えていないかを見るため）。

**ベースラインは必ずアップグレード前に取る。** 後から旧バージョンを入れ直そうとしても、Python 3.15 向けの wheel が無い
依存（0.0.46 の `pyyaml` 等）のビルドに失敗することがある。どうしても必要な場合は、uv で Python 3.13 の別環境を作って入れる
（`uv venv --python 3.13 /tmp/old && VIRTUAL_ENV=/tmp/old uv pip install zensical==A.B.C`）。

### Step 5: バージョンを上げてビルド・比較する

```bash
docker compose exec -T ssg sh -c 'cd /ssg && uv add --dev "zensical>=X.Y.Z" && uv run zensical --version'
docker compose exec -T ssg sh -c 'cd /ssg && zensical build && python3 scripts/compare_build.py /tmp/site-before site'
```

`git diff --stat` で `ssg/pyproject.toml` と `ssg/uv.lock` がホスト側にも反映されたことを確認する。

`compare_build.py` の出力の読み方:

1. **ファイル一覧**: ページ数が一致すること。テーマアセットはハッシュを除いて比較する。
2. **サイドバーの表示名**: 「差分なし」であること。差分があればタイトル解決の変更を疑う。
3. **HTML 差分**: 全ページ共通の差分行はテーマ（UI）由来。「一部のページだけに出る差分行」に本文の要素
   （見出し、表、コードブロック等）が含まれていないかを重点的に見る。
   新しい UI 文言が日本語に翻訳されているか（`__config` の `translations`）もここで分かる。

ページ増減またはサイドバー差分があると終了コード 1 になる。原因を調べてユーザーに報告する。

### Step 6: 見た目と日本語検索を確認する

HTML の比較では、テーマ CSS と自前の CSS（`ssg/assets/stylesheets/`）の組み合わせによる崩れは分からない。
**確認できるものは自分で確認する。** プレビューを起動し直し、ベースラインと同じスクリプトで記録する。

```bash
docker compose restart ssg   # 旧バージョンの serve を止める
docker compose exec -d ssg sh -c 'cd /ssg && zensical serve -a 0.0.0.0:8001 > /tmp/serve.log 2>&1'
node ssg/scripts/browser_check.mjs http://localhost:8001 <scratchpad>/check-after
```

- `page-*-{light,dark}.png` を Read で新旧並べて見比べる（ヘッダー、サイドバー、コードブロック、テーブル）。
- `result.json` の検索ヒット件数を新旧で比べ、件数が大きく変わった語は `search-*.png` で上位の結果が妥当かを見る。
  英語のまま表示される文言は、ベースラインでも同じか（今回のアップグレードで生じたものか）を区別する。
- 自前 JS のテーブルソート（`tablesort.js`）が、直接開いた場合とサイドバーから遷移した場合の両方で「ソート OK」であること。
  テーマの `document$` に依存して初期化するため、UI の更新で壊れうる。NG なら `document$` の扱いがリリースノートで
  変わっていないかを調べる。

**確認する範囲は「このサイトで手を入れている部分」（`overrides/` / `assets/`）に絞る。** コピーボタン、サイドバーの開閉、
テーマ切り替え、スマートフォン幅のドロワーなど Zensical 本体の機能は、手を入れていない限りアップグレードのたびに確認しない
（上流でテストされている）。カスタマイズが増えたら、その部分を確認できるよう `browser_check.config.json`
（必要なら `browser_check.mjs`）に追加する。

どうしても自動で確認できないものがあれば、作成者（ユーザー）に「どのページで・何をして・どうなれば OK か」を伝えて
PR を出す前に確認してもらい、結果を確認結果に入れる。レビュアーに確認を委ねる形で PR に残さない。

### Step 7: 記録を更新し、PR を作る

- `ssg/notes/zensical-upgrade.md` のアップグレード記録に 1 行追記する（Issue 番号を含める）。
- Step 2 で解消が分かった制約があれば、`ssg/notes/` の該当メモを更新する。
- コミットと PR は、ユーザーの確認を取ってから。PR は既定ブランチ（`main`）向け。

PR 本文は次の構成で書く。確認結果には、確認したことを結果（件数など）つきで書く。確認していないことにチェックを付けない。
「取り入れられるアップデート」には Step 2 で拾った新機能を挙げる。この PR で対応する課題ではなく、レビューのときに
次の動きをあわせて相談するための材料という位置付け。各項目は「何が追加されたか」「このサイトで何に使えるか」を書く。
バグや未翻訳など、使える機能ではないものは「既知の差分・注意点」に書く。

```markdown
## やったこと
- `ssg/pyproject.toml` / `ssg/uv.lock`: zensical を X.Y.Z に更新
- （ほかの変更）

## 確認結果
- [x] `zensical build` が警告・エラーなしで成功する
- [x] `compare_build.py`: ページ数が変わらない（N）
- [x] `compare_build.py`: サイドバーの表示名に差分がない（N 項目）
- [x] `compare_build.py`: 本文由来の HTML 差分がない（テーマ由来の差分のみ）
- [x] テンプレートのオーバーライド（`overrides/`）が反映されている
- [x] `browser_check.mjs`: 主要ページ（N ページ × ライト / ダーク）のスクリーンショットに崩れがない（差分: …）
- [x] `browser_check.mjs`: 日本語検索（「…」N → N 件 など）
- [x] `browser_check.mjs`: 自前 JS のテーブルソートが動く（直接開いた場合 / サイドバーから遷移した場合）

## 既知の差分・注意点
- （テーマ由来の差分、未翻訳の文言、出力されなくなったファイルなど）

## 取り入れられるアップデート
今回のアップグレードで使えるようになった機能です。この PR では導入していません。次の動きとして、レビューのときにあわせて見てください。

- **（機能名）**（X.Y.Z）: （何ができるか）。このサイトでは（何に使えるか）。

## 関連リンク
- close #（Issue 番号）
```
