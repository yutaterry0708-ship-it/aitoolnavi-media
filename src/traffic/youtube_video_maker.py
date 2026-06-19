"""YouTube Video Maker: WAV audio + YT script -> MP4 slideshow video.

Automatically creates a YouTube-ready video from:
  - VOICEVOX-generated WAV audio (data/youtube_audio/*.wav)
  - YouTube script markdown (data/youtube_scripts/*.md)

Output: data/youtube_videos/YYYY-MM-DD-slug.mp4

Requirements:
    pip install moviepy pillow

Usage:
    python youtube_video_maker.py                    # auto-pick latest
    python youtube_video_maker.py --script <path>    # specific script
    python youtube_video_maker.py --audio <path>     # specific audio
"""
import os
import re
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = ROOT / "data" / "youtube_scripts"
AUDIO_DIR = ROOT / "data" / "youtube_audio"
VIDEO_DIR = ROOT / "data" / "youtube_videos"

# Video settings
WIDTH, HEIGHT = 1920, 1080
FPS = 24
BG_COLOR = (15, 23, 42)        # dark navy
ACCENT_COLOR = (99, 102, 241)  # indigo
TEXT_COLOR = (248, 250, 252)   # white
SUB_COLOR = (148, 163, 184)    # gray

FONT_PATH = None  # auto-detect
CJK_FONTS = [
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/yugothib.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
    "C:/Windows/Fonts/NotoSansCJKjp-Regular.otf",
]


