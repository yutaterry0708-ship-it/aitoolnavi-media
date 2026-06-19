"""Turn an article into a faceless X (Twitter) thread for traffic.

Dry-run by default; pass --post to actually publish (needs X_* env vars + tweepy).

Usage:
    python sns_repurpose.py --file ../content/2026-06-19-notion-ai.md
    python sns_repurpose.py --file ../content/...md --post
"""
import os
import re
import argparse

import yaml

from llm import call_claude

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def article_to_thread(markdown, cfg):
    body = re.sub(r"^---.*?---", "", markdown, count=1, flags=re.DOTALL).strip()
    prompt = f"""次の記事を、顔出しなしのX(旧Twitter)で伸びるスレッドに再構成してください。
- 1ツイート目=強いフック(数字/逆説/具体)。140字以内。
- 以降3〜5ツイートで要点。各140字以内。
- 最後にブログ誘導の一文(リンクは {{LINK}} と書く)。
- 絵文字は控えめ、煽りすぎない。PR要素は正直に(ステマNG)。
- 出力は各ツイートを "---" 区切りのプレーンテキストのみ。

記事:
{body[:6000]}"""
    return call_claude(prompt, model=cfg["llm"]["keyword_model"], max_tokens=1500, temperature=0.8)


def post_to_x(tweets):
    """Post a thread via X API v2. Off by default."""
    import tweepy

    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_SECRET"),
    )
    prev = None
    for t in tweets:
        resp = client.create_tweet(text=t, in_reply_to_tweet_id=prev)
        prev = resp.data["id"]
    return prev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--post", action="store_true", help="actually post (default: dry-run)")
    args = ap.parse_args()

    cfg = load_config()
    with open(args.file, encoding="utf-8") as f:
        md = f.read()
    thread = article_to_thread(md, cfg)
    tweets = [t.strip() for t in thread.split("---") if t.strip()]
    print("\n\n".join(f"[{i + 1}] {t}" for i, t in enumerate(tweets)))

    if args.post:
        post_to_x(tweets)
        print("\nPosted to X.")
    else:
        print("\n(dry-run: --post を付けると実投稿)")


if __name__ == "__main__":
    main()
