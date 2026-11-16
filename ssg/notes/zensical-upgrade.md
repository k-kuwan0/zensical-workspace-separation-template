# Zensical アップグレード記録

Zensical のバージョンアップの記録を管理者向けに残す。

- 手順: Claude Code のスキル `zensical-upgrade`（`.claude/skills/zensical-upgrade/SKILL.md`）。手作業で行う場合も同じ手順に従う。
- Issue テンプレート: 「Zensical Upgrade」（`.github/ISSUE_TEMPLATE/Zensical_Upgrade.md`）
- ビルド出力の比較: `ssg/scripts/compare_build.py`
- 見た目・日本語検索・自前 JS の確認: `ssg/scripts/browser_check.mjs`（確認対象は `browser_check.config.json`）
- 新旧スクリーンショットの比較画像: `ssg/scripts/compare_shots.mjs`
- 確認結果の根拠: 各 PR に残す（ビルドログ・`compare_build.py` の出力・`result.json` は PR 本文、スクリーンショットは PR のコメント）。元データはローカルの `ssg/.upgrade-evidence/<バージョン>/`（git 管理外）
- リリースノート: https://github.com/zensical/zensical/releases

---

| 日付 | バージョン | Issue / PR | 要点 |
|---|---|---|---|
| 2026-11-10 | 0.0.46 → 0.1.0 | #1 | 破壊的変更の影響なし。日本語（CJK）検索の分かち書きで検索ヒットが改善。新しい UI 文言 `clipboard.error` が未翻訳 |
