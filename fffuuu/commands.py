"""
Command implementations for fffuuu.
"""
import sys
import os
import csv
import io
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

from . import store, display


# ── helpers ───────────────────────────────────────────────────────────────────

def _match(contact: dict, query: str) -> bool:
    q = query.lower()
    return any(
        q in str(v).lower()
        for v in contact.values()
    )


def _teams(contacts: list[dict]) -> dict[str, list[dict]]:
    teams: dict[str, list[dict]] = {}
    for c in contacts:
        t = c.get("team", "unknown")
        teams.setdefault(t, []).append(c)
    return teams


# ── commands ──────────────────────────────────────────────────────────────────

def cmd_list(args) -> int:
    """List all contacts, optionally grouped by team."""
    contacts = store.load_contacts()
    if not contacts:
        display.warn("No contacts found. Run 'fff init' or 'fff import <file>'.")
        return 1

    verbose = getattr(args, "verbose", False)

    if getattr(args, "by_team", False):
        for team, members in sorted(_teams(contacts).items()):
            display.print_section(team, members, verbose=verbose)
    else:
        display.print_header(f"All contacts ({len(contacts)})")
        for c in contacts:
            display.print_contact(c, verbose=verbose)
            print()
    return 0


def cmd_team(args) -> int:
    """Show contacts for a specific team."""
    contacts = store.load_contacts()
    name = args.name.lower()
    matches = [c for c in contacts if c.get("team", "").lower() == name]

    if not matches:
        # fuzzy: team name contains the query
        matches = [c for c in contacts if name in c.get("team", "").lower()]

    if not matches:
        available = sorted({c.get("team", "?") for c in contacts})
        display.err(f"No team matching '{args.name}'. Available: {', '.join(available)}")
        return 1

    team_name = matches[0].get("team", args.name)
    verbose = getattr(args, "verbose", False)
    display.print_section(team_name, matches, verbose=verbose)
    return 0


def cmd_oncall(args) -> int:
    """Show only contacts currently marked as on-call."""
    contacts = store.load_contacts()
    oncall = [c for c in contacts if c.get("oncall", False)]

    if not oncall:
        display.warn("Nobody is marked as on-call in contacts.toml.")
        display.info("Edit the file and set oncall = true, or use 'fff set-oncall <name>'.")
        return 1

    display.print_oncall_banner()
    display.print_header(f"ON-CALL NOW ({len(oncall)} people)")
    verbose = getattr(args, "verbose", False)
    for c in oncall:
        display.print_contact(c, verbose=verbose)
        print()
    return 0


def cmd_find(args) -> int:
    """Full-text search across all fields."""
    contacts = store.load_contacts()
    query = " ".join(args.query)
    matches = [c for c in contacts if _match(c, query)]

    if not matches:
        display.warn(f"No contacts matching '{query}'.")
        return 1

    display.print_header(f"Results for '{query}' ({len(matches)})")
    verbose = getattr(args, "verbose", False)
    for c in matches:
        display.print_contact(c, verbose=verbose)
        print()
    return 0


def cmd_teams(args) -> int:
    """List all known teams."""
    contacts = store.load_contacts()
    teams = _teams(contacts)
    display.print_header(f"Teams ({len(teams)})")
    for team, members in sorted(teams.items()):
        oncall_count = sum(1 for m in members if m.get("oncall", False))
        oncall_str = f"  {display.GREEN}● {oncall_count} on-call{display.RESET}" if oncall_count else ""
        print(f"  {display.CYAN}{display.BOLD}{team:<20}{display.RESET}  {len(members)} people{oncall_str}")
    print()
    return 0


def cmd_add(args) -> int:
    """Interactively add a new contact."""
    print(f"{display.BOLD}Adding new contact (press Enter to skip optional fields){display.RESET}\n")

    def prompt(label: str, required: bool = False, default: str = "") -> str:
        star = "*" if required else " "
        hint = f" [{default}]" if default else ""
        while True:
            val = input(f"  {star} {label}{hint}: ").strip()
            if not val and default:
                return default
            if val or not required:
                return val
            print("    (required)")

    contact = {
        "name":   prompt("Name",        required=True),
        "role":   prompt("Role",        required=True),
        "team":   prompt("Team",        required=True),
        "phone":  prompt("Phone"),
        "slack":  prompt("Slack handle (e.g. @alice)"),
        "email":  prompt("Email"),
        "oncall": prompt("On-call? [y/N]", default="n").lower().startswith("y"),
        "notes":  prompt("Notes (one line)"),
    }
    # strip empty optional fields
    contact = {k: v for k, v in contact.items() if v != "" or k in ("name", "role", "team", "oncall")}

    contacts = store.load_contacts()
    contacts.append(contact)
    store.save_contacts(contacts)
    display.ok(f"Added {contact['name']} → {store.contacts_path()}")
    return 0


