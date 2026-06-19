"""Weekly PDCA engine: analyze SNS performance → find winners → generate next week's plan.

Reads:
  - data/sns_tracker.csv    (X投稿の実績)
  - data/keywords.csv       (公開記事一覧)
  - data/trend_*.json       (今週のトレンド分析)

Outputs:
  - data/pdca/YYYY-WNN_report.md  (週次PDCAレポート)
  - data/pdca/YYYY-WNN_plan.csv   (来週のコンテンツカレンダー)

Usage:
    python pdca_engine.py           # 今週のPDCA実行
    python pdca_engine.py --week 24 # 任意の週を指定
"""
import os
import sys
import csv
import json
import glob
import datetime
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm import call_claude
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDCA_DIR = os.path.join(ROOT, "data", "pdca")


def load_config():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def this_week_label():
    now = datetime.date.today()
    return now.strftime("%Y-W%W")


def load_trend_data():
    pattern = os.path.join(ROOT, "data", "trend_*.json")
    files = sorted(glob.glob(pattern))[-7:]  # 直近7日
    trends = []
    for f in files:
        with open(f, encoding="utf-8") as fp:
            try:
                d = json.load(fp)
                trends.append(d.get("brief", {}))
            except Exception:  # noqa: BLE001
                pass
    return trends


def compute_top_performers(tracker_rows):
    """Return top 5 posts by likes+retweets."""
    scored = []
    for r in tracker_rows:
        try:
            score = int(r.get("likes", 0)) + int(r.get("retweets", 0)) * 3
        except ValueError:
            score = 0
        scored.append({**r, "_score": score})
    return sorted(scored, key=lambda x: x["_score"], reverse=True)[:5]


def build_pdca_prompt(week_label, top_posts, published_articles, trend_summaries, cfg):
    niche = cfg["niche"]["primary"]
    top_str = json.dumps(top_posts, ensure_ascii=False, indent=2) if top_posts else "（まだデータなし）"
    articles_str = json.dumps(
        [{"keyword": r.get("keyword"), "status": r.get("status")} for r in published_articles[:30]],
        ensure_ascii=False
    )
    trend_str = json.dumps(trend_summaries[-3:], ensure_ascii=False, indent=2) if trend_summaries else "（なし）"

    return f"""あなたは {niche} に特化した匿名メディアのコンテンツ戦略家です。
週次PDCAレポートを作成してください。

## 今週のパフォーマンスデータ

### X (Twitter) 上位投稿 TOP5（いいね＋RT×3 でスコア化）:
{top_str}

### 公開済み記事一覧（最新30件）:
{articles_str}

### 直近のトレンド分析 (最新3日分):
{trend_str}

## 出力フォーマット（Markdownで）

# PDCAレポート {week_label}

## ✅ PLAN → DO 振り返り
- 今週やろうとしたこと
- 実際にやったこと

## 📊 CHECK: 何がうまくいったか
- バズったコンテンツの共通点（トピック・フォーマット・投稿時間）
- 伸びなかったコンテンツの原因仮説

## 🔁 ACTION: 来週への改善案（具体的に）
- 増やすべき投稿タイプ
- 減らすべき投稿タイプ
- 推すべきアフィリ案件（理由付き）

## 📅 来週コンテンツカレンダー

| 日付 | プラットフォーム | トピック | バズ型 | アフィリ案件 |
|---|---|---|---|---|
| {(datetime.date.today() + datetime.timedelta(days=1)).isoformat()} | X | ... | 箇条書き | ... |
... 7日分 ...

## 🎯 KPI目標（来週）
- X フォロワー目標: +○○人
- ブログ記事: ○○本公開
- アフィリ成約目標: ○○件
"""


def generate_next_plan_csv(report_text, week_label, cfg):
    """Extract the calendar table from report and save as CSV."""
    import re
    rows = []
    # parse simple markdown table rows
    for line in report_text.split("\n"):
        if re.match(r"^\|\s*202", line):
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) >= 4:
                rows.append({
                    "date": cells[0],
                    "platform": cells[1] if len(cells) > 1 else "",
                    "topic": cells[2] if len(cells) > 2 else "",
                    "buzz_type": cells[3] if len(cells) > 3 else "",
                    "affiliate_tag": cells[4] if len(cells) > 4 else "",
                    "status": "pending",
                })
    if not rows:
        return
    out = os.path.join(PDCA_DIR, f"{week_label}_plan.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "platform", "topic", "buzz_type", "affiliate_tag", "status"])
        w.writeheader()
        w.writerows(rows)
    print(f"プラン保存: {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, default=None)
    args = ap.parse_args()

    cfg = load_config()
    os.makedirs(PDCA_DIR, exist_ok=True)

    week_label = this_week_label()
    if args.week:
        year = datetime.date.today().year
        week_label = f"{year}-W{args.week:02d}"

    tracker = read_csv(os.path.join(ROOT, "data", "sns_tracker.csv"))
    articles = read_csv(os.path.join(ROOT, "data", "keywords.csv"))
    trends = load_trend_data()
    top_posts = compute_top_performers(tracker)

    print(f"PDCA生成中: {week_label}")
    prompt = build_pdca_prompt(week_label, top_posts, articles, trends, cfg)
    report = call_claude(
        prompt,
        model=cfg["llm"]["article_model"],
        max_tokens=4000,
        temperature=0.7,
    )

    out = os.path.join(PDCA_DIR, f"{week_label}_report.md")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(report)
    print(f"レポート保存: {out}")
    print("\n" + report[:800] + "\n...")

    generate_next_plan_csv(report, week_label, cfg)


if __name__ == "__main__":
    main()
