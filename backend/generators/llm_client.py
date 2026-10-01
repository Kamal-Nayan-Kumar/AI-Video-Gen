"""Chat completion client.

Two providers are supported behind one interface:

* **Groq** — OpenAI-compatible HTTP API, selected when `GROQ_API_KEY` is set.
* **Gemini** — native SDK, selected when `GEMINI_API_KEY` is set.

Both expose `generate_json(prompt)`, which returns parsed JSON and retries
once if the model wraps its answer in prose or a code fence. Having a single
interface here means the content, script and animation generators do not care
which provider is configured.
"""

import json
import os
import re
from pathlib import Path

import requests

from config import Config

# Groq is fast and free-tier friendly; 120b is the strongest listed model.
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

TIMEOUT = 90


def _strip_fence(text: str) -> str:
    """Pull a JSON object out of a possibly fenced or chatty response."""
    text = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    # Fall back to the outermost braces if there is surrounding prose.
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]
    return text


class LLMError(RuntimeError):
    """Raised when no provider can produce a usable response."""


class LLMClient:
    """Generate JSON from a prompt using whichever provider is configured."""

    def __init__(self):
        self.provider = None
        self._gemini = None

        if Config.GROQ_API_KEY:
            self.provider = "groq"
        elif Config.GEMINI_API_KEY:
            self.provider = "gemini"
            import google.generativeai as genai

            genai.configure(api_key=Config.GEMINI_API_KEY)
            self._gemini = genai.GenerativeModel(
                model_name=Config.GEMINI_MODEL,
                generation_config={"response_mime_type": "application/json"},
            )

    @property
    def available(self) -> bool:
        return self.provider is not None

    # -- providers ------------------------------------------------------
    def _groq(self, prompt: str, as_json: bool = True) -> str:
        body = {
            "model": DEFAULT_GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        # Only some models accept structured output; fall back to plain
        # completion for code generation, which must not be JSON-wrapped.
        if as_json:
            body["response_format"] = {"type": "json_object"}

        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {Config.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=TIMEOUT,
        )
        if response.status_code != 200:
            raise LLMError(f"Groq {response.status_code}: {response.text[:200]}")
        return response.json()["choices"][0]["message"]["content"]

    def _gemini_generate(self, prompt: str) -> str:
        return self._gemini.generate_content(prompt).text

    # -- public ---------------------------------------------------------
    def generate_json(self, prompt: str) -> dict:
        """Run the prompt and return a parsed JSON object."""
        if not self.available:
            raise LLMError("No LLM provider is configured")

        raw = (self._groq(prompt) if self.provider == "groq"
               else self._gemini_generate(prompt))

        try:
            return json.loads(_strip_fence(raw))
        except json.JSONDecodeError:
            # Some models ignore response_format and wrap output in prose.
            strict = (
                "Respond with a single valid JSON object and nothing else. "
                "No explanation, no markdown fence.\n\n" + prompt
            )
            retry_raw = (self._groq(strict) if self.provider == "groq"
                         else self._gemini_generate(strict))
            try:
                return json.loads(_strip_fence(retry_raw))
            except json.JSONDecodeError as exc:
                raise LLMError(f"Provider returned invalid JSON: {raw[:160]}") from exc

    def generate_code(self, prompt: str) -> str:
        """Run the prompt and return raw source text, not JSON.

        Used for Manim scene generation, where the model must emit Python that
        is then rendered and validated rather than parsed.
        """
        if not self.available:
            raise LLMError("No LLM provider is configured")

        raw = (self._groq(prompt, as_json=False) if self.provider == "groq"
               else self._gemini_generate(prompt))

        # Strip any markdown fence the model may still wrap the code in.
        fence = re.match(r"^```(?:python)?\s*(.*?)\s*```$", raw.strip(), re.DOTALL)
        return fence.group(1).strip() if fence else raw.strip()

    @staticmethod
    def guide_text(limit: int = 6000) -> str:
        """Read the Manim guidelines file, if present, for scene generation."""
        guide = Path(__file__).resolve().parent.parent / "MANIM_CODE_GUIDE.md"
        if guide.is_file():
            return guide.read_text(encoding="utf-8")[:limit]
        return "Follow standard Manim Community Edition syntax."