from __future__ import annotations

import os
from typing import Optional

from src.core.gemini_provider import GeminiProvider
from src.core.llm_provider import LLMProvider
from src.core.openai_provider import OpenAIProvider


def build_provider() -> Optional[LLMProvider]:
    provider_name = os.getenv("DEFAULT_PROVIDER", "none").strip().lower()
    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return OpenAIProvider(model_name=model_name, api_key=api_key)

    if provider_name == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        return GeminiProvider(model_name=model_name, api_key=api_key)

    return None
