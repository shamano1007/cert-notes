#!/usr/bin/env python3
"""AIリーダー.md から単一ファイルの AIリーダー.html を生成する。

使い方:
    python3 build.py                # ../AIリーダー.md を読んで AIリーダー.html を出力
    python3 build.py path/to/foo.md # 入力を明示
"""

import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_SRC = HERE.parent / "AIリーダー.md"
OUT = HERE / "AIリーダー.html"

BOLD = re.compile(r"\*\*(.+?)\*\*")


def inline(text: str) -> str:
    """インライン記法（太字）だけを変換する。"""
    out = html.escape(text.strip())
    return BOLD.sub(r"<strong>\1</strong>", out)


def render_blocks(lines: list[str]) -> str:
    """本文行を段落と箇条書きに振り分けて HTML に変換する。

    Markdown 側では「導入文の直後に空行なしで箇条書き」が多いため、
    ブロック単位ではなく行単位で段落／リストを切り替える。
    """
    parts: list[str] = []
    para: list[str] = []
    items: list[list[str]] = []

    def flush_para() -> None:
        if para:
            parts.append(render_paragraph(para))
            para.clear()

    def flush_list() -> None:
        if not items:
            return
        rendered = []
        for item in items:
            head = inline(item[0])
            rest = "".join(f"<br>{inline(x)}" for x in item[1:])
            rendered.append(f"<li>{head}{rest}</li>")
        parts.append("<ul>" + "".join(rendered) + "</ul>")
        items.clear()

    for raw in lines:
        if not raw.strip():
            flush_list()
            flush_para()
            continue
        if raw.lstrip().startswith("- "):
            flush_para()
            items.append([raw.lstrip()[2:]])
        elif items and (raw.startswith("    ") or raw.startswith("\t")):
            items[-1].append(raw.strip())  # 直前の項目の続き（インデント行）
        else:
            flush_list()
            para.append(raw.strip())
    flush_list()
    flush_para()
    return "\n".join(parts)


def render_paragraph(lines: list[str]) -> str:
    """通常行はまとめて <p>、※ / ⚠️ で始まる行はコールアウトにする。"""
    parts: list[str] = []
    buf: list[str] = []

    def flush_buf() -> None:
        if buf:
            parts.append("<p>" + "<br>".join(inline(x) for x in buf) + "</p>")
            buf.clear()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("⚠️"):
            flush_buf()
            parts.append(f'<p class="callout warn">{inline(stripped.lstrip("⚠️").strip())}</p>')
        elif stripped.startswith("※"):
            flush_buf()
            parts.append(f'<p class="callout note">{inline(stripped.lstrip("※").strip())}</p>')
        else:
            buf.append(stripped)
    flush_buf()
    return "\n".join(parts)


def parse(md: str) -> tuple[str, str, list[dict]]:
    """(タイトル, リード文, 章リスト) を返す。手書きの目次セクションは捨てる。"""
    title = "用語集"
    lead: list[str] = []
    chapters: list[dict] = []
    # None=冒頭 / "skip"=手書き目次 / "term" / "sub"
    mode = "lead"
    buf: list[str] = []

    def stash() -> None:
        """現在のバッファを、直近の見出しの本文として確定する。"""
        nonlocal buf
        body = list(buf)
        buf = []
        if mode == "lead":
            lead.extend(body)
        elif mode == "skip":
            pass
        elif chapters and chapters[-1]["terms"]:
            term = chapters[-1]["terms"][-1]
            if term["subs"]:
                term["subs"][-1]["body"].extend(body)
            else:
                term["body"].extend(body)

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.strip() == "---":
            continue
        if line.startswith("# "):
            stash()
            heading = line[2:].strip()
            if not chapters and not heading.startswith("第"):
                title = heading
                mode = "lead"
            else:
                chapters.append({"title": heading, "terms": []})
                mode = "term"
            continue
        if line.startswith("## "):
            stash()
            heading = line[3:].strip()
            if heading == "目次":
                mode = "skip"
                continue
            if not chapters:  # 章の外に出てきた用語は入れ物を作って受ける
                chapters.append({"title": "", "terms": []})
            chapters[-1]["terms"].append({"title": heading, "body": [], "subs": []})
            mode = "term"
            continue
        if line.startswith("### "):
            stash()
            if chapters and chapters[-1]["terms"]:
                chapters[-1]["terms"][-1]["subs"].append(
                    {"title": line[4:].strip(), "body": []}
                )
                mode = "sub"
            continue
        buf.append(line)
    stash()
    return title, "\n".join(x for x in lead if x.strip()), chapters


