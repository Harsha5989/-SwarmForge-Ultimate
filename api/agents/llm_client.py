"""LLM client wrapping LiteLLM for unified model access."""

import json
import re
import time
import asyncio
from typing import Optional

import httpx
import structlog

from config import get_settings

log = structlog.get_logger()


class LLMClient:
    """Async LLM client that calls models via LiteLLM proxy."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.settings = get_settings()
        self.base_url = self.settings.litellm_base_url
        self.api_key = self.settings.litellm_api_key
        self._client = httpx.AsyncClient(timeout=180.0)

    async def complete(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> tuple[str, int, int]:
        """
        Call the LLM and return (response_text, tokens_in, tokens_out).

        NOTE: json_mode is intentionally NOT sent to the API because Groq/DeepSeek
        models reject response_format=json_object. Instead, callers should instruct
        the model via the system prompt to return JSON, and parse it themselves.
        """
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        payload = {
            "model": self.model_name,
            "messages": messages,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        # Do NOT add response_format — Groq/DeepSeek reject it with 400.
        # The system prompt already instructs models to return JSON.

        max_retries = 3
        for attempt in range(max_retries):
            start = time.time()
            try:
                resp = await self._client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )

                if resp.status_code == 429:
                    wait = (2 ** attempt) * 5
                    log.warning("rate_limited", model=self.model_name, wait=wait, attempt=attempt + 1)
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()
                data = resp.json()

                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                tokens_in = usage.get("prompt_tokens", 0)
                tokens_out = usage.get("completion_tokens", 0)
                elapsed = int((time.time() - start) * 1000)

                log.info(
                    "llm_complete",
                    model=self.model_name,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    duration_ms=elapsed,
                )

                return content, tokens_in, tokens_out

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait = (2 ** attempt) * 5
                    await asyncio.sleep(wait)
                    continue
                log.error("llm_error", model=self.model_name, status=e.response.status_code, error=str(e))
                raise
            except Exception as e:
                log.error("llm_error", model=self.model_name, error=str(e))
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

        raise RuntimeError(f"LLM call failed after {max_retries} retries: {self.model_name}")

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that may contain markdown fences or reasoning tags."""
        # Strip DeepSeek <think>...</think> blocks
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(lines).strip()

        return text

    async def complete_json(self, system: str, user: str) -> dict:
        """Call LLM expecting JSON response, parse and return dict."""
        content, tokens_in, tokens_out = await self.complete(
            system=system, user=user,
        )

        text = self._extract_json(content)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find outermost JSON object or array
            for start_char, end_char in [('{', '}'), ('[', ']')]:
                start_idx = text.find(start_char)
                end_idx = text.rfind(end_char) + 1
                if start_idx != -1 and end_idx > start_idx:
                    candidate = text[start_idx:end_idx]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        continue
            raise ValueError(f"Could not parse JSON from LLM response: {text[:300]}")

    async def close(self):
        await self._client.aclose()
