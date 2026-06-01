from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):  # type: ignore[no-redef]
        return False


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.chatbot.dataset import MetadataRepository
from src.chatbot.service import MetadataChatbot
from src.core.provider_factory import build_provider


def build_chatbot() -> MetadataChatbot:
    dataset_path = os.getenv("DATASET_PATH", "./dataset_tac_pham_van_hoc_wikipedia_100.csv")
    repository = MetadataRepository(PROJECT_ROOT / dataset_path)
    provider = build_provider()
    return MetadataChatbot(repository=repository, llm=provider)


def run_cli() -> None:
    parser = argparse.ArgumentParser(description="Baseline metadata chatbot for Lab 3.")
    parser.add_argument("--query", help="Single-turn query. If omitted, the CLI opens interactive mode.")
    args = parser.parse_args()

    chatbot = build_chatbot()

    if args.query:
        print(chatbot.respond(args.query).answer)
        return

    print("Metadata Chatbot Baseline")
    print("Nhập 'exit' để thoát.")
    while True:
        try:
            user_input = input("\nBạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTạm biệt.")
            return

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Tạm biệt.")
            return

        result = chatbot.respond(user_input)
        print(f"\nBot: {result.answer}")


if __name__ == "__main__":
    run_cli()
