# 学習ノート（資格試験の用語集）

Markdown で原本を書き、`build.py` で静的 HTML を生成して GitHub Pages で公開するリポジトリ。
教材は今後増える前提の構成にしてある。

## 構成

| パス | 役割 |
|---|---|
| `doc/*.md` | **原本**。内容の編集はここだけ |
| `build.py` | `doc/*.md` → `docs/*.html` の変換スクリプト |
| `docs/` | **自動生成物**。GitHub Pages の公開ディレクトリ。直接編集しない（次回ビルドで消える） |
| `docs/index.html` | 教材一覧（Pages のトップ） |
| `memo.md` | 下書き置き場。**git 管理外** |
| `README.md` | GitHub トップに表示される説明 |
| `bk/` | 手動バックアップ。git 管理外 |

⚠️ **`doc/`（原本）と `docs/`（公開物）は1文字違い。** 編集対象は必ず `doc/`。

## 現在の教材

- `doc/genai-leader.md` — Google Cloud Generative AI Leader 用語集

## 更新フロー

1. `doc/<教材>.md` を編集する
2. `python3 build.py` で HTML を再生成する（プロジェクト直下で実行）
3. 用語数・章数が Markdown と一致するか確認する

```bash
python3 build.py                      # doc/ 配下すべて
python3 build.py doc/genai-leader.md  # 1つだけ（一覧も再生成される）
```

### 検算

```bash
grep -c '^## ' doc/genai-leader.md          # 用語数（+1 が手書き目次ぶん）
grep -c '^# 第' doc/genai-leader.md          # 章数
grep -c 'class="term"' docs/genai-leader.html
grep -c 'class="chapter"' docs/genai-leader.html
```

あわせて未変換の記法が残っていないか確認する（生成物に `**` や `<p>- ` が出ていないこと）。

## memo.md からの取り込み

`memo.md` は下書き置き場。「メモを反映して」と言われたらこのファイルを読む。

- **`target:` 行が反映先の md を指す。** 教材が増えたらここが書き換わるので、決め打ちせず毎回読むこと。
- **`{ }` で囲まれた部分は指示。** 用語の下書きではなく作業依頼として扱う（例：`{Transformer の説明追加}`）。
  指示への対応結果は、ターミナル出力にも要点をまとめて報告する。
- メモの見出しは `# 用語名`。**取り込み時に `##` へ降格**し、内容にふさわしい章へ配置する。
- 取り込んだ項目は `memo.md` から削除する（`target:` 行と使い方の説明は残す）。

### 取り込み時に必ずやること

- **既存項目との重複を確認する。** 同名・類似の用語があれば新規追加せず既存へ統合し、別表記は見出しに併記して検索でヒットするようにする。
- **書式ルールに合わせて変換する**（下記）。メモは `#` 見出しや番号リストで書かれていることが多い。
- 冒頭に `**用語＝定義**` の1行サマリを付けて既存項目と体裁を揃える。
- 関連する既存用語への相互参照（`※`）を足す。
- 目次（`## 目次` セクション）にも追加した用語を反映する。

## Markdown の書式ルール

`build.py` は汎用の Markdown パーサではなく、この文書構造に合わせた簡易変換器。
以下から外れると正しく変換されない。

- `# <タイトル>` — 冒頭の1つだけ。ページタイトルになる
- `## 目次` — セクションごと**破棄**される（目次は HTML 側で自動生成するため）
- `# 第N章 …` — 章。ナビゲーションの見出しになる
- `## <用語名>` — 用語。1枚のカードとして描画され、検索対象になる
- `### <小見出し>` — 用語内の小見出し（「具体例」「〜との違い」など）
- `---` — 無視される
- `**太字**` — 対応。**それ以外のインライン記法（リンク・コード・打ち消し）は非対応**で、そのまま文字として出る
- `- ` 始まりの行 — 箇条書き。導入文の直後に空行なしで続けてよい
- 箇条書きの継続行 — 半角スペース4つでインデントすると直前の項目にぶら下がる
- `※` で始まる行 — グレーの注記ボックスになる
- `⚠️` で始まる行 — オレンジの警告ボックスになる

**未対応：表（`|` 記法）、コードブロック、`####` 以下の見出し、番号リスト（`1. `）、ネストした箇条書き。**
必要になったら `build.py` の `render_blocks()` を拡張すること。

### 過去にやったミス

