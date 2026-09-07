#!/usr/bin/env python3
"""Manage the local, secret-free MCP binding for this skill."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


SKILL_NAME = "analyze-yizhilan-data"
SCHEMA_VERSION = 1
REQUIRED_FINGERPRINT = (
    "ai_insight_overview",
    "company_metric_list",
    "material_dashboard",
    "unify_spec_report_list",
    "unify_spec_report_run",
    "unify_table_master",
)


def binding_path() -> Path:
    codex_root_value = os.environ.get("CODEX_HOME")
    codex_root = (
        Path(codex_root_value).expanduser()
        if codex_root_value
        else Path.home() / ".codex"
    )
    return codex_root / "state" / SKILL_NAME / "mcp-binding.json"


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def tool_leaf(raw_name: str) -> str:
    value = raw_name.strip()
    for expected in REQUIRED_FINGERPRINT:
        if value == expected:
            return expected
        if any(
            value.endswith(separator + expected)
            for separator in ("__", ".", "/", ":")
        ):
            return expected
    return value


def fingerprint(tool_names: Iterable[str]) -> list[str]:
    normalized = {tool_leaf(name) for name in tool_names}
    return sorted(set(REQUIRED_FINGERPRINT).intersection(normalized))


def validate_candidate(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    current = fingerprint(args.tool)
    missing = sorted(set(REQUIRED_FINGERPRINT).difference(current))
    return current, missing


def load_binding(path: Path) -> tuple[dict | None, str | None]:
    if not path.exists():
        return None, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"binding_unreadable: {exc}"
    if not isinstance(payload, dict):
        return None, "binding_invalid: root is not an object"
    return payload, None


def command_status(_: argparse.Namespace) -> int:
    path = binding_path()
    binding, error = load_binding(path)
    if error:
        emit({"status": "invalid", "path": str(path), "reason": error})
        return 2
    if binding is None:
        emit({"status": "unbound", "path": str(path)})
        return 0
    safe_fields = {
        key: binding.get(key)
        for key in (
            "schema_version",
            "skill",
            "server_name",
            "namespace",
            "tool_fingerprint",
            "confirmed_at",
        )
    }
    emit({"status": "bound", "path": str(path), "binding": safe_fields})
    return 0


def command_check(args: argparse.Namespace) -> int:
    path = binding_path()
    current, missing = validate_candidate(args)
    if missing:
        emit(
            {
                "status": "invalid_candidate",
                "missing_core_tools": missing,
                "observed_core_tools": current,
            }
        )
        return 2

    binding, error = load_binding(path)
    if error:
        emit(
            {
                "status": "needs_reconfirmation",
                "path": str(path),
                "reason": error,
            }
        )
        return 0
    if binding is None:
        emit(
            {
                "status": "needs_confirmation",
                "path": str(path),
                "candidate": {
                    "server_name": args.server_name,
                    "namespace": args.namespace,
                    "tool_fingerprint": current,
                },
            }
        )
        return 0

    mismatches = {}
    expected_pairs = {
        "schema_version": SCHEMA_VERSION,
        "skill": SKILL_NAME,
        "server_name": args.server_name,
        "namespace": args.namespace,
        "tool_fingerprint": current,
    }
    for key, observed in expected_pairs.items():
        if binding.get(key) != observed:
            mismatches[key] = {
                "bound": binding.get(key),
                "observed": observed,
            }

    if mismatches:
        emit(
            {
                "status": "needs_reconfirmation",
                "path": str(path),
                "mismatches": mismatches,
            }
        )
        return 0

    emit(
        {
            "status": "bound",
            "path": str(path),
            "server_name": args.server_name,
            "namespace": args.namespace,
            "tool_fingerprint": current,
        }
    )
    return 0


def command_confirm(args: argparse.Namespace) -> int:
    if not args.user_confirmed:
        emit(
            {
                "status": "refused",
                "reason": "confirm requires --user-confirmed after an explicit user yes",
            }
        )
        return 2

    current, missing = validate_candidate(args)
    if missing:
        emit(
            {
                "status": "invalid_candidate",
                "missing_core_tools": missing,
                "observed_core_tools": current,
            }
        )
        return 2

    payload = {
        "schema_version": SCHEMA_VERSION,
        "skill": SKILL_NAME,
        "server_name": args.server_name,
        "namespace": args.namespace,
        "tool_fingerprint": current,
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
    }
    path = binding_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".mcp-binding-",
            suffix=".json",
            delete=False,
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            temporary_name = handle.name
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)

    emit({"status": "confirmed", "path": str(path), "binding": payload})
    return 0


def add_candidate_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--server-name", required=True)
    parser.add_argument("--namespace", required=True)
    parser.add_argument(
        "--tool",
        action="append",
        required=True,
        help="Exposed MCP tool name; repeat once per tool.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect, verify, or confirm the local MCP binding."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Show safe binding metadata.")
    status_parser.set_defaults(func=command_status)

    check_parser = subparsers.add_parser(
        "check", help="Compare a discovered MCP candidate with the local binding."
    )
    add_candidate_arguments(check_parser)
    check_parser.set_defaults(func=command_check)

    confirm_parser = subparsers.add_parser(
        "confirm", help="Write a binding after the user explicitly confirms it."
    )
    add_candidate_arguments(confirm_parser)
    confirm_parser.add_argument(
        "--user-confirmed",
        action="store_true",
        help="Assert that the user explicitly approved this candidate.",
    )
    confirm_parser.set_defaults(func=command_confirm)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
