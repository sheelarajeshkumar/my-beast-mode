#!/usr/bin/env python3
"""Append privacy-safe My Beast Mode usage events to local memory."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import uuid


def memory_path(explicit: str | None = None) -> Path:
    return Path(explicit or os.environ.get("MY_BEAST_MODE_MEMORY", "~/.my-beast-mode/memory.jsonl")).expanduser()


def clean(text: str, limit: int = 240) -> str:
    return " ".join(text.split())[:limit]


def append_event(path: Path, event: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(event, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)


def base_event(kind: str, session: str, project: str) -> dict[str, object]:
    return {
        "version": 1,
        "event": kind,
        "session": session,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project": str(Path(project).expanduser().resolve()),
    }


def self_test() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "memory.jsonl"
        append_event(path, {**base_event("start", "test-session", tmp), "summary": clean("  safe\nsummary  ")})
        append_event(path, {**base_event("finish", "test-session", tmp), "outcome": "success"})
        events = [json.loads(line) for line in path.read_text().splitlines()]
        assert [event["event"] for event in events] == ["start", "finish"]
        assert events[0]["summary"] == "safe summary"
    print("self-test passed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory", help="override the memory.jsonl path")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="record the start of a skill run")
    start.add_argument("--project", default=os.getcwd())
    start.add_argument("--task-type", choices=("review", "debug", "change", "research", "other"), default="other")
    start.add_argument("--orchestrator", choices=("local", "remote", "host", "off"), default="host")
    start.add_argument("--summary", required=True, help="sanitized high-level intent, no prompt or secrets")

    finish = sub.add_parser("finish", help="record the end of a skill run")
    finish.add_argument("--session", required=True)
    finish.add_argument("--project", default=os.getcwd())
    finish.add_argument("--outcome", choices=("success", "partial", "failed"), required=True)
    finish.add_argument("--summary", required=True, help="sanitized result, no source content or secrets")
    finish.add_argument("--files-changed", type=int, default=0)
    finish.add_argument("--checks-passed", type=int, default=0)
    finish.add_argument("--checks-failed", type=int, default=0)

    sub.add_parser("self-test", help="run the bundled smoke test")
    args = parser.parse_args()
    if args.command == "self-test":
        self_test()
        return

    path = memory_path(args.memory)
    if args.command == "start":
        session = str(uuid.uuid4())
        event = base_event("start", session, args.project)
        event.update(task_type=args.task_type, orchestrator=args.orchestrator, summary=clean(args.summary))
        append_event(path, event)
        print(session)
        return

    event = base_event("finish", args.session, args.project)
    event.update(
        outcome=args.outcome,
        summary=clean(args.summary),
        files_changed=max(0, args.files_changed),
        checks_passed=max(0, args.checks_passed),
        checks_failed=max(0, args.checks_failed),
    )
    append_event(path, event)
    print(path)


if __name__ == "__main__":
    main()
