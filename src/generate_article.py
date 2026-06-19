"""Generate one E-E-A-T SEO article (markdown + frontmatter) from a keyword.

Usage:
    python generate_article.py --keyword "Notion AI 使い方" --title "..." --intent commercial
"""
import os
import re
import datetime
import argparse

import yaml

from llm import call_claude

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text or "").strip().lower()
    return re.sub(r"[\s_]+", "-", text)[:60] or "post"


def build_prompt(keyword, title, intent, affiliate_tag, cfg):
    niche = cfg["niche"]["primary"]
    min_words = cfg["seo"]["min_words"]
    brand = cfg["brand"]["name"]
    disclosure = cfg["content"]["disclosure"]
    today = datetime.date.today().isoformat()
    return f"""あなたは「{niche}」を専門に、実際に多数のツールを使い込んできた日本語ライターです（媒体名: {brand}）。
Googleの E-E-A-T（経験・専門性・権威性・信頼性）を強く満たす記事を書いてください。
AI量産の薄い記事は順位が付きません。実体験ベースの具体例・比較・正直なデメリットを必ず入れること。

対象キーワード: {keyword}
記事タイトル: {title}
検索意図: {intent}
紐づけ案件ヒント: {affiliate_tag}

# 要件
- 文字数: {min_words}字以上
- 構成: 導入(悩みに共感＋結論先出し) → 本文(H2/H3で整理) → 比較表(Markdown表) → 正直なメリット/デメリット → FAQ(3問) → まとめ
- 経験の明示: 「実際に使ってみて」「私の運用では」等を自然に。ただし"嘘の固有数値"は作らず一般論として書く
- アフィリンクを置く箇所に必ず `[[AFF:案件名]]` プレースホルダーを2〜4個入れる（後で実リンクに置換）
- 禁止: 「必ず稼げる/治る/痩せる」等の断定（景表法・薬機法）。金融・投資・医療の助言は一切書かない
- 冒頭にYAMLフロントマターを付ける

# 出力フォーマット（これ以外の前置きを書かない）
---
title: "{title}"
description: "<120字以内のメタディスクリプション>"
keywords: ["{keyword}"]
date: "{today}"
draft: false
---

> {disclosure}

<ここから本文(Markdown)>
"""


def generate(keyword, title, intent, affiliate_tag, cfg):
    prompt = build_prompt(keyword, title, intent, affiliate_tag, cfg)
    return call_claude(
        prompt,
        model=cfg["llm"]["article_model"],
        max_tokens=8000,
        temperature=cfg["llm"].get("temperature", 0.7),
    )


def save(markdown, title, cfg):
    out_dir = os.path.join(ROOT, cfg["content"]["output_dir"])
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{datetime.date.today().isoformat()}-{slugify(title)}.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(markdown)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", required=True)
    ap.add_argument("--title", default=None)
    ap.add_argument("--intent", default="informational")
    ap.add_argument("--affiliate-tag", default="なし")
    args = ap.parse_args()

    cfg = load_config()
    title = args.title or args.keyword
    md = generate(args.keyword, title, args.intent, args.affiliate_tag, cfg)
    print(f"Wrote {save(md, title, cfg)}")


if __name__ == "__main__":
    main()
