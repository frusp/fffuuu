"""
Storage layer for fffuuu.
All data lives in ~/.fff/contacts.toml - plain text, human-readable,
survives being cat'd during an outage.
"""
import os
import sys
import copy
import tomllib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# ── stdlib-only TOML write (Python has tomllib read-only until 3.11) ──────────
# We implement a minimal TOML serialiser so we have zero external deps.

def _toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(v)
    if isinstance(v, str):
        escaped = v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    if isinstance(v, list):
        items = ", ".join(_toml_value(i) for i in v)
        return f"[{items}]"
    raise TypeError(f"Unsupported type for TOML: {type(v)}")


def _write_toml(data: dict, path: Path) -> None:
    """Minimal TOML writer - handles the flat+array-of-tables structure we use."""
    lines = []

    # Top-level scalars first
    for k, v in data.items():
        if not isinstance(v, (dict, list)) or (isinstance(v, list) and not v):
            lines.append(f"{k} = {_toml_value(v)}")
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            pass  # array of tables - handled below
        elif isinstance(v, dict):
            pass  # inline table section - handled below

    # Inline table sections (non-array)
    for k, v in data.items():
        if isinstance(v, dict):
            lines.append(f"\n[{k}]")
            for sk, sv in v.items():
                if not isinstance(sv, (dict, list)):
                    lines.append(f"{sk} = {_toml_value(sv)}")

    # Array of tables
    for k, v in data.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            for item in v:
                lines.append(f"\n[[{k}]]")
                for sk, sv in item.items():
                    if isinstance(sv, list) and sv and isinstance(sv[0], dict):
                        # nested array of tables (e.g. contact.schedules)
                        for sub in sv:
                            lines.append(f"  # nested - stored inline")
                    else:
                        lines.append(f"{sk} = {_toml_value(sv)}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Paths ─────────────────────────────────────────────────────────────────────

def _fff_dir() -> Path:
    base = os.environ.get("FFF_DIR")
    if base:
        return Path(base)
    return Path.home() / ".fff"


def contacts_path() -> Path:
    return _fff_dir() / "contacts.toml"


def config_path() -> Path:
    return _fff_dir() / "config.toml"


def ensure_dir() -> None:
    _fff_dir().mkdir(parents=True, exist_ok=True)


# ── Default data ──────────────────────────────────────────────────────────────

EXAMPLE_CONTACTS = """\
# fffuuu contacts - human-readable emergency contact directory
# Edit this file directly or use: fff add / fff import
# Fields: name, role, team, phone, slack, email, oncall (bool), notes

[[contact]]
name    = "Ada Lovelace"
role    = "Senior SRE"
team    = "platform"
phone   = "+1-555-000-0001"
slack   = "@ada"
email   = "ada@example.com"
oncall  = true
notes   = "Primary on-call Mon-Wed. Prefers Slack ping first."

[[contact]]
name    = "Grace Hopper"
role    = "SRE Lead"
team    = "platform"
phone   = "+1-555-000-0002"
slack   = "@grace"
email   = "grace@example.com"
oncall  = false
notes   = "Escalation path for platform. Will answer at any hour for SEV-0."

[[contact]]
name    = "Dennis Ritchie"
role    = "SRE"
team    = "networking"
phone   = "+1-555-000-0003"
slack   = "@dennis"
email   = "dennis@example.com"
oncall  = true
notes   = "BGP/routing issues. Kernel panics. Owns the dark fibre runbook."

[[contact]]
name    = "Ken Thompson"
role    = "Principal SRE"
team    = "networking"
phone   = "+1-555-000-0004"
slack   = "@ken"
email   = "ken@example.com"
oncall  = false
notes   = "Wake Ken only for full DC loss. Seriously."
"""

EXAMPLE_CONFIG = """\
# fffuuu config
[sync]
# url = "https://your-internal-url/contacts.toml"
# Or a path to a shared network file:
# path = "/mnt/shared/sre/contacts.toml"
last_synced = ""
"""


# ── Load / Save ───────────────────────────────────────────────────────────────

def load_contacts() -> list[dict]:
    path = contacts_path()
    if not path.exists():
        return []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        return data.get("contact", [])
    except Exception as e:
        print(f"[fff] ERROR reading {path}: {e}", file=sys.stderr)
        print(f"[fff] The file may be corrupt. Check it manually: {path}", file=sys.stderr)
        sys.exit(1)


def save_contacts(contacts: list[dict]) -> None:
    ensure_dir()
    path = contacts_path()
    # Write TOML manually so we keep the human-friendly format
    lines = [
        "# fffuuu contacts - human-readable emergency contact directory",
        "# Edit this file directly or use: fff add / fff import",
        "# Fields: name, role, team, phone, slack, email, oncall (bool), notes",
        "",
    ]
    for c in contacts:
        lines.append("[[contact]]")
        for field in ["name", "role", "team", "phone", "slack", "email", "oncall", "notes"]:
            if field in c:
                v = c[field]
                if isinstance(v, bool):
                    lines.append(f"{field:<7} = {'true' if v else 'false'}")
                elif isinstance(v, str):
                    escaped = v.replace("\\", "\\\\").replace('"', '\\"')
                    lines.append(f"{field:<7} = \"{escaped}\"")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def init_if_needed() -> bool:
    """Create default files if they don't exist. Returns True if freshly initialised."""
    ensure_dir()
    fresh = False
    if not contacts_path().exists():
        contacts_path().write_text(EXAMPLE_CONTACTS, encoding="utf-8")
        fresh = True
    if not config_path().exists():
        config_path().write_text(EXAMPLE_CONFIG, encoding="utf-8")
    return fresh