- 太字を語中で閉じた（`仕組**みです` → `仕組み**です`）
- 見出しに非 ASCII のハイフン（U+2011）が混入し、検索でヒットしなくなった
- 日本語のつもりで韓国語の文字を打ち込んだ（`리スク`、`포ートフォリオ`）

ビルド後に次を確認すると検出できる。

```bash
python3 - <<'PY'
import re
m = open('doc/genai-leader.md', encoding='utf-8').read()
print('非ASCIIハイフン:', '‑' in m)
print('非日本語CJK:', re.findall(r'[가-힣]', m) or 'なし')
print('ネストリスト:', '      - ' in m, '/ 表:', '\n|' in m)
PY
```

## 生成される HTML の仕様

単一ファイル完結（外部 CDN 参照なし）。オフラインでも動く。

- インクリメンタル検索（本文込み、ヒット件数表示）
- PC（900px以上）: ヘッダー固定 + 左メニューと右本文が**独立スクロール**
- スマホ: ページ全体スクロール（アドレスバー収納・プルリフレッシュを阻害しないため、あえて内部スクロールにしていない）
- ダークモード（OS設定追従 + 手動切替を localStorage 保存）
- 教材ページのヘッダーに一覧（`./`）へ戻るリンクがある

### 触ってはいけない仕様

- **左メニューの自動スクロールは入れない。** 過去に `scrollIntoView` で現在位置を追従させたところ、目次タップ時のスムーススクロール中に通過した用語ごとに発火し、メニューが往復して使いづらくなった。現在位置のハイライトのみ行う。
- スマホ側を内部スクロールコンテナにしない（上記の理由）。
- **外部リソースを参照しない。** CDN の CSS / JS / フォント / 画像を足さない。オフライン閲覧と表示速度のため。

## 公開（GitHub Pages）

public リポジトリ + Pages で外部公開する想定。Settings → Pages で
Source `Deploy from a branch` / Branch `main` / フォルダ `/docs`。

Jekyll のビルドは通るが、生成 HTML は YAML フロントマターを持たないため
**静的ファイルとして素通しされる**（Liquid の `{{ }}` は解釈されない）。
そのため `.nojekyll` は置いていない。`docs/` に `_` 始まりのファイルを出力する
ようになった場合のみ、`.nojekyll` の追加を検討する。

公開を前提にしているため、以下に注意する。

- **`docs/` に個人情報や社内情報を出さない。** `memo.md` を git 管理外にしているのはこのため。
- ファイル名は**英数字とハイフン**にする。日本語ファイル名は URL がパーセントエンコードされて扱いにくい。
- 一覧ページの URL は `<Pages のルート>/`、教材は `<ルート>/<ファイル名>.html`。
- Free プランでは **private リポジトリから Pages を公開できない**（Pro 以上が必要）。public 前提で運用する。

## 表示確認の方法

macOS の Chrome はウィンドウ幅を 500px 未満にできないため、`--window-size=390,844` を指定しても
実際には 500px で描画され、スクリーンショットだけが 390px に切り取られる（崩れて見えるが誤検知）。
**スマホ幅の確認は iframe に埋めて行う。**

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
D=/Users/hamano.shun/work/学習/docs

# PC
"$CHROME" --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1440,900 --force-device-scale-factor=1 \
  --screenshot=pc.png "file://$D/genai-leader.html"

# スマホ（375px を iframe で再現）
cat > frame.html <<EOF
<!doctype html><meta charset="utf-8">
<style>body{margin:0;background:#555;padding:10px}iframe{border:0}</style>
<iframe src="file://$D/genai-leader.html" width="375" height="880"></iframe>
EOF
"$CHROME" --headless=new --disable-gpu --hide-scrollbars \
  --window-size=420,900 --force-device-scale-factor=1 --allow-file-access-from-files \
  --screenshot=sp.png "file://$PWD/frame.html"
```

## 内容面の注意（genai-leader）

- 2026年4月の Cloud Next '26 で **Vertex AI → Gemini Enterprise Agent Platform（略称 Agent Platform）** に改名された。
  本文は新名称で書いているが、**受験する試験ガイドの版が旧名称のままの可能性がある**ため旧名称も併記している。
- 公式の学習ガイド（`generative_ai_leader_study_guide_ja.pdf`）は画像ベースの PDF で、
  WebFetch ではテキストが取れない。**Read ツールに `pages` を指定して読む**と中身が取れる。
- `A2A` と `MCP` は公式試験ガイドへの記載を確認できていない。参考情報として収録している。