def build(src: Path) -> str:
    title, lead, chapters = parse(src.read_text(encoding="utf-8"))

    nav: list[str] = []
    main: list[str] = []
    total = 0

    for ci, chapter in enumerate(chapters, 1):
        cid = f"c{ci}"
        nav.append(f'<li class="nav-chapter" data-chapter="{cid}">')
        nav.append(f'<a href="#{cid}">{html.escape(chapter["title"])}</a><ul>')
        main.append(f'<section class="chapter" id="{cid}" data-chapter="{cid}">')
        main.append(f'<h2 class="chapter-title">{html.escape(chapter["title"])}</h2>')

        for term in chapter["terms"]:
            total += 1
            tid = f"t{total}"
            name = html.escape(term["title"])
            nav.append(f'<li class="nav-term" data-target="{tid}"><a href="#{tid}">{name}</a></li>')

            main.append(f'<article class="term" id="{tid}" data-term="{tid}">')
            main.append(f'<h3 class="term-title"><a class="anchor" href="#{tid}">{name}</a></h3>')
            main.append(render_blocks(term["body"]))
            for sub in term["subs"]:
                main.append(f'<h4 class="sub-title">{html.escape(sub["title"])}</h4>')
                main.append(render_blocks(sub["body"]))
            main.append("</article>")

        nav.append("</ul></li>")
        main.append("</section>")

    return TEMPLATE.format(
        title=html.escape(title),
        title_json=json.dumps(title, ensure_ascii=False),
        lead=render_blocks(lead.splitlines()),
        nav="\n".join(nav),
        main="\n".join(main),
        total=total,
        chapters=len(chapters),
    )


TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="description" content="Google Cloud Generative AI Leader 認定試験の用語集。{total}用語を{chapters}章に整理。">
<title>{title}</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📘</text></svg>">
<style>
:root {{
  --bg: #ffffff;
  --bg-soft: #f6f7f9;
  --bg-card: #ffffff;
  --fg: #1a1d21;
  --fg-muted: #5b6472;
  --line: #e2e6ec;
  --accent: #1a73e8;
  --accent-soft: #e8f0fe;
  --warn-bg: #fff4e5;
  --warn-line: #f0a63c;
  --warn-fg: #7a4a06;
  --note-bg: #f2f4f7;
  --note-fg: #4a5361;
  --mark: #ffe680;
  --shadow: 0 1px 2px rgba(16,24,40,.06), 0 1px 3px rgba(16,24,40,.10);
  --header-h: 56px;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #0f1216;
    --bg-soft: #161a20;
    --bg-card: #171c22;
    --fg: #e6e9ee;
    --fg-muted: #9aa4b2;
    --line: #262d36;
    --accent: #7cb0ff;
    --accent-soft: #1b2836;
    --warn-bg: #2e2311;
    --warn-line: #b9822f;
    --warn-fg: #f0c489;
    --note-bg: #1b2028;
    --note-fg: #aab3c0;
    --mark: #6b5a12;
    --shadow: none;
  }}
}}
:root[data-theme="light"] {{
  --bg: #ffffff; --bg-soft: #f6f7f9; --bg-card: #ffffff;
  --fg: #1a1d21; --fg-muted: #5b6472; --line: #e2e6ec;
  --accent: #1a73e8; --accent-soft: #e8f0fe;
  --warn-bg: #fff4e5; --warn-line: #f0a63c; --warn-fg: #7a4a06;
  --note-bg: #f2f4f7; --note-fg: #4a5361; --mark: #ffe680;
  --shadow: 0 1px 2px rgba(16,24,40,.06), 0 1px 3px rgba(16,24,40,.10);
}}
:root[data-theme="dark"] {{
  --bg: #0f1216; --bg-soft: #161a20; --bg-card: #171c22;
  --fg: #e6e9ee; --fg-muted: #9aa4b2; --line: #262d36;
  --accent: #7cb0ff; --accent-soft: #1b2836;
  --warn-bg: #2e2311; --warn-line: #b9822f; --warn-fg: #f0c489;
  --note-bg: #1b2028; --note-fg: #aab3c0; --mark: #6b5a12;
  --shadow: none;
}}

* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Hiragino Kaku Gothic ProN",
               "Noto Sans JP", "Yu Gothic UI", Meiryo, sans-serif;
  font-size: 16px;
  line-height: 1.85;
  -webkit-text-size-adjust: 100%;
  overflow-wrap: anywhere;
}}

/* ---------- header ---------- */
header {{
  position: sticky; top: 0; z-index: 40;
  height: var(--header-h);
  display: flex; align-items: center; gap: 8px;
  padding: 0 12px;
  padding-top: env(safe-area-inset-top);
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: saturate(180%) blur(12px);
  border-bottom: 1px solid var(--line);
}}
.brand {{
  font-weight: 700; font-size: 15px; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; flex: 1; min-width: 0;
}}
.iconbtn {{
  flex: none;
  width: 38px; height: 38px; display: grid; place-items: center;
  border: 1px solid var(--line); border-radius: 10px;
  background: var(--bg-card); color: var(--fg);
  font-size: 17px; cursor: pointer; padding: 0;
}}
.iconbtn:active {{ transform: scale(.95); }}
@media (min-width: 900px) {{ #menuBtn {{ display: none; }} }}

/* ---------- search ---------- */
.searchwrap {{ position: relative; flex: 2; min-width: 120px; max-width: 340px; }}
#search {{
  width: 100%; height: 38px;
  padding: 0 30px 0 32px;
  border: 1px solid var(--line); border-radius: 10px;
  background: var(--bg-soft); color: var(--fg);
  font-size: 16px; font-family: inherit;
}}
#search:focus {{ outline: 2px solid var(--accent); outline-offset: -1px; background: var(--bg-card); }}
.searchwrap::before {{
  content: "🔍"; position: absolute; left: 9px; top: 50%;
  transform: translateY(-50%); font-size: 13px; opacity: .65; pointer-events: none;
}}
#clearBtn {{
  position: absolute; right: 4px; top: 50%; transform: translateY(-50%);
  width: 24px; height: 24px; border: 0; border-radius: 6px;
  background: transparent; color: var(--fg-muted); cursor: pointer;
  font-size: 15px; line-height: 1; display: none;
}}
#clearBtn.on {{ display: block; }}

/* ---------- layout ----------
   モバイル: ページ全体をスクロール（アドレスバー収納やプルリフレッシュを殺さない）
   PC(>=900px): ヘッダー固定 + 左メニューと右本文をそれぞれ独立スクロール       */
.wrap {{ display: block; }}
@media (min-width: 900px) {{
  html, body {{ height: 100%; }}
  body {{ display: flex; flex-direction: column; overflow: hidden; }}
  header {{ position: static; flex: none; }}
  .wrap {{
    flex: 1; min-height: 0;
    display: grid; grid-template-columns: 290px minmax(0, 1fr);
  }}
}}

