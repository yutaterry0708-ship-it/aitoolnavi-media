"""Generate a complete faceless YouTube video script from a topic/article.

Output: scripts/YYYYMMDD-slug.md with:
  - 台本（TTS向けマーカー付き）
  - サムネアイデア
  - タイトル案（3本）
  - タグ
  - 説明文（SEO最適化）
  - ピン留めコメント案

Usage:
    python youtube_script.py --keyword "Notion AI 使い方" --length 8
    python youtube_script.py --from-article ../content/2026-06-19-notion-ai.md
"""
import os
import sys
import datetime
import argparse
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm import call_claude
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(ROOT, "data", "youtube_scripts")


def load_config():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text or "").strip().lower()
    return re.sub(r"[\s_]+", "-", text)[:50] or "script"


def generate_script(topic, length_min, article_body, cfg):
    brand = cfg["brand"]["name"]
    prompt = f"""あなたは日本語の顔出しなしYouTubeチャンネルの脚本家です。
チャンネルコンセプト: {brand}（AIツール・SaaSの比較レビュー、非金融）
動画時間の目安: 約{length_min}分（600字/分として約{length_min * 600}字）

禁止: 顔/名前の言及・金融投資の助言・保証表現

参考コンテンツ（ある場合）:
{article_body[:4000] if article_body else '（なし）'}

トピック: {topic}

# 出力フォーマット（Markdownで書く）

## 📺 タイトル案（3本・クリックされる型）
1. ...
2. ...
3. ...

## 🖼️ サムネアイデア
- 背景: ...
- メインテキスト（大文字・衝撃系）: ...
- アイコン・素材: ...

## 🏷️ タグ（20〜30個）
...

## 📝 説明文（500字・SEO最適化）
...

## 📜 台本

### [HOOK] 最初15秒（視聴継続の命）
（視聴者の悩みに直撃するフレーズ → 動画で解決できると示す → 視聴者が得るものを宣言）
{{pause:1.0}}
...

### [INTRO] 30秒
（チャンネル説明・今日のゴール。簡潔に）
...

### [MAIN-1] ...
（H2見出しごとにセクション分け。TTS向けに｛pause:0.5｝を自然な場所に）
...

### [CTA-MID] （動画中盤・アフィリリンク誘導）
「詳細や最新キャンペーンは概要欄のリンクから確認できます。」
...

### [OUTRO] 最後30秒
（まとめ→高評価・チャンネル登録を自然に促す→次の動画への誘導）

## 💬 ピン留めコメント案
...
"""
    return call_claude(
        prompt,
        model=cfg["llm"]["article_model"],
        max_tokens=6000,
        temperature=0.75,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", default=None)
    ap.add_argument("--length", type=int, default=8, help="動画の長さ（分）")
    ap.add_argument("--from-article", default=None, help="既存記事mdファイルのパス")
    args = ap.parse_args()

    cfg = load_config()
    article_body = ""
    topic = args.keyword or "AIツール活用術"

    if args.from_article:
        with open(args.from_article, encoding="utf-8") as f:
            raw = f.read()
        # remove frontmatter
        article_body = re.sub(r"^---.*?---", "", raw, count=1, flags=re.DOTALL).strip()
        if not args.keyword:
            m = re.search(r'title:\s*"(.+?)"', raw)
            topic = m.group(1) if m else os.path.basename(args.from_article)

    print(f"スクリプト生成中: {topic} ({args.length}分)")
    script = generate_script(topic, args.length, article_body, cfg)

    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    today = datetime.date.today().isoformat()
    out = os.path.join(SCRIPTS_DIR, f"{today}-{slugify(topic)}.md")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {topic} （動画スクリプト）\n\n")
        f.write(script)

    print(f"保存: {out}")


if __name__ == "__main__":
    main()
