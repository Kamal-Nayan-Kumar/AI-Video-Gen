"""Chat completion client.

Multiple providers are supported behind one interface, tried in order:

1. **Groq** — OpenAI-compatible HTTP API, fastest.
2. **OpenRouter** — OpenAI-compatible, a broad multi-provider fallback.
3. **Gemini** — native SDK, last resort before local generation.

Each provider exposes `generate_json(prompt)` and `generate_code(prompt)`.
`generate_json` returns parsed JSON and retries once if the model wraps its
answer in prose or a code fence. Having a single interface here means the
content, script and animation generators never care which provider answered,
and a provider that rate-limits or errors falls through to the next one
rather than failing the whole generation.

Note on OpenRouter "free" models: OpenRouter has no model literally called
`openrouter/free`. Free models carry a `:free` suffix and share a very low
daily request cap (50/day on a free-tier key), so they are unreliable as an
automatic fallback. The default here is a cheap paid model; override with
`OPENROUTER_MODEL` if you prefer a `:free` variant.
"""

import json
import os
import re
from pathlib import Path

import requests

from config import Config

TIMEOUT = 90

# Groq is fast and free-tier friendly; 120b is the strongest listed model.
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# OpenRouter default. Two "universal router" IDs exist:
#
#   openrouter/free  — picks a random free model. Zero cost, but shares a
#                      50-request/day cap and drops ~1 in 3 requests with an
#                      empty response, which defeats a fallback.
#   openrouter/auto  — routes by prompt; tested 3/3 on this pipeline and billed
#                      at the selected model's rates (≈$0.10 per 1M tokens, so
#                      well under a cent per deck).
#
# The default is `openrouter/auto` because a fallback must actually answer.
# Set OPENROUTER_MODEL=openrouter/free if you would rather pay nothing and
# retry through to the local demo content on the odd failure.
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/auto")


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
    """Generate JSON or code from a prompt using whichever provider answers."""

    def __init__(self):
        # Ordered chain. A provider is included only when its key is set, so
        # adding a key to .env enables it without touching call sites.
        self.providers: list[str] = []

        if Config.GROQ_API_KEY:
            self.providers.append("groq")
        if Config.OPENROUTER_API_KEY:
            self.providers.append("openrouter")
        if Config.GEMINI_API_KEY:
            self.providers.append("gemini")
            import google.generativeai as genai

            genai.configure(api_key=Config.GEMINI_API_KEY)
            self._gemini = genai.GenerativeModel(
                model_name=Config.GEMINI_MODEL,
                generation_config={"response_mime_type": "application/json"},
            )
        else:
            self._gemini = None

    @property
    def available(self) -> bool:
        return bool(self.providers)

    @property
    def provider(self) -> str | None:
        """The preferred provider, for capability reporting."""
        return self.providers[0] if self.providers else None

    # -- providers ------------------------------------------------------
    def _openai_compatible(
        self, url: str, key: str, model: str, prompt: str, as_json: bool
    ) -> str:
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        # Structured output is only offered by some models; code generation
        # must not be JSON-wrapped, so it is always sent as plain completion.
        if as_json:
            body["response_format"] = {"type": "json_object"}

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=TIMEOUT,
        )
        if response.status_code != 200:
            raise LLMError(f"{url.split('/')[2]} {response.status_code}: {response.text[:200]}")

        try:
            message = response.json()["choices"][0]["message"].get("content")
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMError(f"Malformed response from {url.split('/')[2]}") from exc
        if not message:
            # Rate-limited free models sometimes return an empty message.
            raise LLMError(f"Empty response from {url.split('/')[2]}")
        return message

    def _groq(self, prompt: str, as_json: bool = True) -> str:
        return self._openai_compatible(
            GROQ_URL, Config.GROQ_API_KEY, DEFAULT_GROQ_MODEL, prompt, as_json
        )

    def _openrouter(self, prompt: str, as_json: bool = True) -> str:
        return self._openai_compatible(
            OPENROUTER_URL,
            Config.OPENROUTER_API_KEY,
            DEFAULT_OPENROUTER_MODEL,
            prompt,
            as_json,
        )

    def _gemini_generate(self, prompt: str) -> str:
        if self._gemini is None:
            raise LLMError("Gemini is not configured")
        text = self._gemini.generate_content(prompt).text
        if not text:
            raise LLMError("Empty response from Gemini")
        return text

    # -- dispatch -------------------------------------------------------
    def _call(self, provider: str, prompt: str, as_json: bool) -> str:
        if provider == "groq":
            return self._groq(prompt, as_json)
        if provider == "openrouter":
            return self._openrouter(prompt, as_json)
        if provider == "gemini":
            return self._gemini_generate(prompt)
        raise LLMError(f"Unknown provider: {provider}")

    def _dispatch(self, prompt: str, as_json: bool, strict: bool = False) -> str:
        """Try each provider in turn, returning the first usable answer.

        `strict` re-asks for pure JSON on the second pass, used when a model
        wrapped valid output in prose.
        """
        errors = []
        for provider in self.providers:
            try:
                return self._call(provider, prompt, as_json)
            except Exception as exc:  # noqa: BLE001
                # Do not print every fallback noise; the UI reports the final
                # outcome, and the local generator is a legitimate result.
                print(f"  {provider} failed: {str(exc)[:140]}")
                errors.append(f"{provider}: {str(exc)[:80]}")
        raise LLMError("All LLM providers failed — " + "; ".join(errors))

    # -- public ---------------------------------------------------------
    def generate_json(self, prompt: str) -> dict:
        """Run the prompt and return a parsed JSON object."""
        if not self.available:
            raise LLMError("No LLM provider is configured")

        raw = self._dispatch(prompt, as_json=True)

        try:
            return json.loads(_strip_fence(raw))
        except json.JSONDecodeError:
            # Some models ignore response_format and wrap output in prose.
            strict = (
                "Respond with a single valid JSON object and nothing else. "
                "No explanation, no markdown fence.\n\n" + prompt
            )
            retry_raw = self._dispatch(strict, as_json=True)
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

        raw = self._dispatch(prompt, as_json=False)

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