/* ---------- sidebar ---------- */
#sidebar {{
  position: fixed; inset: 0 auto 0 0; z-index: 50;
  width: min(86vw, 330px);
  background: var(--bg-soft);
  border-right: 1px solid var(--line);
  overflow-y: auto; overscroll-behavior: contain;
  padding: 14px 12px 40px;
  transform: translateX(-102%);
  transition: transform .22s ease;
}}
#sidebar.open {{ transform: none; box-shadow: 0 0 40px rgba(0,0,0,.35); }}
@media (min-width: 900px) {{
  #sidebar {{
    position: static; transform: none; box-shadow: none;
    width: auto; inset: auto; height: 100%; min-height: 0;
    overscroll-behavior: contain;
  }}
}}
#overlay {{
  position: fixed; inset: 0; z-index: 45;
  background: rgba(0,0,0,.42); opacity: 0; pointer-events: none;
  transition: opacity .22s ease;
}}
#overlay.on {{ opacity: 1; pointer-events: auto; }}
@media (min-width: 900px) {{ #overlay {{ display: none; }} }}

#sidebar ul {{ list-style: none; margin: 0; padding: 0; }}
.nav-chapter {{ margin-bottom: 6px; }}
.nav-chapter > a {{
  display: block; padding: 7px 10px;
  font-weight: 700; font-size: 13.5px; letter-spacing: .01em;
  color: var(--fg); text-decoration: none; border-radius: 8px;
}}
.nav-chapter > a:hover {{ background: var(--accent-soft); }}
.nav-chapter > ul {{ margin: 0 0 10px 4px; border-left: 2px solid var(--line); padding-left: 8px; }}
.nav-term > a {{
  display: block; padding: 5px 9px;
  font-size: 13.5px; line-height: 1.5;
  color: var(--fg-muted); text-decoration: none; border-radius: 7px;
}}
.nav-term > a:hover {{ background: var(--accent-soft); color: var(--accent); }}
.nav-term.active > a {{ background: var(--accent-soft); color: var(--accent); font-weight: 600; }}

/* ---------- content ---------- */
main {{ width: 100%; }}
.inner {{ padding: 20px 16px 96px; max-width: 820px; margin: 0 auto; }}
@media (min-width: 900px) {{
  main {{
    min-height: 0; height: 100%;
    overflow-y: auto; overscroll-behavior: contain;
    scroll-behavior: smooth;
  }}
  .inner {{ padding: 28px 44px 120px; }}
  /* PC ではヘッダーがスクロール領域の外にあるので余白を詰める */
  .chapter, .term {{ scroll-margin-top: 14px; }}
}}

.lead {{ margin-bottom: 22px; }}
.lead h1 {{ font-size: 23px; line-height: 1.45; margin: 0 0 8px; letter-spacing: -.01em; }}
@media (min-width: 900px) {{ .lead h1 {{ font-size: 30px; }} }}
.lead p {{ color: var(--fg-muted); font-size: 14.5px; margin: 0; }}
.stats {{
  display: flex; gap: 8px; flex-wrap: wrap; margin-top: 14px;
  font-size: 12.5px; color: var(--fg-muted);
}}
.stats span {{
  background: var(--bg-soft); border: 1px solid var(--line);
  border-radius: 999px; padding: 3px 11px;
}}

.chapter {{ margin-top: 40px; scroll-margin-top: calc(var(--header-h) + 10px); }}
.chapter-title {{
  font-size: 19px; margin: 0 0 4px;
  padding-bottom: 9px; border-bottom: 2px solid var(--accent);
  letter-spacing: -.01em;
}}

.term {{
  margin-top: 18px; padding: 16px 17px;
  background: var(--bg-card);
  border: 1px solid var(--line); border-radius: 13px;
  box-shadow: var(--shadow);
  scroll-margin-top: calc(var(--header-h) + 10px);
}}
.term-title {{ font-size: 17px; margin: 0 0 10px; line-height: 1.45; }}
.term-title .anchor {{ color: var(--fg); text-decoration: none; }}
.term-title .anchor:hover {{ color: var(--accent); }}
.term-title .anchor::after {{
  content: " #"; color: var(--accent); opacity: 0; font-weight: 400; font-size: .85em;
}}
.term-title:hover .anchor::after {{ opacity: .55; }}
.term:target {{ border-color: var(--accent); }}

.sub-title {{
  font-size: 14.5px; margin: 18px 0 8px;
  color: var(--accent); letter-spacing: .01em;
}}
.term p {{ margin: 0 0 10px; font-size: 15px; }}
.term p:last-child {{ margin-bottom: 0; }}
.term ul {{ margin: 0 0 10px; padding-left: 1.25em; font-size: 15px; }}
.term li {{ margin-bottom: 7px; }}
.term li:last-child {{ margin-bottom: 0; }}
strong {{ font-weight: 700; }}

.callout {{
  padding: 9px 13px; border-radius: 9px; font-size: 14px; line-height: 1.75;
}}
.callout.note {{ background: var(--note-bg); color: var(--note-fg); }}
.callout.warn {{
  background: var(--warn-bg); color: var(--warn-fg);
  border-left: 3px solid var(--warn-line);
}}
.callout.warn::before {{ content: "⚠️ "; }}
.callout.note::before {{ content: "※ "; opacity: .8; }}

mark {{ background: var(--mark); color: inherit; border-radius: 3px; padding: 0 1px; }}

#empty {{
  display: none; text-align: center; color: var(--fg-muted);
  padding: 60px 20px; font-size: 15px;
}}
#empty.on {{ display: block; }}
#count {{
  display: none; margin: 4px 0 0; font-size: 13px; color: var(--fg-muted);
}}
#count.on {{ display: block; }}

