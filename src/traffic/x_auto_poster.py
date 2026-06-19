"""X (Twitter) auto-poster with scheduling, queue management, and tracking.

Queue: data/sns_queue.csv  (keyword, hook, thread_body, scheduled_at, status)
Tracker: data/sns_tracker.csv (post_id, posted_at, type, content_preview, likes, retweets, replies)

Optimal post times JST: 9:00, 12:00, 19:00  (configurable)
Rate limit guard: 15 posts/15 min per X API v2 free tier.

Usage:
    python x_auto_poster.py --generate 5     # AI でXスレッドを5本キューに追加
    python x_auto_poster.py --post           # キューから投稿（時間条件チェック）
    python x_auto_poster.py --post --force   # 時間関係なく即投稿
    python x_auto_poster.py --sync-metrics   # 既投稿のいいね/RT を更新
"""
import os
import sys
import csv
import json
import datetime
import argparse
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm import call_claude
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OPTIMAL_HOURS_JST = [9, 12, 19]   # 投稿する時刻（JST）
QUEUE_PATH = os.path.join(ROOT, "data", "sns_queue.csv")
TRACKER_PATH = os.path.join(ROOT, "data", "sns_tracker.csv")

# X投稿バズ型テンプレート（毎日ローテーション）
BUZZ_TEMPLATES = [
    "【知らないと損】{topic}について、使ってみてわかった本音を話す\n\n↓\n{body}",
    "正直に言う。{topic}は{verdict}\n\n理由はこの5つ\n\n{body}",
    "{topic}で月の作業時間が○割減った話をする\n\n{body}",
    "無料で使える{topic}ツール、有料版と比べてみた\n\n{body}",
    "{topic}を1週間使い続けた結果→\n\n{body}",
]


def load_config():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_csv(path, fieldnames):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writeheader()


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def generate_x_threads(topics, cfg, n=5):
    """Generate n X thread posts from topics and add to queue."""
    niche = cfg["niche"]["primary"]
    prompt = f"""あなたはAIツール・SaaS専門の顔出しなしXアカウントの運用者です。
ニッチ: {niche}
禁止: 金融/投資/医療助言・実名・保証表現（「必ず」「確実に」等）

以下のトピックから{n}本のXスレッドを生成してください。
トピック候補: {json.dumps(topics, ensure_ascii=False)}

バズる投稿の型（必ず使う）:
- 1ツイート目: 数字 or 逆説 or 「正直に言う」で始まる強フック（140字以内）
- 2〜5ツイート目: 箇条書き で要点（各140字以内）
- 最後: ブログ誘導「詳しくは→{{BLOG_LINK}}」

出力はJSONのみ:
[
  {{
    "topic": "記事のトピック名",
    "affiliate_tag": "紐づくアフィリ案件名（なければ'なし'）",
    "tweets": ["ツイート1（140字以内）", "ツイート2", "..."]
  }},
  ...
]
"""
    result = _call_json(prompt, cfg)
    if not isinstance(result, list):
        result = []
    now = datetime.datetime.now().isoformat()
    ensure_csv(QUEUE_PATH, ["topic", "affiliate_tag", "tweets_json", "scheduled_at", "status"])
    rows = read_csv(QUEUE_PATH)
    for item in result:
        tweets = item.get("tweets", [])
        rows.append({
            "topic": item.get("topic", ""),
            "affiliate_tag": item.get("affiliate_tag", "なし"),
            "tweets_json": json.dumps(tweets, ensure_ascii=False),
            "scheduled_at": now,
            "status": "pending",
        })
    write_csv(QUEUE_PATH, rows, ["topic", "affiliate_tag", "tweets_json", "scheduled_at", "status"])
    print(f"キューに {len(result)} 件追加")


def _call_json(prompt, cfg):
    from llm import call_llm_json
    return call_llm_json(prompt, model=cfg["llm"]["keyword_model"], max_tokens=3000)


def is_posting_time(force=False):
    if force:
        return True
    now_jst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    return now_jst.hour in OPTIMAL_HOURS_JST


def post_thread(tweets, client):
    """Post a thread via tweepy v2 client. Returns thread root ID."""
    prev_id = None
    for tweet in tweets:
        tweet = tweet.replace("{BLOG_LINK}", "リンクはプロフィールから")
        resp = client.create_tweet(text=tweet[:280], in_reply_to_tweet_id=prev_id)
        prev_id = resp.data["id"]
        time.sleep(1)  # rate limit guard
    return prev_id


