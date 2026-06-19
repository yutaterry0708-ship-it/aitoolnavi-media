"""VOICEVOX TTS: YouTube script -> WAV audio file.

Reads the [HOOK]/[INTRO]/[MAIN-*]/[CTA-MID]/[OUTRO] sections from a
youtube_script.py output file and generates audio via VOICEVOX local API.

Requirements:
  - VOICEVOX must be running (http://127.0.0.1:50021)
  - pip install requests (already in requirements.txt)

Usage:
    python voicevox_tts.py --script data/youtube_scripts/2026-06-19-chatgpt.md
    python voicevox_tts.py --script data/youtube_scripts/2026-06-19-chatgpt.md --speaker 11
    python voicevox_tts.py --list-speakers

Speaker recommendations:
    11  = 玄野武宏 ノーマル  (落ち着いた男声・解説向き)
    30  = No.7 アナウンス    (アナウンサー調・聞き取りやすい)
    13  = 青山龍星 ノーマル  (ナレーション向き)
     2  = 四国めたん ノーマル (女声・明るい)
"""
import os
import re
import sys
import json
import struct
import argparse
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VOICEVOX_URL = "http://127.0.0.1:50021"
DEFAULT_SPEAKER = 11  # 玄野武宏 ノーマル
AUDIO_DIR = os.path.join(ROOT, "data", "youtube_audio")


def check_server():
    try:
        r = requests.get(f"{VOICEVOX_URL}/version", timeout=3)
        return r.ok
    except Exception:
        return False


def list_speakers():
    r = requests.get(f"{VOICEVOX_URL}/speakers", timeout=5)
    for sp in r.json():
        for style in sp["styles"]:
            print(f"  ID {style['id']:3d}: {sp['name']} ({style['name']})")


def text_to_wav_bytes(text, speaker_id):
    """Convert a single text chunk to WAV bytes via VOICEVOX."""
    # Step 1: audio_query
    r = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params={"text": text, "speaker": speaker_id},
        timeout=30,
    )
    r.raise_for_status()
    query = r.json()
    query["outputSamplingRate"] = 44100
    query["outputStereo"] = False

    # Step 2: synthesis
    r2 = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={"speaker": speaker_id},
        headers={"Content-Type": "application/json"},
        data=json.dumps(query),
        timeout=60,
    )
    r2.raise_for_status()
    return r2.content  # raw WAV bytes


def silence_wav(seconds, sample_rate=44100):
    """Generate silent WAV chunk (for pause markers)."""
    num_samples = int(sample_rate * seconds)
    data = b"\x00\x00" * num_samples
    # Build minimal WAV header
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(data)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16, 1, num_channels, sample_rate,
        byte_rate, block_align, bits_per_sample,
        b"data", data_size,
    )
    return header + data


def merge_wavs(wav_list):
    """Merge list of WAV byte strings into one WAV (same format assumed)."""
    if not wav_list:
        return b""
    # Extract data chunks from each WAV
    combined_data = b""
    sample_rate = 44100
    for wav in wav_list:
        # skip 44-byte header, take data
        if len(wav) > 44:
            combined_data += wav[44:]
    # Rebuild header
    data_size = len(combined_data)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16, 1, 1, sample_rate,
        sample_rate * 2, 2, 16,
        b"data", data_size,
    )
    return header + combined_data