#top {{
  position: fixed; right: 14px; z-index: 30;
  bottom: calc(14px + env(safe-area-inset-bottom));
  width: 44px; height: 44px; border-radius: 50%;
  border: 1px solid var(--line); background: var(--bg-card); color: var(--fg);
  font-size: 17px; cursor: pointer; box-shadow: 0 3px 12px rgba(0,0,0,.18);
  opacity: 0; pointer-events: none; transition: opacity .2s;
}}
#top.on {{ opacity: 1; pointer-events: auto; }}

@media print {{
  header, #sidebar, #overlay, #top {{ display: none !important; }}
  .wrap {{ display: block; }}
  .term {{ break-inside: avoid; box-shadow: none; }}
}}
</style>
</head>
<body>

<header>
  <button class="iconbtn" id="menuBtn" aria-label="目次を開く">☰</button>
  <span class="brand">{title}</span>
  <div class="searchwrap">
    <input id="search" type="search" placeholder="用語を検索…" autocomplete="off"
           enterkeyhint="search" aria-label="用語を検索">
    <button id="clearBtn" aria-label="検索をクリア">✕</button>
  </div>
  <button class="iconbtn" id="themeBtn" aria-label="配色を切り替え">◐</button>
</header>

<div id="overlay"></div>

<div class="wrap">
  <nav id="sidebar" aria-label="目次">
    <ul id="nav">
{nav}
    </ul>
  </nav>

  <main>
   <div class="inner">
    <div class="lead">
      <h1>{title}</h1>
      {lead}
      <div class="stats"><span>全 {total} 用語</span><span>{chapters} 章</span></div>
      <p id="count"></p>
    </div>
    <div id="empty">該当する用語がありません</div>
{main}
   </div>
  </main>
</div>

<button id="top" aria-label="先頭へ戻る">↑</button>

