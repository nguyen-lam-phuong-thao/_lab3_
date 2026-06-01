from __future__ import annotations

from dataclasses import dataclass

from src.chatbot.dataset import normalize_text


@dataclass(frozen=True)
class IntentResult:
    name: str
    confidence: float


RECOMMEND_TERMS = (
    "goi y",
    "gợi ý",
    "de xuat",
    "đề xuất",
    "recommend",
    "similar",
    "tuong tu",
    "tương tự",
)

SUMMARIZE_TERMS = (
    "tom tat",
    "tóm tắt",
    "gioi thieu",
    "giới thiệu",
    "summary",
    "mo ta",
    "mô tả",
)

SEARCH_TERMS = (
    "tim",
    "tìm",
    "search",
    "tra cuu",
    "tra cứu",
    "liet ke",
    "liệt kê",
    "co tac pham nao",
    "có tác phẩm nào",
)


def detect_intent(user_input: str) -> IntentResult:
    normalized = normalize_text(user_input)

    if any(term in normalized for term in RECOMMEND_TERMS):
        return IntentResult(name="recommend", confidence=0.95)
    if any(term in normalized for term in SUMMARIZE_TERMS):
        return IntentResult(name="summarize", confidence=0.92)
    if any(term in normalized for term in SEARCH_TERMS):
        return IntentResult(name="search", confidence=0.88)
    return IntentResult(name="search", confidence=0.60)
