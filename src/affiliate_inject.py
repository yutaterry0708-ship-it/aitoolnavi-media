"""Replace [[AFF:name]] placeholders with real affiliate links from config.

Placeholders whose URL is not set yet are left untouched (never destroyed), so
adding the URL to config.yaml later fills them in on the next run.
static_publisher.py hides unresolved placeholders from the public pages.

Usage:
    python affiliate_inject.py
"""
import os
import re
import glob

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def inject(text, links):
    def repl(m):
        name = m.group(1).strip()
        url = links.get(name)
        if not url:
            return m.group(0)
        return (f'<a href="{url}" rel="sponsored nofollow noopener" '
                f'target="_blank">{name}を公式サイトで見る</a>')
    return re.sub(r"\[\[AFF:(.*?)\]\]", repl, text)


def main():
    cfg = load_config()
    links = (cfg.get("affiliate", {}) or {}).get("links", {}) or {}
    content_dir = os.path.join(ROOT, cfg["content"]["output_dir"])
    for path in glob.glob(os.path.join(content_dir, "*.md")):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        new = inject(text, links)
        if new != text:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(new)
            print(f"Injected: {os.path.basename(path)}")


if __name__ == "__main__":
    main()