<script>
(function () {{
  var root = document.documentElement;
  var KEY = "genai-glossary-theme";

  /* ---- theme ---- */
  try {{
    var saved = localStorage.getItem(KEY);
    if (saved) root.setAttribute("data-theme", saved);
  }} catch (e) {{}}
  document.getElementById("themeBtn").addEventListener("click", function () {{
    var dark = root.getAttribute("data-theme")
      ? root.getAttribute("data-theme") === "dark"
      : window.matchMedia("(prefers-color-scheme: dark)").matches;
    var next = dark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try {{ localStorage.setItem(KEY, next); }} catch (e) {{}}
  }});

  /* ---- drawer ---- */
  var sidebar = document.getElementById("sidebar");
  var overlay = document.getElementById("overlay");
  function closeNav() {{ sidebar.classList.remove("open"); overlay.classList.remove("on"); }}
  document.getElementById("menuBtn").addEventListener("click", function () {{
    sidebar.classList.toggle("open");
    overlay.classList.toggle("on", sidebar.classList.contains("open"));
  }});
  overlay.addEventListener("click", closeNav);
  sidebar.addEventListener("click", function (e) {{
    if (e.target.tagName === "A") closeNav();
  }});
  document.addEventListener("keydown", function (e) {{
    if (e.key === "Escape") {{ closeNav(); }}
  }});

  /* ---- search ---- */
  var terms = [].slice.call(document.querySelectorAll(".term")).map(function (el) {{
    return {{ el: el, id: el.id, text: el.textContent.toLowerCase() }};
  }});
  var navTerms = {{}};
  [].slice.call(document.querySelectorAll(".nav-term")).forEach(function (el) {{
    navTerms[el.getAttribute("data-target")] = el;
  }});
  var chapters = [].slice.call(document.querySelectorAll(".chapter"));
  var navChapters = [].slice.call(document.querySelectorAll(".nav-chapter"));
  var input = document.getElementById("search");
  var clearBtn = document.getElementById("clearBtn");
  var empty = document.getElementById("empty");
  var count = document.getElementById("count");

  function run() {{
    var q = input.value.trim().toLowerCase();
    clearBtn.classList.toggle("on", q.length > 0);
    var hits = 0;

    terms.forEach(function (t) {{
      var show = !q || t.text.indexOf(q) !== -1;
      t.el.style.display = show ? "" : "none";
      if (navTerms[t.id]) navTerms[t.id].style.display = show ? "" : "none";
      if (show) hits++;
    }});

    chapters.forEach(function (sec, i) {{
      var any = sec.querySelector('.term:not([style*="display: none"])');
      sec.style.display = any ? "" : "none";
      if (navChapters[i]) navChapters[i].style.display = any ? "" : "none";
    }});

    empty.classList.toggle("on", q.length > 0 && hits === 0);
    count.classList.toggle("on", q.length > 0);
    count.textContent = q ? hits + " 件ヒット" : "";
  }}

  input.addEventListener("input", run);
  clearBtn.addEventListener("click", function () {{ input.value = ""; run(); input.focus(); }});
  input.addEventListener("keydown", function (e) {{ if (e.key === "Escape") {{ input.value = ""; run(); }} }});
  document.addEventListener("keydown", function (e) {{
    if (e.key === "/" && document.activeElement !== input) {{ e.preventDefault(); input.focus(); }}
  }});

  /* ---- active section in nav ---- */
  if ("IntersectionObserver" in window) {{
    var current = null;
    var io = new IntersectionObserver(function (entries) {{
      entries.forEach(function (en) {{
        if (!en.isIntersecting) return;
        var nav = navTerms[en.target.id];
        if (!nav || nav === current) return;
        /* ハイライトのみ。メニュー側は自動スクロールさせない
           （スムーススクロール中に通過した用語ごとに発火して目次が暴れるため） */
        if (current) current.classList.remove("active");
        nav.classList.add("active");
        current = nav;
      }});
    }}, {{ rootMargin: "-70px 0px -70% 0px" }});
    terms.forEach(function (t) {{ io.observe(t.el); }});
  }}

  /* ---- back to top ----
     PC では main が、モバイルでは window がスクロール主体になるので両方を見る */
  var mainEl = document.querySelector("main");
  var top = document.getElementById("top");
  function onScroll() {{
    top.classList.toggle("on", (mainEl.scrollTop || window.scrollY) > 500);
  }}
  top.addEventListener("click", function () {{
    mainEl.scrollTo({{ top: 0, behavior: "smooth" }});
    window.scrollTo({{ top: 0, behavior: "smooth" }});
  }});
  mainEl.addEventListener("scroll", onScroll, {{ passive: true }});
  window.addEventListener("scroll", onScroll, {{ passive: true }});

  /* 検索で絞り込んだら先頭に戻す */
  input.addEventListener("input", function () {{
    mainEl.scrollTop = 0;
    if (!window.matchMedia("(min-width: 900px)").matches) window.scrollTo(0, 0);
  }});
}})();
</script>
</body>
</html>
"""


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    if not src.exists():
        sys.exit(f"入力が見つかりません: {src}")
    OUT.write_text(build(src), encoding="utf-8")
    print(f"{src} -> {OUT}")


if __name__ == "__main__":
    main()
