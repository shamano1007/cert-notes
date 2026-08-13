# 学習ノート

資格試験の勉強用にまとめた用語集です。Markdown で原本を書き、静的サイトとして公開しています。

**公開サイト**: <https://shamano1007.github.io/cert-notes/>

## 収録教材

| 教材 | 原本 | 公開ページ |
|---|---|---|
| Google Cloud Generative AI Leader 用語集 | [`doc/genai-leader.md`](doc/genai-leader.md) | [genai-leader.html](https://shamano1007.github.io/cert-notes/genai-leader.html) |

## ディレクトリ構成

```
.
├── doc/           # 原本の Markdown（ここを編集する）
│   └── genai-leader.md
├── docs/          # 生成物。GitHub Pages の公開ディレクトリ（直接編集しない）
│   ├── index.html         教材一覧
│   └── genai-leader.html
├── build.py       # doc/*.md → docs/*.html の変換スクリプト
├── memo.md        # 下書き置き場（git 管理外）
├── README.md
└── CLAUDE.md      # Claude Code 向けの運用手順
```

> `doc/`（原本）と `docs/`（公開物）は1文字違いです。**編集するのは `doc/`**、`docs/` はビルドで上書きされます。

## ビルド

```bash
python3 build.py                    # doc/ 配下すべて
python3 build.py doc/genai-leader.md  # 1つだけ（一覧も再生成される）
```

外部ライブラリは不要です（Python 3.9 以上の標準ライブラリのみ）。

## 教材を追加する

1. `doc/` に新しい `.md` を置く（ファイル名は英数字とハイフン。これが URL になります）
2. `python3 build.py` を実行する

`doc/*.md` を自動で走査するため、設定ファイルの更新は不要です。一覧ページにも自動で並びます。
ファイル名の先頭を `_` にすると下書き扱いでビルド対象から外れます。

## 生成される HTML

- **単一ファイル完結**。外部 CDN を参照しないため、ダウンロードしてオフラインでも読めます
- インクリメンタル検索（用語名＋本文の全文、ヒット件数表示）
- PC はヘッダー固定＋左メニューと本文の独立スクロール、スマホはドロワー目次
- ダークモード（OS 設定に追従＋手動切替を `localStorage` に保存）

## Markdown の書式

`build.py` は汎用の Markdown パーサではなく、この文書構造に合わせた簡易変換器です。
対応記法は [CLAUDE.md](CLAUDE.md) にまとめています。**表とコードブロックは未対応**です。

## GitHub Pages の設定

リポジトリの Settings → Pages で以下を選びます。

- Source: `Deploy from a branch`
- Branch: `main` / フォルダ: `/docs`

## 注意

内容の正確性は保証しません。試験対策としてご利用の際は、必ず公式の試験ガイドをあわせて確認してください。
特に製品名は改称されることがあります（例：2026年4月に Vertex AI → Gemini Enterprise Agent Platform）。
