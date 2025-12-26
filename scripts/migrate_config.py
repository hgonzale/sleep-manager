#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _normalize_common(data: dict[str, Any]) -> dict[str, Any]:
    common: dict[str, Any] = {}
    common_source = None
    for candidate in ("common", "COMMON"):
        if isinstance(data.get(candidate), dict):
            common_source = data[candidate]
            break

    if common_source is not None:
        common = {str(key).lower(): value for key, value in common_source.items()}
    else:
        key_map = {
            "DOMAIN": "domain",
            "domain": "domain",
            "PORT": "port",
            "port": "port",
            "DEFAULT_REQUEST_TIMEOUT": "default_request_timeout",
            "default_request_timeout": "default_request_timeout",
            "API_KEY": "api_key",
            "api_key": "api_key",
        }
        for key, value in data.items():
            if key in key_map:
                common[key_map[key]] = value

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
    lines.append("[common]")
    for key, value in common.items():
        lines.append(f"{key} = {_format_value(value)}")
    lines.append("")

    for section, candidates in (("waker", ("waker", "WAKER")), ("sleeper", ("sleeper", "SLEEPER"))):
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
