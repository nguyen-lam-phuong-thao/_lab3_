from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional


class IndustryLogger:
    def __init__(self, name: str = "lab3-baseline-chatbot", log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if self.logger.handlers:
            return

        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

        formatter = logging.Formatter("%(message)s")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        if os.getenv("LOG_TO_CONSOLE", "0") == "1":
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def log_turn(
        self,
        *,
        input_text: str,
        answer_text: str,
        intent: str,
        status: str,
        latency_ms: int,
        error_code: Optional[str] = None,
    ) -> None:
        timestamp = datetime.now(UTC).isoformat()
        payload: Dict[str, Any] = {
            "timestamp": timestamp,
            "event": "CHAT_TURN",
            "data": {
                "intent": intent,
                "status": status,
                "latency_ms": latency_ms,
                "input": input_text,
                "answer": answer_text,
                "error_code": error_code,
            },
        }
        self.logger.info(json.dumps(payload, ensure_ascii=False))
        self.append_chat_history(
            timestamp=timestamp,
            intent=intent,
            status=status,
            user_input=input_text,
            answer=answer_text,
        )

    def append_chat_history(
        self,
        *,
        timestamp: str,
        intent: str,
        status: str,
        user_input: str,
        answer: str,
    ) -> None:
        history_path = Path(os.getenv("CHAT_HISTORY_PATH", "reports/chat_history.txt"))
        history_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"[{timestamp}]",
            f"intent: {intent}",
            f"status: {status}",
            f"user: {user_input}",
            f"bot: {answer}",
            "",
        ]
        with history_path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))


logger = IndustryLogger(log_dir=os.getenv("LOG_DIR", "logs"))
