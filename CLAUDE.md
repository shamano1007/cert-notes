# 学習ノート（Google Cloud Generative AI Leader）

## 構成

| パス | 役割 |
|---|---|
| `AIリーダー.md` | **原本**。用語集の内容はここだけを編集する |
| `html/build.py` | `AIリーダー.md` → `html/AIリーダー.html` の変換スクリプト |
| `html/AIリーダー.html` | **自動生成物**。直接編集しない（次回ビルドで消える） |
| `bk/` | 手動バックアップ |

## 更新フロー

1. `AIリーダー.md` を編集する
2. `cd html && python3 build.py` で HTML を再生成する
3. 用語数・章数が Markdown と一致するか確認する

`build.py` は引数なしで `../AIリーダー.md` を読み、`html/AIリーダー.html` を上書きする。

## AIリーダー.md の書式ルール

`build.py` は汎用の Markdown パーサではなく、この文書の構造に合わせた簡易変換器。
以下の書式から外れると正しく変換されない。

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

**表（`|` 記法）とコードブロックは未対応。** 必要になったら `build.py` の `render_blocks()` を拡張すること。

## 生成される HTML の仕様

単一ファイル完結（外部 CDN 参照なし）。オフラインでも動く。

- インクリメンタル検索（本文込み、ヒット件数表示）
- PC（900px以上）: ヘッダー固定 + 左メニューと右本文が**独立スクロール**
- スマホ: ページ全体スクロール（アドレスバー収納・プルリフレッシュを阻害しないため、あえて内部スクロールにしていない）
- ダークモード（OS設定追従 + 手動切替を localStorage 保存）

### 触ってはいけない仕様

- **左メニューの自動スクロールは入れない。** 過去に `scrollIntoView` で現在位置を追従させたところ、目次タップ時のスムーススクロール中に通過した用語ごとに発火し、メニューが往復して使いづらくなった。現在位置のハイライトのみ行う。
- スマホ側を内部スクロールコンテナにしない（上記の理由）。

## 表示確認の方法

macOS の Chrome はウィンドウ幅を 500px 未満にできないため、`--window-size=390,844` を指定しても
実際には 500px で描画され、スクリーンショットだけが 390px に切り取られる（崩れて見えるが誤検知）。
**スマホ幅の確認は iframe に埋めて行う。**

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# PC
"$CHROME" --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1440,900 --force-device-scale-factor=1 \
  --screenshot=pc.png "file:///Users/hamano.shun/work/学習/html/AIリーダー.html"

# スマホ（375px を iframe で再現）
cat > frame.html <<'EOF'
<!doctype html><meta charset="utf-8">
<style>body{margin:0;background:#555;padding:10px}iframe{border:0}</style>
<iframe src="file:///Users/hamano.shun/work/%E5%AD%A6%E7%BF%92/html/AIリーダー.html" width="375" height="860"></iframe>
EOF
"$CHROME" --headless=new --disable-gpu --hide-scrollbars \
  --window-size=420,880 --force-device-scale-factor=1 --allow-file-access-from-files \
  --screenshot=sp.png "file://$PWD/frame.html"
```

## 内容面の注意

- 2026年4月の Cloud Next '26 で **Vertex AI → Gemini Enterprise Agent Platform（略称 Agent Platform）** に改名された。
  本文は新名称で書いているが、**受験する試験ガイドの版が旧名称のままの可能性がある**ため旧名称も併記している。
- `A2A` と `MCP` は公式試験ガイドへの記載を確認できていない。参考情報として収録している。
