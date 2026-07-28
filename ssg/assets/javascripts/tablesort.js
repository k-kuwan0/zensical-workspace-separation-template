// Zensical 公式ドキュメント（Data tables）で案内されている定型コード。
// 参考: https://zensical.org/docs/authoring/data-tables/
//
// article 直下の <table>（クラス無し）に対して Tablesort を適用する。
// tablesort ライブラリ本体は zensical.toml の extra_javascript で unpkg 経由で読み込む。
document$.subscribe(function() {
  var tables = document.querySelectorAll("article table:not([class])")
  tables.forEach(function(table) {
    new Tablesort(table)
  })
})
