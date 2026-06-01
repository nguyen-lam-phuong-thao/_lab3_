from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_turns(log_path: Path) -> list[dict]:
    turns = []
    with log_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event") == "CHAT_TURN":
                turns.append(event["data"])
    return turns


def summarize(log_path: Path) -> str:
    turns = load_turns(log_path)
    total = len(turns)
    success = sum(1 for turn in turns if turn.get("status") == "success")
    fail = total - success
    avg_latency = round(sum(turn.get("latency_ms", 0) for turn in turns) / total, 2) if total else 0.0

    lines = [
        f"Log file: {log_path}",
        f"Total chat turns: {total}",
        f"Success: {success}",
        f"Fail: {fail}",
        f"Average latency (ms): {avg_latency}",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize simple chatbot logs.")
    parser.add_argument("--log", default="./logs/latest", help="Path to a .log file or ./logs/latest")
    parser.add_argument("--output", help="Optional path to save the summary")
    args = parser.parse_args()

    if args.log == "./logs/latest":
        candidates = sorted(Path("./logs").glob("*.log"))
        if not candidates:
            raise SystemExit("No log files found in ./logs")
        log_path = candidates[-1]
    else:
        log_path = Path(args.log)

    summary = summarize(log_path)
    print(summary)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(summary + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
