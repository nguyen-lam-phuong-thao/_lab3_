from __future__ import annotations

import time
from typing import Any, Dict, Generator, Optional

from src.core.llm_provider import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        super().__init__(model_name=model_name, api_key=api_key)
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(
                "Thiếu package google-generativeai. Hãy cài bằng pip install -r requirements.txt."
            ) from exc

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        full_prompt = prompt if not system_prompt else f"System: {system_prompt}\n\nUser: {prompt}"
        response = self.model.generate_content(full_prompt)
        latency_ms = int((time.time() - start_time) * 1000)
        usage_metadata = getattr(response, "usage_metadata", None)
        return {
            "content": getattr(response, "text", "") or "",
            "usage": {
                "prompt_tokens": getattr(usage_metadata, "prompt_token_count", 0),
                "completion_tokens": getattr(usage_metadata, "candidates_token_count", 0),
                "total_tokens": getattr(usage_metadata, "total_token_count", 0),
            },
            "latency_ms": latency_ms,
            "provider": "gemini",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        full_prompt = prompt if not system_prompt else f"System: {system_prompt}\n\nUser: {prompt}"
        response = self.model.generate_content(full_prompt, stream=True)
        for chunk in response:
            text = getattr(chunk, "text", "")
            if text:
                yield text