def find_font(size=48):
    from PIL import ImageFont
    for fp in CJK_FONTS:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width pixels."""
    words = list(text)  # character-level for Japanese
    lines = []
    current = ""
    for ch in words:
        test = current + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def make_slide(title, body_lines, slide_num, total_slides, brand="AIツールナビ"):
    """Create a single slide image (numpy array for moviepy)."""
    import numpy as np
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Background gradient effect (simple stripes)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_COLOR[0] + (30 - BG_COLOR[0]) * ratio * 0.3)
        g = int(BG_COLOR[1] + (35 - BG_COLOR[1]) * ratio * 0.3)
        b = int(BG_COLOR[2] + (60 - BG_COLOR[2]) * ratio * 0.3)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # Accent bar (left side)
    draw.rectangle([(0, 0), (8, HEIGHT)], fill=ACCENT_COLOR)

    # Brand name (top right)
    font_brand = find_font(28)
    draw.text((WIDTH - 220, 30), brand, font=font_brand, fill=SUB_COLOR)

    # Slide counter (top left)
    draw.text((30, 30), f"{slide_num}/{total_slides}", font=font_brand, fill=SUB_COLOR)

    # Title
    font_title = find_font(56)
    title_y = 140
    title_lines = []
    temp_draw = draw
    title_lines = wrap_text(title, font_title, WIDTH - 120, temp_draw)
    for i, line in enumerate(title_lines[:3]):
        draw.text((60, title_y + i * 75), line, font=font_title, fill=TEXT_COLOR)

    # Divider line
    body_start_y = title_y + min(len(title_lines), 3) * 75 + 40
    draw.rectangle([(60, body_start_y), (WIDTH - 60, body_start_y + 3)], fill=ACCENT_COLOR)

    # Body text
    font_body = find_font(38)
    body_y = body_start_y + 30
    for line in body_lines[:12]:
        if body_y > HEIGHT - 120:
            break
        # Bullet point styling
        if line.startswith("・") or line.startswith("•") or line.startswith("-"):
            draw.text((60, body_y), "▶", font=find_font(28), fill=ACCENT_COLOR)
            draw.text((100, body_y), line.lstrip("・•- "), font=font_body, fill=TEXT_COLOR)
        else:
            draw.text((60, body_y), line, font=font_body, fill=TEXT_COLOR)
        bbox = draw.textbbox((0, 0), line or " ", font=font_body)
        body_y += (bbox[3] - bbox[1]) + 14

    # Bottom bar
    draw.rectangle([(0, HEIGHT - 60), (WIDTH, HEIGHT)], fill=(20, 30, 55))
    font_sub = find_font(24)
    draw.text((60, HEIGHT - 45), "AIツールナビ | aitoolnavi.com | チャンネル登録よろしく！", font=font_sub, fill=SUB_COLOR)

    return np.array(img)


def extract_slides_from_script(md_path: Path) -> list:
    """Extract slide content from YouTube script markdown."""
    text = md_path.read_text(encoding="utf-8")

    # Get title
    h1 = re.search(r"^# (.+)$", text, re.MULTILINE)
    main_title = h1.group(1).strip() if h1 else md_path.stem

    # Extract sections: HOOK, INTRO, MAIN-*, CTA, OUTRO
    sections = re.findall(
        r"###\s*\[([^\]]+)\]\s*(.+?)(?=###\s*\[|\Z)",
        text, re.DOTALL
    )

    slides = []

    # Title slide
    slides.append({
        "title": main_title,
        "body": ["チャンネル登録 & 高評価をお願いします！", "", "今日のテーマ：", main_title]
    })

    for tag, content in sections:
        tag = tag.strip()
        content = content.strip()

        # Remove markdown formatting
        content = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", content)
        content = re.sub(r"`(.+?)`", r"\1", content)
        content = re.sub(r"\{+pause:\d+\.?\d*\}+", "", content)
        content = re.sub(r"^#{1,4} .+$", "", content, flags=re.MULTILINE)

        lines = [l.strip() for l in content.split("\n") if l.strip() and len(l.strip()) > 2]

        if not lines:
            continue

        # Create slide title from tag
        tag_titles = {
            "HOOK": "今日のポイント",
            "INTRO": "はじめに",
            "OUTRO": "まとめ・チャンネル登録",
            "CTA-MID": "関連情報",
        }
        slide_title = tag_titles.get(tag, tag.replace("MAIN-", "").replace("-", " "))

        # Split long sections into multiple slides (max 10 lines each)
        chunk_size = 10
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i + chunk_size]
            suffix = f" ({i//chunk_size + 1})" if len(lines) > chunk_size else ""
            slides.append({"title": slide_title + suffix, "body": chunk})

    # End slide
    slides.append({
        "title": "ご視聴ありがとうございました！",
        "body": [
            "チャンネル登録 & 高評価よろしくお願いします",
            "",
            "▶ aitoolnavi.com でより詳しい記事を公開中",
            "▶ 次の動画もお楽しみに！",
        ]
    })

    return slides


def make_video(script_path: Path, audio_path: Path, out_path: Path = None):
    """Generate MP4 video from script + audio."""
    try:
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips
    except ImportError:
        from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips

    print(f"スクリプト: {script_path.name}")
    print(f"音声: {audio_path.name}")

    # Load audio
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration
    print(f"音声長: {duration:.1f}秒 ({duration/60:.1f}分)")

    # Extract slides
    slides = extract_slides_from_script(script_path)
    n_slides = len(slides)
    slide_duration = duration / n_slides
    print(f"スライド数: {n_slides} (各{slide_duration:.1f}秒)")

    # Generate slide clips
    clips = []
    for i, slide in enumerate(slides):
        print(f"  スライド {i+1}/{n_slides}: {slide['title'][:30]}")
        frame = make_slide(slide["title"], slide["body"], i + 1, n_slides)
        clip = ImageClip(frame, duration=slide_duration).with_fps(FPS)
        clips.append(clip)

    # Concatenate and add audio
    video = concatenate_videoclips(clips, method="compose")
    video = video.with_audio(audio)

    # Output path
    if out_path is None:
        VIDEO_DIR.mkdir(exist_ok=True)
        stem = script_path.stem
        out_path = VIDEO_DIR / f"{stem}.mp4"

    print(f"書き出し中: {out_path}")
    video.write_videofile(
        str(out_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        logger=None,
    )
    print(f"完成: {out_path} ({out_path.stat().st_size/1024/1024:.1f}MB)")
    return out_path


def auto_pair() -> tuple:
    """Auto-pair latest script with matching audio."""
    scripts = sorted(SCRIPTS_DIR.glob("*.md"), reverse=True)
    if not scripts:
        return None, None

    for script in scripts:
        stem = script.stem
        # Look for matching audio
        matching = list(AUDIO_DIR.glob(f"{stem}*.wav"))
        if matching:
            return script, matching[0]

    # If no match, return latest script and latest audio
    audios = sorted(AUDIO_DIR.glob("*.wav"), reverse=True)
    if scripts and audios:
        return scripts[0], audios[0]
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", help="YouTubeスクリプト.mdパス")
    ap.add_argument("--audio", help="WAV音声ファイルパス")
    ap.add_argument("--out", help="出力MP4パス")
    args = ap.parse_args()

    if args.script:
        script_path = Path(args.script)
    else:
        script_path, auto_audio = auto_pair()
        if not script_path:
            print("スクリプトが見つかりません")
            sys.exit(1)
        if not args.audio:
            args.audio = str(auto_audio) if auto_audio else None

    if args.audio:
        audio_path = Path(args.audio)
    else:
        # Find matching audio
        audios = sorted(AUDIO_DIR.glob("*.wav"), reverse=True)
        if not audios:
            print("WAV音声ファイルが見つかりません。先に voicevox_tts.py を実行してください")
            sys.exit(1)
        audio_path = audios[0]

    out_path = Path(args.out) if args.out else None
    make_video(script_path, audio_path, out_path)


if __name__ == "__main__":
    main()
