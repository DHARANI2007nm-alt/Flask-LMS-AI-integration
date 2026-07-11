"""
ai.py
-----
Thin wrapper around any OpenAI-compatible Chat Completions endpoint.

Two capabilities:
  1. tutor_reply(course, question, history)  -> str
  2. generate_quiz(topic, n, difficulty)     -> list[dict]

If OPENAI_API_KEY is not set, functions raise `AIUnavailable`, which routes
catch and turn into a friendly flash message.
"""
from __future__ import annotations
import json
import re
from typing import Iterable
import requests
from flask import current_app


class AIUnavailable(RuntimeError):
    """Raised when the AI provider is not configured or returns an error."""


def _config():
    key = current_app.config.get("OPENAI_API_KEY", "")
    if not key:
        raise AIUnavailable(
            "AI is not configured. Set OPENAI_API_KEY (and optionally "
            "OPENAI_BASE_URL / OPENAI_MODEL) as environment variables."
        )
    return {
        "key": key,
        "base": current_app.config["OPENAI_BASE_URL"].rstrip("/"),
        "model": current_app.config["OPENAI_MODEL"],
    }


def _chat(messages: list[dict], *, temperature: float = 0.4,
          response_format: dict | None = None, timeout: int = 60) -> str:
    cfg = _config()
    payload: dict = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature,
    }
    if response_format:
        payload["response_format"] = response_format
    try:
        r = requests.post(
            f"{cfg['base']}/chat/completions",
            headers={
                "Authorization": f"Bearer {cfg['key'].strip()}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as e:
        raise AIUnavailable(f"Network error contacting AI provider: {e}") from e

    if r.status_code == 401:
        raise AIUnavailable("AI provider rejected the API key (401).")
    if r.status_code == 402:
        raise AIUnavailable("AI credits exhausted (402). Please top up your account.")
    if r.status_code == 429:
        raise AIUnavailable("AI rate limit hit (429). Try again in a moment.")
    if r.status_code >= 400:
        raise AIUnavailable(f"AI provider error {r.status_code}: {r.text[:200]}")

    data = r.json()
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError) as e:
        raise AIUnavailable(f"Unexpected AI response shape: {data}") from e


# ---------- AI Tutor ----------

def tutor_reply(course_title: str, course_description: str,
                question: str, history: Iterable[dict] = ()) -> str:
    """
    Answer a student's question, grounded in the course they're taking.
    `history` is an iterable of {"role": "user"|"assistant", "content": str}.
    """
    system = (
        "You are a friendly, patient tutor for an online learning platform. "
        f"The student is enrolled in the course: '{course_title}'.\n"
        f"Course description: {course_description or '(none provided)'}\n"
        "Rules:\n"
        "- Explain concepts clearly, use short paragraphs and examples.\n"
        "- If the student asks something off-topic, gently steer them back.\n"
        "- Never claim to be a human; you are an AI tutor.\n"
        "- Prefer Markdown formatting (headings, lists, code blocks)."
    )
    messages = [{"role": "system", "content": system}]
    messages.extend(list(history)[-10:])  # last 10 turns for context
    messages.append({"role": "user", "content": question})
    return _chat(messages, temperature=0.5)


# ---------- AI Quiz Generation ----------

_QUIZ_SCHEMA_HINT = (
    'Return ONLY valid JSON of the form:\n'
    '{"questions":[{"text":"...","options":["A","B","C","D"],"correct_index":0}, ...]}\n'
    'where correct_index is 0..3 (index into options). No prose, no code fences.'
)


def _extract_json(raw: str) -> dict:
    """Be tolerant of models that wrap JSON in ```json fences or extra prose."""
    raw = raw.strip()
    # strip fenced code block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.S)
    if m:
        raw = m.group(1)
    # fallback: first { ... last }
    if not raw.startswith("{"):
        i, j = raw.find("{"), raw.rfind("}")
        if i != -1 and j != -1 and j > i:
            raw = raw[i : j + 1]
    return json.loads(raw)


def generate_quiz(topic: str, num_questions: int = 5,
                  difficulty: str = "medium") -> list[dict]:
    """
    Returns a list of dicts: [{text, option_a, option_b, option_c, option_d, correct_index}]
    """
    num_questions = max(1, min(15, int(num_questions)))
    system = (
        "You are an expert quiz author. Produce multiple-choice questions with exactly "
        "4 options and exactly one correct answer. Keep questions unambiguous and factual."
    )
    user = (
        f"Topic: {topic}\n"
        f"Number of questions: {num_questions}\n"
        f"Difficulty: {difficulty}\n\n"
        + _QUIZ_SCHEMA_HINT
    )
    raw = _chat(
        [{"role": "system", "content": system},
         {"role": "user", "content": user}],
        temperature=0.6,
        response_format={"type": "json_object"},
    )
    try:
        obj = _extract_json(raw)
        items = obj["questions"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise AIUnavailable(f"AI returned invalid JSON: {e}") from e

    out: list[dict] = []
    for q in items[:num_questions]:
        opts = q.get("options") or []
        if len(opts) != 4:
            continue
        try:
            ci = int(q.get("correct_index", 0))
        except (TypeError, ValueError):
            ci = 0
        ci = max(0, min(3, ci))
        text = (q.get("text") or "").strip()
        if not text:
            continue
        out.append({
            "text": text,
            "option_a": str(opts[0])[:300],
            "option_b": str(opts[1])[:300],
            "option_c": str(opts[2])[:300],
            "option_d": str(opts[3])[:300],
            "correct_index": ci,
        })
    if not out:
        raise AIUnavailable("AI did not return any usable questions.")
    return out
