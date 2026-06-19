"""Generate Instagram Reels scripts + carousel slide copy (faceless, text-based).

Reels: 7-15 seconds, text overlay on AI-generated background image.
Carousel: 4-8 slides with bold single-point text per slide.
Outputs to data/instagram/.

Usage:
    python instagram_reel.py --topic "Notion AIの3つの使い方" --type reel
    python instagram_reel.py --topic "ChatGPT vs Claude 比較" --type carousel
    python instagram_reel.py --topic "..." --type both
"""
import os
import sys
import json
import datetime
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm import call_llm_json
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IG_DIR = os.path.join(ROOT, "data", "instagram")


def load_config():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_reel(topic, cfg):
    schema_str = json.dumps({
        "hook_text": "画面に出る最初のテキスト（7文字以内・インパクト重視）",
        "body_texts": ["テキスト2（7〜12秒に表示）", "..."],
        "cta_text": "最後のテキスト（プロフリンク誘導）",
        "background_prompt_en": "Stable Diffusion/DALL-Eへの背景プロンプト（英語）",
        "caption": "投稿キャプション（日本語・200字以内）",
        "hashtags": ["#AIツール", "...（30個以内）"],
        "music_vibe": "BGM雰囲気（例: lo-fi/upbeat/calm）"
    }, ensure_ascii=False)

    prompt = f"""Instagram Reels（7〜15秒・顔出しなし・テキスト主体）を設計してください。
テーマ: {topic}
ニッチ: AIツール・SaaS（非金融・非医療）
禁止: 保証表現・実名・顔出し

2026年のInstagram攻略のコツ:
- 最初の2秒で視聴者を止める（文字は大きく・短く）
- 7〜15秒に収める（アルゴリズム優遇）
- テキストオーバーレイはシンプルに（1フレーム1メッセージ）
- CTAは「プロフィールのリンクから詳しく」が定番

以下のJSONだけ返す（説明なし）:
{schema_str}
"""
    return call_llm_json(prompt, model=cfg["llm"]["keyword_model"], max_tokens=1000)


def generate_carousel(topic, cfg):
    prompt = f"""Instagram カルーセル（4〜8枚）を設計してください。
テーマ: {topic}
ニッチ: AIツール・SaaS（非金融・非医療）
禁止: 保証表現・実名

カルーセルの鉄則:
- 1枚目: 「○○知ってる？」「実は○○できる」系フック
- 2〜N枚目: 1枚1ポイント（箇条書きNG・1スライド1文）
- 最終枚: まとめ + 保存してね + プロフリンク誘導

以下のJSONのみ返す:
{{
  "slides": [
    {{"slide_no": 1, "headline": "1枚目のメインテキスト", "subtext": "補足（あれば）"}},
    ...
  ],
  "caption": "投稿キャプション（200字・CTA含む）",
  "hashtags": ["...", "...（30個以内）"],
  "background_color": "#16213e",
  "text_color": "#ffffff",
  "accent_color": "#0f3460"
}}
"""
    return call_llm_json(prompt, model=cfg["llm"]["keyword_model"], max_tokens=1200)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--type", choices=["reel", "carousel", "both"], default="both")
    args = ap.parse_args()

    cfg = load_config()
    os.makedirs(IG_DIR, exist_ok=True)
    today = datetime.date.today().isoformat()
    slug = args.topic[:30].replace(" ", "_")
    result = {}

    if args.type in ("reel", "both"):
        print("Reels生成中...")
        r = generate_reel(args.topic, cfg)
        result["reel"] = r
        print(json.dumps(r, ensure_ascii=False, indent=2))

    if args.type in ("carousel", "both"):
        print("カルーセル生成中...")
        c = generate_carousel(args.topic, cfg)
        result["carousel"] = c
        print(json.dumps(c, ensure_ascii=False, indent=2))

    out = os.path.join(IG_DIR, f"{today}-{slug}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n保存: {out}")


if __name__ == "__main__":
    main()
