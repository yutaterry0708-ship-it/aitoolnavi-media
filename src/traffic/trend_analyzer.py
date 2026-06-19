"""Daily trend analysis: RSS feeds → Claude → content ideas + buzz patterns.

Pulls from Japanese/English tech RSS → extracts AI/SaaS trends → outputs daily brief.
No human needed; designed for Task Scheduler (fully headless).

Usage:
    python trend_analyzer.py             # print brief
    python trend_analyzer.py --save      # save to data/trend_YYYYMMDD.json
"""
import os
import sys
import json
import datetime
import argparse

# feedparser may not be installed yet; skip gracefully
try:
    import feedparser
    _HAS_FEEDPARSER = True
except ImportError:
    _HAS_FEEDPARSER = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm import call_claude, call_llm_json
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RSS_FEEDS = [
    # Japanese tech news
    "https://gigazine.net/news/rss_2.0/",
    "https://japan.cnet.com/rss/index.rdf",
    "https://www.itmedia.co.jp/rss/xml/aiplus/rss20.xml",
    # English AI/SaaS
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://openai.com/blog/rss.xml",
]

BUZZ_PATTERNS = [
    "知らないと損する○○",
    "○○が○日で○○になった結果",
    "AIで○○を完全自動化した話",
    "無料で使える○○ツール5選",
    "○○の代わりになるAIツール比較",
    "プロが使ってる○○ツールをこっそり教える",
    "○○秒でできる AI活用術",
    "○○のコスパ最強AIツール",
]


def load_config():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_rss_headlines(max_per_feed=5):
    if not _HAS_FEEDPARSER:
        return []
    headlines = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                headlines.append(entry.get("title", ""))
        except Exception:  # noqa: BLE001
            continue
    return [h for h in headlines if h]


def analyze_trends(headlines, cfg):
    niche = cfg["niche"]["primary"]
    headlines_text = "\n".join(f"- {h}" for h in headlines) if headlines else "(RSS取得不可)"
    schema = {
        "type": "object",
        "properties": {
            "top_topics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "今日バズる可能性が高いAIツール・SaaSトピック TOP5"
            },
            "x_post_ideas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "hook": {"type": "string", "description": "140字以内の冒頭ツイート（バズ型）"},
                        "type": {"type": "string", "enum": ["箇条書き", "逆説", "数字", "比較", "問いかけ"]},
                        "affiliate_angle": {"type": "string"}
                    }
                },
                "description": "今日投稿するXツイートアイデア5案"
            },
            "youtube_idea": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "サムネ/タイトル"},
                    "hook_15sec": {"type": "string", "description": "最初15秒の台本"},
                    "keyword": {"type": "string"}
                }
            },
            "instagram_reel_idea": {
                "type": "object",
                "properties": {
                    "text_overlay": {"type": "string", "description": "7〜15秒で使う文字テロップ"},
                    "hashtags": {"type": "array", "items": {"type": "string"}}
                }
            },
            "blog_article_idea": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "title": {"type": "string"},
                    "affiliate_tag": {"type": "string"}
                }
            }
        }
    }

    prompt = f"""あなたはAIツール・SaaS専門の匿名メディアのコンテンツ戦略家です。
ニッチ: {niche}
バズ型パターン: {", ".join(BUZZ_PATTERNS[:4])}

今日のテックニュース見出し（RSS）:
{headlines_text}

これらを踏まえて「今日投稿すべきコンテンツ」を全プラットフォーム分まとめてください。
- 禁止: 金融・投資・医療助言。実名・顔出し不要。
- Xのフックは箇条書き/数字/逆説を使うと伸びる。
- YouTubeは最初15秒が勝負（視聴継続率を上げる）。
- Instagramは7〜15秒のテキスト主体リール。

以下のJSONのみを返す（前置き不要）:
```json
{json.dumps(schema, ensure_ascii=False, indent=2)}
```
"""
    return call_llm_json(prompt, model=cfg["llm"]["keyword_model"], max_tokens=2000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    headlines = fetch_rss_headlines()
    brief = analyze_trends(headlines, cfg)

    today = datetime.date.today().isoformat()
    print(f"\n===== トレンド分析 {today} =====")
    print(json.dumps(brief, ensure_ascii=False, indent=2))

    if args.save:
        out = os.path.join(ROOT, "data", f"trend_{today}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"date": today, "brief": brief}, f, ensure_ascii=False, indent=2)
        print(f"\n保存: {out}")

    return brief


if __name__ == "__main__":
    main()
