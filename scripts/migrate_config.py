#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _normalize_common(data: dict[str, Any]) -> dict[str, Any]:
    common: dict[str, Any] = {}
    common_source = None
    for candidate in ("COMMON", "common"):
        if isinstance(data.get(candidate), dict):
            common_source = data[candidate]
            break

    if common_source is not None:
        common = dict(common_source)
    else:
        key_map = {
            "DOMAIN": "DOMAIN",
            "domain": "DOMAIN",
            "PORT": "PORT",
            "port": "PORT",
            "DEFAULT_REQUEST_TIMEOUT": "DEFAULT_REQUEST_TIMEOUT",
            "default_request_timeout": "DEFAULT_REQUEST_TIMEOUT",
            "API_KEY": "API_KEY",
            "api_key": "API_KEY",
            "ROLE": "ROLE",
            "role": "ROLE",
        }
        for key, value in data.items():
            if key in key_map:
                common[key_map[key]] = value

    role = None
    if isinstance(common.get("ROLE"), str):
        role = common["ROLE"].lower()
    elif isinstance(data.get("ROLE"), str):
        role = data["ROLE"].lower()
    elif ("WAKER" in data or "waker" in data) and ("SLEEPER" not in data and "sleeper" not in data):
        role = "waker"
    elif ("SLEEPER" in data or "sleeper" in data) and ("WAKER" not in data and "waker" not in data):
        role = "sleeper"

    if role in ("waker", "sleeper"):
        common["ROLE"] = role

    return common


def _normalize_section(section_data: Any) -> dict[str, Any] | None:
    if not isinstance(section_data, dict):
        return None
    normalized: dict[str, Any] = {}
    key_map = {
        "name": "name",
        "mac_address": "mac_address",
        "mac": "mac_address",
        "systemctl_command": "systemctl_command",
        "systemctl": "systemctl_command",
        "suspend_verb": "suspend_verb",
        "status_verb": "status_verb",
        "wol_exec": "wol_exec",
    }
    for key, value in section_data.items():
        lowered = key.lower()
        if lowered in key_map:
            normalized[key_map[lowered]] = value
        else:
            normalized[key] = value
    return normalized


def _format_value(value: Any) -> str:
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def migrate_config(src: Path, dest: Path) -> bool:
    data = json.loads(src.read_text())

    lines: list[str] = []
    common = _normalize_common(data)
    lines.append("[COMMON]")
    for key, value in common.items():
        lines.append(f"{key} = {_format_value(value)}")
    lines.append("")

    for section, candidates in (("WAKER", ("WAKER", "waker")), ("SLEEPER", ("SLEEPER", "sleeper"))):
        section_data = None
        for candidate in candidates:
            if candidate in data:
                section_data = data.get(candidate)
                break
        section_data = _normalize_section(section_data)
        if not isinstance(section_data, dict):
            continue
        lines.append(f"[{section}]")
        for key, value in section_data.items():
            lines.append(f"{key} = {_format_value(value)}")
        lines.append("")

    dest.write_text("\n".join(lines).strip() + "\n")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate Sleep Manager JSON config to TOML")
    parser.add_argument("src", type=Path, help="Path to legacy JSON config")
    parser.add_argument("dest", type=Path, help="Path to TOML output")
    args = parser.parse_args()

    migrate_config(args.src, args.dest)