def do_post(force=False):
    """Pop one pending item from queue and post."""
    cfg = load_config()
    if not is_posting_time(force):
        now_h = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).hour
        print(f"投稿時刻外（現在{now_h}時JST）。最適: {OPTIMAL_HOURS_JST}。--force で強制投稿。")
        return

    keys = os.getenv("X_API_KEY"), os.getenv("X_API_SECRET"), os.getenv("X_ACCESS_TOKEN"), os.getenv("X_ACCESS_SECRET")
    if not all(keys):
        print("[DRY-RUN] X API キーが未設定。.envに X_* を設定すると実投稿します。")
        _dry_run_post()
        return

    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=keys[0], consumer_secret=keys[1],
            access_token=keys[2], access_token_secret=keys[3]
        )
    except ImportError:
        print("tweepy未インストール: pip install tweepy")
        return

    rows = read_csv(QUEUE_PATH)
    for r in rows:
        if r["status"] != "pending":
            continue
        tweets = json.loads(r.get("tweets_json", "[]"))
        print(f"投稿: {r['topic']} ({len(tweets)}ツイート)")
        try:
            root_id = post_thread(tweets, client)
            r["status"] = "posted"
            # append to tracker
            ensure_csv(TRACKER_PATH, ["post_id", "posted_at", "topic", "affiliate_tag", "likes", "retweets", "replies"])
            t_rows = read_csv(TRACKER_PATH)
            t_rows.append({
                "post_id": str(root_id),
                "posted_at": datetime.datetime.now().isoformat(),
                "topic": r["topic"],
                "affiliate_tag": r["affiliate_tag"],
                "likes": "0", "retweets": "0", "replies": "0",
            })
            write_csv(TRACKER_PATH, t_rows, ["post_id", "posted_at", "topic", "affiliate_tag", "likes", "retweets", "replies"])
        except Exception as e:  # noqa: BLE001
            r["status"] = "error"
            print(f"  エラー: {e}")
        break  # 1回に1スレッドだけ（次の最適時間に次のを投稿）

    write_csv(QUEUE_PATH, rows, ["topic", "affiliate_tag", "tweets_json", "scheduled_at", "status"])


def _dry_run_post():
    rows = read_csv(QUEUE_PATH)
    for r in rows:
        if r["status"] != "pending":
            continue
        tweets = json.loads(r.get("tweets_json", "[]"))
        print(f"\n[DRY-RUN] トピック: {r['topic']}")
        for i, t in enumerate(tweets):
            print(f"  [{i+1}] {t[:80]}...")
        break


def sync_metrics():
    """Update likes/RT from X API for posted items."""
    cfg = load_config()
    keys = os.getenv("X_API_KEY"), os.getenv("X_API_SECRET"), os.getenv("X_ACCESS_TOKEN"), os.getenv("X_ACCESS_SECRET")
    if not all(keys):
        print("[SKIP] X API未設定")
        return
    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=keys[0], consumer_secret=keys[1],
            access_token=keys[2], access_token_secret=keys[3]
        )
    except ImportError:
        return

    rows = read_csv(TRACKER_PATH)
    for r in rows:
        if not r.get("post_id"):
            continue
        try:
            resp = client.get_tweet(r["post_id"], tweet_fields=["public_metrics"])
            m = resp.data.public_metrics
            r["likes"] = str(m["like_count"])
            r["retweets"] = str(m["retweet_count"])
            r["replies"] = str(m["reply_count"])
        except Exception:  # noqa: BLE001
            pass
    write_csv(TRACKER_PATH, rows, ["post_id", "posted_at", "topic", "affiliate_tag", "likes", "retweets", "replies"])
    print("メトリクス更新完了")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate", type=int, metavar="N", help="N件のXスレッドを生成してキューへ")
    ap.add_argument("--post", action="store_true", help="キューから1件投稿")
    ap.add_argument("--force", action="store_true", help="時間関係なく投稿")
    ap.add_argument("--sync-metrics", action="store_true")
    args = ap.parse_args()

    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"), override=True)
    cfg = load_config()

    if args.generate:
        # キーワードCSVからトピックを取得
        kw_path = os.path.join(ROOT, "data", "keywords.csv")
        topics = []
        if os.path.exists(kw_path):
            with open(kw_path, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("status") == "published":
                        topics.append(row.get("keyword", ""))
        if not topics:
            topics = ["ChatGPT 活用術", "Notion AI 使い方", "AI 文字起こしツール", "Claude 使い方", "AI 議事録作成"]
        generate_x_threads(topics[:args.generate * 2], cfg, n=args.generate)
    elif args.post:
        do_post(force=args.force)
    elif args.sync_metrics:
        sync_metrics()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
