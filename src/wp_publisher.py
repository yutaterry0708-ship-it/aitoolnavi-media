"""WordPress REST API Publisher: content/*.md -> aitoolnavi.com

Reads generated markdown articles and publishes them to WordPress via REST API.
Requires WP_USER and WP_APP_PASSWORD in .env

Usage:
    python wp_publisher.py                  # publish all pending articles
    python wp_publisher.py --dry-run        # preview without publishing
    python wp_publisher.py --file <path>    # publish specific file
"""
import os
import re
import sys
import json
import base64
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

ROOT = Path(__file__).parent.parent
CONTENT_DIR = ROOT / "content"
PUBLISHED_LOG = ROOT / "data" / "published.json"

WP_URL = os.getenv("WP_URL", "https://aitoolnavi.com")
WP_USER = os.getenv("WP_USER", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

DISCLOSURE = "※本記事はアフィリエイト広告（PR）を含みます。実際に使用・調査した内容に基づき公平に解説しています。\n\n"


def get_auth_header():
    token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def load_published():
    if PUBLISHED_LOG.exists():
        return json.loads(PUBLISHED_LOG.read_text(encoding="utf-8"))
    return {}


def save_published(data):
    PUBLISHED_LOG.parent.mkdir(exist_ok=True)
    PUBLISHED_LOG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_markdown(md_path: Path):
    """Extract title, excerpt, tags, and body from generated article."""
    text = md_path.read_text(encoding="utf-8")

    # Extract frontmatter-style metadata if present
    title = ""
    excerpt = ""
    tags = []

    # Try to get title from first H1
    h1 = re.search(r"^# (.+)$", text, re.MULTILINE)
    if h1:
        title = h1.group(1).strip()

    # Try meta block at top
    meta_title = re.search(r"(?:title|タイトル)[:\s]+(.+)", text[:500])
    if meta_title and not title:
        title = meta_title.group(1).strip()

    # Excerpt from first non-heading paragraph
    paras = re.findall(r"(?:^|\n)(?!#)(.{40,200})", text)
    if paras:
        excerpt = paras[0].strip()[:200]

    # Tags from keywords in filename
    slug = md_path.stem
    tags = [t for t in re.split(r"[-_]", slug) if len(t) > 1 and not t[0].isdigit()][:5]

    # Convert markdown to HTML (basic)
    body = md_to_html(text)

    # Prepend disclosure
    body = f'<p class="affiliate-disclosure">{DISCLOSURE}</p>\n' + body

    return {
        "title": title or slug,
        "content": body,
        "excerpt": excerpt,
        "slug": slug,
        "tags": tags,
        "status": "publish",
        "categories": [],
    }


def md_to_html(md: str) -> str:
    """Basic markdown to HTML conversion."""
    try:
        import markdown
        return markdown.markdown(md, extensions=["tables", "fenced_code"])
    except ImportError:
        pass

    # Fallback: manual conversion
    lines = md.split("\n")
    html_lines = []
    in_list = False
    in_code = False

    for line in lines:
        if line.startswith("```"):
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                html_lines.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            html_lines.append(line)
            continue

        # Headers
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("- ") or line.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item = line[2:]
            item = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item)
            html_lines.append(f"<li>{item}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if line.strip():
                line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
                line = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', line)
                html_lines.append(f"<p>{line}</p>")
            else:
                html_lines.append("")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def publish_post(post_data: dict, dry_run=False) -> dict:
    """Publish a post to WordPress via REST API."""
    if dry_run:
        print(f"  [DRY-RUN] Would publish: {post_data['title']}")
        return {"id": 0, "link": "dry-run"}

    headers = get_auth_header()
    headers["Content-Type"] = "application/json"

    # Create or get tags
    tag_ids = []
    for tag in post_data.get("tags", []):
        r = requests.get(
            f"{WP_URL}/wp-json/wp/v2/tags",
            params={"search": tag},
            headers=get_auth_header(),
            timeout=15,
        )
        existing = r.json()
        if existing:
            tag_ids.append(existing[0]["id"])
        else:
            r2 = requests.post(
                f"{WP_URL}/wp-json/wp/v2/tags",
                json={"name": tag},
                headers=headers,
                timeout=15,
            )
            if r2.ok:
                tag_ids.append(r2.json()["id"])

    payload = {
        "title": post_data["title"],
        "content": post_data["content"],
        "excerpt": post_data["excerpt"],
        "slug": post_data["slug"],
        "status": post_data["status"],
        "tags": tag_ids,
    }

    r = requests.post(
        f"{WP_URL}/wp-json/wp/v2/posts",
        json=payload,
        headers=headers,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def get_pending_articles(published: dict) -> list:
    """Find articles not yet published."""
    articles = sorted(CONTENT_DIR.glob("*.md"), reverse=False)
    return [a for a in articles if a.name not in published]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--file", help="特定ファイルのみ公開")
    ap.add_argument("--check-auth", action="store_true", help="認証テストのみ")
    args = ap.parse_args()

    if not WP_USER or not WP_APP_PASSWORD:
        print("ERROR: WP_USER と WP_APP_PASSWORD を .env に設定してください")
        print("  WordPress管理画面 → ユーザー → プロフィール → アプリケーションパスワード")
        sys.exit(1)

    if args.check_auth:
        r = requests.get(
            f"{WP_URL}/wp-json/wp/v2/users/me",
            headers=get_auth_header(),
            timeout=10,
        )
        if r.ok:
            print(f"認証OK: {r.json().get('name')} ({r.json().get('slug')})")
        else:
            print(f"認証NG: {r.status_code} {r.text[:200]}")
        return

    published = load_published()

    if args.file:
        targets = [Path(args.file)]
    else:
        targets = get_pending_articles(published)

    if not targets:
        print("公開待ち記事なし")
        return

    print(f"公開対象: {len(targets)} 件")
    for md_path in targets:
        print(f"\n→ {md_path.name}")
        try:
            post_data = parse_markdown(md_path)
            print(f"  タイトル: {post_data['title']}")
            result = publish_post(post_data, dry_run=args.dry_run)
            if not args.dry_run:
                published[md_path.name] = {
                    "wp_id": result.get("id"),
                    "link": result.get("link"),
                    "published_at": result.get("date"),
                }
                save_published(published)
                print(f"  公開済: {result.get('link')}")
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n完了")


if __name__ == "__main__":
    main()
