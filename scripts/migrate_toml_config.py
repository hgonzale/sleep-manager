#!/usr/bin/env python3
from __future__ import annotations

import datetime
import shutil
import tomllib
from pathlib import Path
from typing import Any

ALLOWED_SECTIONS = {"common", "waker", "sleeper"}
COMMON_KEY_ORDER = ["role", "domain", "port", "default_request_timeout", "api_key"]
WAKER_KEY_ORDER = ["name", "wol_exec"]
SLEEPER_KEY_ORDER = ["name", "mac_address", "systemctl_command", "suspend_verb", "status_verb"]


def _is_old_format(data: dict[str, Any]) -> bool:
    for key in data:
        if key not in ALLOWED_SECTIONS:
            return True
        if key.lower() != key:
            return True

    for section in ALLOWED_SECTIONS:
        section_data = data.get(section)
        if isinstance(section_data, dict):
            for key in section_data:
                if str(key).lower() != str(key):
                    return True
    return False


def _lower_key_map(data: dict[str, Any], key_map: dict[str, str]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in data.items():
        lowered = str(key).lower()
        normalized[key_map.get(lowered, lowered)] = value
    return normalized


def _normalize_common(common_data: dict[str, Any], top_level_data: dict[str, Any]) -> dict[str, Any]:
    key_map = {
        "domain": "domain",
        "port": "port",
        "default_request_timeout": "default_request_timeout",
        "api_key": "api_key",
        "role": "role",
    }
    normalized = _lower_key_map(common_data, key_map)
    for key, value in top_level_data.items():
        lowered = str(key).lower()
        if lowered in ALLOWED_SECTIONS:
            continue
        normalized[key_map.get(lowered, lowered)] = value
    return normalized


def _normalize_section(section_data: dict[str, Any], key_map: dict[str, str]) -> dict[str, Any]:
    return _lower_key_map(section_data, key_map)


def _pick_section(data: dict[str, Any], section: str) -> dict[str, Any]:
    for candidate in (section, section.upper()):
        section_value = data.get(candidate)
        if isinstance(section_value, dict):
            return dict(section_value)
    return {}


def _format_value(value: Any) -> str:
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _write_section(lines: list[str], name: str, data: dict[str, Any], key_order: list[str]) -> None:
    if not data:
        return
    lines.append(f"[{name}]")
    ordered_keys = [key for key in key_order if key in data]
    remaining_keys = sorted(key for key in data if key not in ordered_keys)
    for key in ordered_keys + remaining_keys:
        lines.append(f"{key} = {_format_value(data[key])}")
    lines.append("")


def migrate_toml_config(path: Path, dest: Path | None = None) -> bool:
    data = tomllib.loads(path.read_text())
    if not _is_old_format(data):
        return False

    common_raw = _pick_section(data, "common")
    waker_raw = _pick_section(data, "waker")
    sleeper_raw = _pick_section(data, "sleeper")

    common = _normalize_common(common_raw, data)
    waker = _normalize_section(
        waker_raw,
        {
            "name": "name",
            "wol_exec": "wol_exec",
        },
    )
    sleeper = _normalize_section(
        sleeper_raw,
        {
            "name": "name",
            "mac": "mac_address",
            "mac_address": "mac_address",
            "systemctl": "systemctl_command",
            "systemctl_command": "systemctl_command",
            "suspend_verb": "suspend_verb",
            "status_verb": "status_verb",
        },
    )

    lines: list[str] = []
    _write_section(lines, "common", common, COMMON_KEY_ORDER)
    _write_section(lines, "waker", waker, WAKER_KEY_ORDER)
    _write_section(lines, "sleeper", sleeper, SLEEPER_KEY_ORDER)
    new_content = "\n".join(lines).strip() + "\n"

    if dest is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = path.with_name(f"{path.name}.bak.{timestamp}")
        shutil.copy2(path, backup_path)
        path.write_text(new_content)
    else:
        dest.write_text(new_content)
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate legacy TOML config to lowercase sections/keys.")
    parser.add_argument("path", type=Path, help="Path to TOML config file")
    parser.add_argument(
        "--dest",
        type=Path,
        help="Write migrated config to destination path instead of modifying in place",
    )
    args = parser.parse_args()

    migrated = migrate_toml_config(args.path, args.dest)
    if migrated and args.dest is None:
        print(f"Migrated legacy config; backup saved to {args.path.name}.bak.<timestamp>")
    if not migrated:
        raise SystemExit(2)
