from __future__ import annotations

import time
from typing import Any, Dict, Generator, Optional

from src.core.llm_provider import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        super().__init__(model_name=model_name, api_key=api_key)
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Thiếu package openai. Hãy cài bằng pip install -r requirements.txt.") from exc
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "content": response.choices[0].message.content or "",
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "latency_ms": latency_ms,
            "provider": "openai",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
