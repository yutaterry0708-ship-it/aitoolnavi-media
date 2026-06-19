"""Shared LLM client: Claude (primary) + Gemini (fallback), with retries.

Run scripts from this src/ directory so `import llm` resolves.
"""
import os
import json
import time
import re

from dotenv import load_dotenv

# override empty system env vars (see global CLAUDE.md note)
load_dotenv(override=True)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            override=True)

_ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
_GEMINI_KEY = os.getenv("GEMINI_API_KEY")


def call_claude(prompt, model="claude-sonnet-4-6", system=None,
                max_tokens=4096, temperature=0.7, retries=3):
    """Call the Anthropic API with exponential-backoff retries."""
    from anthropic import Anthropic

    if not _ANTHROPIC_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set (.env)")
    client = Anthropic(api_key=_ANTHROPIC_KEY)
    last_err = None
    for attempt in range(retries):
        try:
            kwargs = dict(model=model, max_tokens=max_tokens, temperature=temperature,
                          messages=[{"role": "user", "content": prompt}])
            if system:
                kwargs["system"] = system
            resp = client.messages.create(**kwargs)
            return "".join(b.text for b in resp.content
                           if getattr(b, "type", "") == "text").strip()
        except Exception as e:  # noqa: BLE001 - retry any transient API error
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Claude call failed after {retries} tries: {last_err}")


def call_gemini(prompt, model="gemini-2.5-flash", retries=3):
    """Fallback generator. Current model names: gemini-2.5-pro / gemini-2.5-flash."""
    import google.generativeai as genai

    if not _GEMINI_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set (.env)")
    genai.configure(api_key=_GEMINI_KEY)
    m = genai.GenerativeModel(model)
    last_err = None
    for attempt in range(retries):
        try:
            return (m.generate_content(prompt).text or "").strip()
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Gemini call failed after {retries} tries: {last_err}")


def call_llm_json(prompt, model="claude-sonnet-4-6", retries=3, **kw):
    """Call an LLM and parse JSON, retrying if the first response is prose."""
    last = None
    for _ in range(retries):
        raw = call_claude(prompt, model=model, **kw)
        data = _extract_json(raw)
        if data is not None:
            return data
        last = raw
    raise ValueError(f"Could not parse JSON after {retries} tries. Last: {str(last)[:300]}")


def _extract_json(text):
    text = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    for opener, closer in (("[", "]"), ("{", "}")):
        s, e = text.find(opener), text.rfind(closer)
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(text[s:e + 1])
            except json.JSONDecodeError:
                continue
    return None