def cmd_set_oncall(args) -> int:
    """Mark one or more people as on-call (clears previous on-call flags first if --replace)."""
    contacts = store.load_contacts()
    query = " ".join(args.name).lower()
    matched = [c for c in contacts if query in c.get("name", "").lower()]

    if not matched:
        display.err(f"No contact matching '{query}'.")
        return 1

    if getattr(args, "replace", False):
        for c in contacts:
            c["oncall"] = False

    for c in matched:
        c["oncall"] = True
        display.ok(f"Marked {c['name']} as ON-CALL")

    store.save_contacts(contacts)
    return 0


def cmd_clear_oncall(args) -> int:
    """Remove on-call flag from everyone (or a specific person)."""
    contacts = store.load_contacts()

    if args.name:
        query = " ".join(args.name).lower()
        targets = [c for c in contacts if query in c.get("name", "").lower()]
        if not targets:
            display.err(f"No contact matching '{query}'.")
            return 1
        for c in targets:
            c["oncall"] = False
            display.ok(f"Cleared on-call for {c['name']}")
    else:
        for c in contacts:
            c["oncall"] = False
        display.ok("Cleared on-call for all contacts.")

    store.save_contacts(contacts)
    return 0


def cmd_import(args) -> int:
    """Import contacts from a CSV or TOML file."""
    path = Path(args.file)
    if not path.exists():
        display.err(f"File not found: {path}")
        return 1

    suffix = path.suffix.lower()
    contacts = store.load_contacts()
    added = 0

    if suffix == ".toml":
        import tomllib
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        new_contacts = data.get("contact", [])
        contacts.extend(new_contacts)
        added = len(new_contacts)

    elif suffix == ".csv":
        text = path.read_text(encoding="utf-8")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            c = {k.strip().lower(): v.strip() for k, v in row.items() if v.strip()}
            if "oncall" in c:
                c["oncall"] = c["oncall"].lower() in ("true", "yes", "1", "y")
            contacts.append(c)
            added += 1

    else:
        display.err(f"Unsupported format: {suffix}. Use .toml or .csv")
        return 1

    store.save_contacts(contacts)
    display.ok(f"Imported {added} contacts from {path}")
    display.info(f"Total contacts: {len(contacts)}")
    return 0


def cmd_export(args) -> int:
    """Export contacts to CSV."""
    contacts = store.load_contacts()
    if not contacts:
        display.warn("No contacts to export.")
        return 1

    fields = ["name", "role", "team", "phone", "slack", "email", "oncall", "notes"]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for c in contacts:
        row = {f: c.get(f, "") for f in fields}
        writer.writerow(row)

    dest = args.output if args.output else "-"
    if dest == "-":
        print(out.getvalue(), end="")
    else:
        Path(dest).write_text(out.getvalue(), encoding="utf-8")
        display.ok(f"Exported {len(contacts)} contacts to {dest}")
    return 0


def cmd_sync(args) -> int:
    """Fetch fresh contacts from a URL or network path (requires connectivity)."""
    cfg = store.load_config()
    sync_cfg = cfg.get("sync", {})

    url = getattr(args, "url", None) or sync_cfg.get("url", "")
    src_path = getattr(args, "path", None) or sync_cfg.get("path", "")

    if not url and not src_path:
        display.err("No sync source configured.")
        display.info(f"Set 'url' or 'path' in [sync] section of {store.config_path()}")
        display.info("Or pass a URL directly: fff sync https://...")
        return 1

    display.info("Syncing contacts (network required for URL sync)...")

    try:
        if url:
            req = urllib.request.urlopen(url, timeout=10)
            content = req.read().decode("utf-8")
        else:
            content = Path(src_path).read_text(encoding="utf-8")
    except urllib.error.URLError as e:
        display.err(f"Network error: {e}")
        display.warn("Continuing with local contacts.")
        return 1
    except OSError as e:
        display.err(f"Could not read {src_path}: {e}")
        return 1

    # Write raw to contacts.toml (it's valid TOML already)
    store.ensure_dir()
    store.contacts_path().write_text(content, encoding="utf-8")

    import tomllib
    data = tomllib.loads(content)
    count = len(data.get("contact", []))
    display.ok(f"Synced {count} contacts.")
    return 0


def cmd_init(args) -> int:
    """Initialise ~/.fff/ with example contacts."""
    fresh = store.init_if_needed()
    if fresh:
        display.ok(f"Initialised {store._fff_dir()}/")
        display.info(f"Contacts file: {store.contacts_path()}")
        display.info(f"Config file:   {store.config_path()}")
        display.info("Edit contacts.toml to add your team, then run: fff list")
    else:
        display.warn(f"{store._fff_dir()} already exists.")
        display.info(f"Contacts: {store.contacts_path()}")
    return 0


def cmd_where(args) -> int:
    """Print the path to the contacts file (for scripts / editors)."""
    print(store.contacts_path())
    return 0


def cmd_edit(args) -> int:
    """Open contacts.toml in $EDITOR."""
    store.init_if_needed()
    editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "vi"))
    path = str(store.contacts_path())
    display.info(f"Opening {path} with {editor}")
    os.execvp(editor, [editor, path])
    return 0  # unreachable after execvp
