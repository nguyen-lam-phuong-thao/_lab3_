from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

os.environ["LOG_DIR"] = str(PROJECT_ROOT / "logs" / "tests")
os.environ["CHAT_HISTORY_PATH"] = str(PROJECT_ROOT / "logs" / "tests" / "chat_history.txt")

from src.chatbot.dataset import MetadataRepository
from src.chatbot.service import MetadataChatbot


def build_chatbot() -> MetadataChatbot:
    repository = MetadataRepository(PROJECT_ROOT / "dataset_tac_pham_van_hoc_wikipedia_100.csv")
    return MetadataChatbot(repository=repository)


class MetadataChatbotTests(unittest.TestCase):
    def test_search_returns_matching_title(self) -> None:
        chatbot = build_chatbot()
        result = chatbot.respond("Tìm tác phẩm Chí Phèo")
        self.assertEqual(result.status, "success")
        self.assertIn("Chí Phèo", result.answer)
        self.assertIn("Nam Cao", result.answer)

    def test_recommend_for_title_keeps_related_metadata(self) -> None:
        chatbot = build_chatbot()
        result = chatbot.respond("Gợi ý tác phẩm tương tự Chí Phèo")
        self.assertEqual(result.status, "success")
        self.assertTrue("Lão Hạc" in result.answer or "Đời thừa" in result.answer)

    def test_summarize_author_uses_metadata_only(self) -> None:
        chatbot = build_chatbot()
        result = chatbot.respond("Giới thiệu Nam Cao")
        self.assertEqual(result.status, "success")
        self.assertIn("Nam Cao", result.answer)


if __name__ == "__main__":
    unittest.main()