def extract_script_text(md_path):
    """Extract only the narration text from 台本 sections."""
    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    # Find everything under ## 📜 台本
    m = re.search(r"## 📜 台本(.*?)(?=^## |\Z)", content, re.DOTALL | re.MULTILINE)
    if not m:
        # Fallback: use whole file
        script_body = content
    else:
        script_body = m.group(1)

    # Remove markdown headers (### [...])
    script_body = re.sub(r"^#{1,4} .*$", "", script_body, flags=re.MULTILINE)

    # Remove code blocks
    script_body = re.sub(r"```.*?```", "", script_body, flags=re.DOTALL)

    # Process pause markers: {pause:1.5} or {{pause:1.0}}
    # We'll tag them as special tokens
    script_body = re.sub(r"\{+pause:(\d+\.?\d*)\}+", r"[PAUSE:\1]", script_body)

    # Remove remaining markdown (bold, italic, links)
    script_body = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", script_body)
    script_body = re.sub(r"`[^`]+`", "", script_body)
    script_body = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", script_body)

    # Split into chunks: text lines and pause markers
    chunks = []
    for line in script_body.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Split by [PAUSE:x] within a line
        parts = re.split(r"(\[PAUSE:\d+\.?\d*\])", line)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            pm = re.match(r"\[PAUSE:(\d+\.?\d*)\]", part)
            if pm:
                chunks.append(("pause", float(pm.group(1))))
            elif len(part) > 1:
                chunks.append(("text", part))

    return chunks


def generate_audio(md_path, speaker_id, out_path=None):
    chunks = extract_script_text(md_path)
    if not chunks:
        print("No script text found.")
        return

    text_count = sum(1 for t, _ in chunks if t == "text")
    print(f"Chunks: {len(chunks)} ({text_count} text + {len(chunks)-text_count} pauses)")

    wav_parts = []
    for i, (kind, val) in enumerate(chunks):
        if kind == "pause":
            print(f"  [{i+1}/{len(chunks)}] pause {val}s")
            wav_parts.append(silence_wav(val))
        else:
            text_preview = val[:30] + ("..." if len(val) > 30 else "")
            print(f"  [{i+1}/{len(chunks)}] TTS: {text_preview}")
            try:
                wav_bytes = text_to_wav_bytes(val, speaker_id)
                wav_parts.append(wav_bytes)
            except Exception as e:
                print(f"    WARN: skip ({e})")

    merged = merge_wavs(wav_parts)
    if not merged:
        print("No audio generated.")
        return

    os.makedirs(AUDIO_DIR, exist_ok=True)
    if out_path is None:
        base = os.path.splitext(os.path.basename(md_path))[0]
        out_path = os.path.join(AUDIO_DIR, f"{base}_speaker{speaker_id}.wav")

    with open(out_path, "wb") as f:
        f.write(merged)

    size_mb = len(merged) / 1024 / 1024
    print(f"\nSaved: {out_path} ({size_mb:.1f} MB)")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", help="YouTubeスクリプトの.mdファイルパス")
    ap.add_argument("--speaker", type=int, default=DEFAULT_SPEAKER,
                    help=f"VOICEVOXのスピーカーID (default: {DEFAULT_SPEAKER}=玄野武宏)")
    ap.add_argument("--list-speakers", action="store_true", help="利用可能な声一覧を表示")
    ap.add_argument("--out", default=None, help="出力WAVのパス（省略時は自動命名）")
    args = ap.parse_args()

    if not check_server():
        print("ERROR: VOICEVOXが起動していません。")
        print(f"  起動: {AUDIO_DIR}")
        print("  C:\\Users\\yutat\\AppData\\Local\\Programs\\VOICEVOX\\VOICEVOX.exe を起動してから再実行してください。")
        sys.exit(1)

    if args.list_speakers:
        list_speakers()
        return

    if not args.script:
        # 最新スクリプトを自動選択
        scripts = sorted(
            [f for f in os.listdir(os.path.join(ROOT, "data", "youtube_scripts"))
             if f.endswith(".md")],
            reverse=True
        )
        if not scripts:
            print("スクリプトが見つかりません。youtube_script.py を先に実行してください。")
            sys.exit(1)
        md_path = os.path.join(ROOT, "data", "youtube_scripts", scripts[0])
        print(f"最新スクリプト: {scripts[0]}")
    else:
        md_path = args.script
        if not os.path.isabs(md_path):
            md_path = os.path.join(ROOT, md_path)

    generate_audio(md_path, args.speaker, args.out)


if __name__ == "__main__":
    main()
