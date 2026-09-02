#!/usr/bin/env python3
"""Append privacy-safe My Beast Mode usage events to local memory."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import uuid


SKILL_VERSION = "1.3.0"


def memory_path(explicit: str | None = None) -> Path:
    return Path(explicit or os.environ.get("MY_BEAST_MODE_MEMORY", "~/.my-beast-mode/memory.jsonl")).expanduser()


def clean(text: str, limit: int = 240) -> str:
    return " ".join(text.split())[:limit]


def safe_name(text: str, default: str = "unknown") -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]", "-", text.strip())[:40]
    return value or default


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
        "version": 2,
        "skill_version": SKILL_VERSION,
        "event": kind,
        "session": session,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project": str(Path(project).expanduser().resolve()),
    }


def read_sessions(path: Path) -> list[dict[str, object]]:
    starts: dict[str, dict[str, object]] = {}
    finishes: dict[str, dict[str, object]] = {}
    if not path.is_file():
        return []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
            session = str(event["session"])
            if event.get("event") == "start":
                starts[session] = event
            elif event.get("event") == "finish":
                finishes[session] = event
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    sessions = []
    for session, start in starts.items():
        finish = finishes.get(session, {})
        sessions.append({
            "id": session,
            "started": start.get("timestamp", ""),
            "finished": finish.get("timestamp", ""),
            "project": start.get("project", ""),
            "task_type": start.get("task_type", "other"),
            "agent": start.get("agent", "unknown"),
            "orchestrator": start.get("orchestrator", "host"),
            "outcome": finish.get("outcome", "incomplete"),
            "summary": finish.get("summary", start.get("summary", "")),
            "files_changed": finish.get("files_changed", 0),
            "checks_passed": finish.get("checks_passed", 0),
            "checks_failed": finish.get("checks_failed", 0),
            "skill_version": start.get("skill_version", "legacy"),
        })
    return sorted(sessions, key=lambda item: str(item["started"]), reverse=True)


def search_sessions(sessions: list[dict[str, object]], args: argparse.Namespace) -> list[dict[str, object]]:
    query = args.query.casefold()
    matches = []
    for session in sessions:
        haystack = " ".join(str(session[key]) for key in ("summary", "project", "task_type", "agent", "outcome")).casefold()
        if query and query not in haystack:
            continue
        if args.project and args.project.casefold() not in str(session["project"]).casefold():
            continue
        if args.task_type and session["task_type"] != args.task_type:
            continue
        if args.outcome and session["outcome"] != args.outcome:
            continue
        if args.agent and args.agent.casefold() != str(session["agent"]).casefold():
            continue
        date = str(session["started"])[:10]
        if args.date_start and date < args.date_start:
            continue
        if args.date_end and date > args.date_end:
            continue
        matches.append(session)
    return matches[: args.limit]


def self_test() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "memory.jsonl"
        append_event(path, {**base_event("start", "test-session", tmp), "summary": clean("  safe\nsummary  ")})
        append_event(path, {**base_event("finish", "test-session", tmp), "outcome": "success"})
        events = [json.loads(line) for line in path.read_text().splitlines()]
        assert [event["event"] for event in events] == ["start", "finish"]
        assert events[0]["summary"] == "safe summary"
        args = argparse.Namespace(query="safe", project="", task_type="", outcome="success", agent="", date_start="", date_end="", limit=20)
        assert search_sessions(read_sessions(path), args)[0]["outcome"] == "success"
    print("self-test passed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory", help="override the memory.jsonl path")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="record the start of a skill run")
    start.add_argument("--project", default=os.getcwd())
    start.add_argument("--task-type", choices=("review", "debug", "change", "research", "other"), default="other")
    start.add_argument("--orchestrator", choices=("local", "remote", "host", "off"), default="host")
    start.add_argument("--agent", default=os.environ.get("MY_BEAST_MODE_AGENT", "unknown"))
    start.add_argument("--summary", required=True, help="sanitized high-level intent, no prompt or secrets")

    finish = sub.add_parser("finish", help="record the end of a skill run")
    finish.add_argument("--session", required=True)
    finish.add_argument("--project", default=os.getcwd())
    finish.add_argument("--outcome", choices=("success", "partial", "failed"), required=True)
    finish.add_argument("--summary", required=True, help="sanitized result, no source content or secrets")
    finish.add_argument("--files-changed", type=int, default=0)
    finish.add_argument("--checks-passed", type=int, default=0)
    finish.add_argument("--checks-failed", type=int, default=0)

    recall = sub.add_parser("recall", help="search prior Beast Mode sessions")
    recall.add_argument("query", nargs="?", default="")
    recall.add_argument("--project", default="")
    recall.add_argument("--task-type", choices=("review", "debug", "change", "research", "other"))
    recall.add_argument("--outcome", choices=("success", "partial", "failed", "incomplete"))
    recall.add_argument("--agent", default="")
    recall.add_argument("--date-start", default="")
    recall.add_argument("--date-end", default="")
    recall.add_argument("--limit", type=int, choices=range(1, 101), default=20, metavar="1..100")
    recall.add_argument("--format", choices=("text", "json"), default="text")

    sub.add_parser("self-test", help="run the bundled smoke test")
    args = parser.parse_args()
    if args.command == "self-test":
        self_test()
        return

    path = memory_path(args.memory)
    if args.command == "recall":
        matches = search_sessions(read_sessions(path), args)
        if args.format == "json":
            print(json.dumps(matches, indent=2, ensure_ascii=False))
        elif not matches:
            print("No matching Beast Mode memory.")
        else:
            for item in matches:
                project = Path(str(item["project"])).name or str(item["project"])
                print(f"{str(item['started'])[:10]}  {str(item['id'])[:8]}  {item['outcome']:<10}  {project:<24}  {clean(str(item['summary']), 100)}")
        return

    if args.command == "start":
        session = str(uuid.uuid4())
        event = base_event("start", session, args.project)
        event.update(task_type=args.task_type, orchestrator=args.orchestrator, agent=safe_name(args.agent), summary=clean(args.summary))
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
