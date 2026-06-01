from __future__ import annotations

import textwrap
import time
from dataclasses import dataclass
from typing import Optional

from src.chatbot.dataset import MetadataRepository
from src.chatbot.intent import detect_intent
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import normalize_error_code


@dataclass(frozen=True)
class ChatResult:
    intent: str
    answer: str
    status: str
    latency_ms: int
    error_code: Optional[str] = None


class MetadataChatbot:
    def __init__(self, repository: MetadataRepository, llm: Optional[LLMProvider] = None):
        self.repository = repository
        self.llm = llm

    def respond(self, user_input: str) -> ChatResult:
        started_at = time.perf_counter()
        intent = detect_intent(user_input)
        status = "success"
        error_code: Optional[str] = None

        try:
            if intent.name == "recommend":
                answer = self._recommend_response(user_input)
            elif intent.name == "summarize":
                answer = self._summarize_response(user_input)
            else:
                answer = self._search_response(user_input)
        except Exception as exc:
            status = "fail"
            error_code = normalize_error_code(exc)
            answer = (
                "Tôi gặp lỗi khi xử lý yêu cầu này. "
                "Bạn hãy thử lại bằng tên tác phẩm, tác giả hoặc thể loại cụ thể hơn."
            )

        latency_ms = int((time.perf_counter() - started_at) * 1000)
        logger.log_turn(
            input_text=user_input,
            answer_text=answer,
            intent=intent.name,
            status=status,
            latency_ms=latency_ms,
            error_code=error_code,
        )
        return ChatResult(
            intent=intent.name,
            answer=answer,
            status=status,
            latency_ms=latency_ms,
            error_code=error_code,
        )

    def _search_response(self, user_input: str) -> str:
        hits = self.repository.search(user_input, top_k=5)
        if not hits:
            return (
                "Tôi chưa tìm thấy kết quả phù hợp trong dataset 100 tác phẩm. "
                "Bạn có thể thử theo tên tác phẩm, tên tác giả, thể loại hoặc khu vực."
            )

        base_answer = self._format_records(
            intro="Tôi tìm thấy các mục phù hợp trong metadata:",
            records=[hit.record for hit in hits],
        )

        prompt = textwrap.dedent(
            f"""
            Dựa hoàn toàn trên metadata sau, hãy viết câu trả lời ngắn gọn bằng tiếng Việt.
            Không bịa thêm nội dung ngoài metadata.

            Câu hỏi người dùng: {user_input}

            Metadata:
            {base_answer}
            """
        ).strip()
        return self._maybe_polish_with_llm(prompt, base_answer)

    def _summarize_response(self, user_input: str) -> str:
        title_match = self.repository.find_title_match(user_input)
        if title_match:
            base_answer = self.repository.summarize_work(title_match)
        else:
            author_match = self.repository.find_author_match(user_input)
            if author_match:
                base_answer = self.repository.summarize_author(author_match)
            else:
                hits = self.repository.search(user_input, top_k=1)
                if not hits:
                    return (
                        "Tôi chưa xác định được tác phẩm hay tác giả cần tóm tắt trong dataset. "
                        "Bạn hãy nêu rõ tên tác phẩm hoặc tác giả."
                    )
                base_answer = self.repository.summarize_work(hits[0].record)

        prompt = textwrap.dedent(
            f"""
            Viết lại phần mô tả sau thành 2-4 câu tiếng Việt tự nhiên, vẫn chỉ dựa trên metadata.
            Không thêm tình tiết nội dung tác phẩm.

            Nội dung gốc:
            {base_answer}
            """
        ).strip()
        return self._maybe_polish_with_llm(prompt, base_answer)

    def _recommend_response(self, user_input: str) -> str:
        seed = self.repository.find_title_match(user_input)
        recommendations = self.repository.recommend(user_input, top_k=5)
        if not recommendations:
            return "Tôi chưa có đủ metadata để đưa ra gợi ý phù hợp."

        if seed:
            intro = f"Nếu bạn quan tâm đến \"{seed.title}\", đây là các tác phẩm gần nhất theo metadata:"
        else:
            author_match = self.repository.find_author_match(user_input)
            if author_match:
                intro = f"Dựa trên tác giả {author_match}, đây là một số gợi ý từ dataset:"
            else:
                genre = self.repository.extract_genre(user_input)
                region = self.repository.extract_region(user_input)
                scope = ", ".join(part for part in [genre, region] if part)
                intro = f"Gợi ý theo metadata ({scope}):" if scope else "Đây là một số gợi ý từ dataset:"

        base_answer = self._format_records(intro=intro, records=recommendations)

        prompt = textwrap.dedent(
            f"""
            Viết lại danh sách gợi ý sau thành câu trả lời tiếng Việt rõ ràng, ngắn gọn.
            Chỉ dùng dữ liệu đã có, không suy đoán nội dung tác phẩm.

            {base_answer}
            """
        ).strip()
        return self._maybe_polish_with_llm(prompt, base_answer)

    def _maybe_polish_with_llm(self, prompt: str, fallback: str) -> str:
        if self.llm is None:
            return fallback

        try:
            result = self.llm.generate(
                prompt=prompt,
                system_prompt=(
                    "Bạn là chatbot baseline cho bài lab. "
                    "Chỉ diễn đạt lại metadata thành tiếng Việt gọn rõ, không bịa thêm nội dung."
                ),
            )
        except Exception:
            return fallback

        content = (result.get("content") or "").strip()
        return content or fallback

    def _format_records(self, intro: str, records: list) -> str:
        lines = [intro]
        for index, record in enumerate(records, start=1):
            lines.append(
                f"{index}. {record.title} - {record.author} | {record.genre} | {record.display_year} | {record.region}"
            )
        return "\n".join(lines)
