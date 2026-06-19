"""Static HTML Publisher: content/*.md -> docs/ (GitHub Pages / Cloudflare Pages)

WordPress不要。生成した記事をHTML化してdocs/フォルダに出力。
GitHub Pages または Cloudflare Pages で無料公開可能。

Usage:
    python static_publisher.py          # 全記事をHTML化
    python static_publisher.py --serve  # ローカルプレビュー(port 8080)
"""
import os
import re
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import yaml

ROOT = Path(__file__).parent.parent
CONTENT_DIR = ROOT / "content"
OUTPUT_DIR = ROOT / "docs"  # GitHub Pages convention

DISCLOSURE = "※本記事はアフィリエイト広告（PR）を含みます。実際に使用・調査した内容に基づき公平に解説しています。"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{description}">
<title>{title} | AIツールナビ</title>
<link rel="canonical" href="https://aitoolnavi.com/{slug}/">
<style>
:root{{--accent:#6366f1;--bg:#0f172a;--surface:#1e293b;--text:#f8fafc;--muted:#94a3b8}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Hiragino Sans','Yu Gothic',sans-serif;background:var(--bg);color:var(--text);line-height:1.8;font-size:17px}}
.container{{max-width:800px;margin:0 auto;padding:0 20px}}
header{{background:var(--surface);border-bottom:3px solid var(--accent);padding:16px 0}}
header a{{color:var(--text);text-decoration:none;font-weight:700;font-size:1.2rem}}
.hero{{padding:60px 0 40px;border-bottom:1px solid #334155}}
h1{{font-size:clamp(1.4rem,4vw,2rem);line-height:1.4;color:var(--text);margin-bottom:16px}}
.meta{{color:var(--muted);font-size:.9rem;margin-bottom:24px}}
.disclosure{{background:#1e293b;border-left:4px solid var(--accent);padding:12px 16px;font-size:.85rem;color:var(--muted);margin:24px 0;border-radius:0 4px 4px 0}}
article{{padding:40px 0}}
article h2{{font-size:1.5rem;color:var(--accent);margin:40px 0 16px;padding-bottom:8px;border-bottom:2px solid #334155}}
article h3{{font-size:1.2rem;margin:28px 0 12px;color:#e2e8f0}}
article p{{margin-bottom:16px;color:#cbd5e1}}
article ul,article ol{{margin:16px 0 16px 24px;color:#cbd5e1}}
article li{{margin-bottom:8px}}
article strong{{color:var(--text)}}
article a{{color:var(--accent);text-decoration:none}}
article a:hover{{text-decoration:underline}}
.aff-link{{display:inline-block;background:var(--accent);color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;margin:8px 0;font-weight:600}}
.aff-link:hover{{opacity:.85;text-decoration:none}}
footer{{background:var(--surface);padding:32px 0;text-align:center;color:var(--muted);font-size:.85rem;margin-top:60px}}
</style>
</head>
<body>
<header><div class="container"><a href="/">AIツールナビ</a></div></header>
<main>
<div class="hero container">
<h1>{title}</h1>
<div class="meta">更新日: {date} | AIツールナビ編集部</div>
<div class="disclosure">{disclosure}</div>
</div>
<article class="container">
{body}
</article>
</main>
<footer><div class="container">© 2026 AIツールナビ | <a href="/">トップ</a></div></footer>
</body>
</html>"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="AIツール・SaaSを実際に使って比較するメディア。ChatGPT・Claude・Notionなど最新AIツールの使い方を徹底解説。">
<title>AIツールナビ | AI・SaaSツール比較メディア</title>
<style>
:root{{--accent:#6366f1;--bg:#0f172a;--surface:#1e293b;--text:#f8fafc;--muted:#94a3b8}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Hiragino Sans','Yu Gothic',sans-serif;background:var(--bg);color:var(--text);line-height:1.8}}
.container{{max-width:1100px;margin:0 auto;padding:0 20px}}
header{{background:var(--surface);border-bottom:3px solid var(--accent);padding:20px 0}}
header h1{{font-size:1.5rem;font-weight:700}}
header p{{color:var(--muted);font-size:.9rem;margin-top:4px}}
.hero{{padding:60px 0;text-align:center}}
.hero h2{{font-size:clamp(1.5rem,5vw,2.5rem);margin-bottom:16px}}
.hero p{{color:var(--muted);max-width:600px;margin:0 auto}}
.articles{{padding:40px 0}}
.articles h2{{font-size:1.4rem;margin-bottom:24px;color:var(--accent)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px}}
.card{{background:var(--surface);border-radius:10px;padding:24px;border:1px solid #334155;transition:.2s}}
.card:hover{{border-color:var(--accent);transform:translateY(-2px)}}
.card h3{{font-size:1.05rem;margin-bottom:10px;line-height:1.5}}
.card h3 a{{color:var(--text);text-decoration:none}}
.card h3 a:hover{{color:var(--accent)}}
.card .meta{{color:var(--muted);font-size:.8rem}}
footer{{background:var(--surface);padding:32px 0;text-align:center;color:var(--muted);font-size:.85rem;margin-top:60px}}
</style>
</head>
<body>
<header><div class="container"><h1>AIツールナビ</h1><p>実際に使って選ぶ、AIツールの比較メディア</p></div></header>
<main>
<div class="hero container">
<h2>AIツール・SaaSを<br>本音でレビュー</h2>
<p>ChatGPT・Claude・Notion・GitHub Copilotなど、最新AIツールの使い方・比較・活用法を毎日更新</p>
</div>
<div class="articles container">
<h2>最新記事</h2>
<div class="grid">
{cards}
</div>
</div>
</main>
<footer><div class="container">© 2026 AIツールナビ | AIツール比較メディア</div></footer>
</body>
</html>"""


def md_to_html(md: str) -> str:
    """Markdown → HTML（基本変換）"""
    try:
        import markdown
        return markdown.markdown(md, extensions=["tables", "fenced_code", "nl2br"])
    except ImportError:
        pass
    # Fallback
    lines = md.split("\n")
    out, in_ul, in_ol, in_code = [], False, False, False
    for line in lines:
        if line.startswith("```"):
            if in_code:
                out.append("</code></pre>"); in_code = False
            else:
                out.append('<pre><code>'); in_code = True
            continue
        if in_code:
            out.append(line.replace("<", "&lt;").replace(">", "&gt;")); continue
        if line.startswith("### "): out.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "): out.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "): out.append(f"<h1>{line[2:]}</h1>")
        elif re.match(r"^\d+\. ", line):
            if not in_ol: out.append("<ol>"); in_ol = True
            out.append(f"<li>{line[3:]}</li>")
        elif line.startswith("- ") or line.startswith("* "):
            if not in_ul: out.append("<ul>"); in_ul = True
            out.append(f"<li>{line[2:]}</li>")
        else:
            if in_ul: out.append("</ul>"); in_ul = False
            if in_ol: out.append("</ol>"); in_ol = False
            if line.strip():
                line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
                line = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', line)
                out.append(f"<p>{line}</p>")
    if in_ul: out.append("</ul>")
    if in_ol: out.append("</ol>")
    return "\n".join(out)


def parse_md(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    h1 = re.search(r"^# (.+)$", text, re.MULTILINE)
    title = h1.group(1).strip() if h1 else md_path.stem
    body_md = re.sub(r"^# .+\n", "", text, count=1, flags=re.MULTILINE)
    paras = [p.strip() for p in body_md.split("\n") if p.strip() and not p.startswith("#")]
    desc = paras[0][:120] if paras else title
    body_html = md_to_html(body_md)
    slug = md_path.stem
    date_m = re.match(r"(\d{4}-\d{2}-\d{2})", slug)
    date = date_m.group(1) if date_m else "2026-06-19"
    return {"title": title, "slug": slug, "date": date, "description": desc, "body": body_html}


def build_site():
    OUTPUT_DIR.mkdir(exist_ok=True)
    articles = []
    mds = sorted(CONTENT_DIR.glob("*.md"), reverse=True)
    print(f"記事数: {len(mds)} 本")
    for md_path in mds:
        info = parse_md(md_path)
        out_dir = OUTPUT_DIR / info["slug"]
        out_dir.mkdir(exist_ok=True)
        html = HTML_TEMPLATE.format(
            title=info["title"],
            slug=info["slug"],
            date=info["date"],
            description=info["description"],
            disclosure=DISCLOSURE,
            body=info["body"],
        )
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        articles.append(info)
        print(f"  → docs/{info['slug']}/index.html")

    # Build index
    cards = "\n".join(
        f'<div class="card"><h3><a href="/{a["slug"]}/">{a["title"]}</a></h3>'
        f'<div class="meta">{a["date"]}</div></div>'
        for a in articles
    )
    index_html = INDEX_TEMPLATE.format(cards=cards)
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print(f"\nindex.html 作成完了")
    print(f"→ docs/ フォルダを GitHub にpushすれば即公開！")
    print(f"  GitHub Pages: https://<user>.github.io/<repo>/")
    print(f"  Cloudflare Pages: 無料・独自ドメイン対応")
    return len(articles)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true", help="ローカルプレビュー")
    args = ap.parse_args()
    n = build_site()
    if args.serve:
        import http.server, socketserver, os
        os.chdir(OUTPUT_DIR)
        with socketserver.TCPServer(("", 8080), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"\nプレビュー: http://localhost:8080")
            httpd.serve_forever()


if __name__ == "__main__":
    main()
