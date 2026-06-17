"""
CLI entry point for fffuuu.
Installed as three commands: fffuuu, fck, sev
The invocation name is detected and affects tone only — behaviour is identical.
"""
import argparse
import os
import sys
from pathlib import Path
from . import commands, store, display


def _invocation_name() -> str:
    """Detect which alias was used to invoke us."""
    return Path(sys.argv[0]).name


def _descriptions() -> tuple[str, str]:
    """Return (description, epilog) tuned to the invocation name."""
    name = _invocation_name()

    if name == "fck":
        desc = """\
fck - who do I call when everything is on fire?

  Offline-first SRE emergency contact directory.
  No network needed. No Confluence. No Slack. Just phone numbers.
"""
    elif name == "sev":
        desc = """\
sev - SRE emergency contact directory

  Offline-first. Works during outages. Always.
  Data lives in a local TOML file you can read with cat.
"""
    else:
        desc = """\
fffuuu - offline-first SRE emergency contact directory

  When your infra is on fire and Confluence won't load,
  this still works. Always. Because it's a local file.
"""

    epilog = """\
Data lives in ~/.fff/contacts.toml  (plain TOML, edit it directly)
Config lives in ~/.fff/config.toml

Aliases: fffuuu / fck / sev  (all identical, pick your mood)
Env:     FFF_DIR   override data directory
         NO_COLOR  disable colour output
"""
    return desc, epilog


def build_parser() -> argparse.ArgumentParser:
    name = _invocation_name()
    desc, epilog = _descriptions()

    parser = argparse.ArgumentParser(
        prog=name,
        description=desc,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # list
    p_list = sub.add_parser("list", aliases=["ls"], help="list all contacts")
    p_list.add_argument("-t", "--by-team", action="store_true", help="group by team")
    p_list.add_argument("-v", "--verbose", action="store_true", help="show notes field")
    p_list.set_defaults(func=commands.cmd_list)

    # oncall
    p_oncall = sub.add_parser("oncall", help="show who is on-call RIGHT NOW")
    p_oncall.add_argument("-v", "--verbose", action="store_true", help="show notes field")
    p_oncall.set_defaults(func=commands.cmd_oncall)

    # team
    p_team = sub.add_parser("team", help="show contacts for a team")
    p_team.add_argument("name", help="team name (partial match ok)")
    p_team.add_argument("-v", "--verbose", action="store_true", help="show notes field")
    p_team.set_defaults(func=commands.cmd_team)

    # teams
    p_teams = sub.add_parser("teams", help="list all teams")
    p_teams.set_defaults(func=commands.cmd_teams)

    # find
    p_find = sub.add_parser("find", aliases=["search", "f"], help="search across all fields")
    p_find.add_argument("query", nargs="+", help="search terms")
    p_find.add_argument("-v", "--verbose", action="store_true", help="show notes field")
    p_find.set_defaults(func=commands.cmd_find)

    # add
    p_add = sub.add_parser("add", help="add a contact interactively")
    p_add.set_defaults(func=commands.cmd_add)

    # set-oncall
    p_so = sub.add_parser("set-oncall", help="mark someone as on-call")
    p_so.add_argument("name", nargs="+", help="name (partial match ok)")
    p_so.add_argument("--replace", action="store_true",
                      help="clear all other on-call flags first")
    p_so.set_defaults(func=commands.cmd_set_oncall)

    # clear-oncall
    p_co = sub.add_parser("clear-oncall", help="remove on-call flag")
    p_co.add_argument("name", nargs="*", help="name (leave blank for everyone)")
    p_co.set_defaults(func=commands.cmd_clear_oncall)

    # import
    p_import = sub.add_parser("import", help="import from .toml or .csv file")
    p_import.add_argument("file", help="path to .toml or .csv")
    p_import.set_defaults(func=commands.cmd_import)

    # export
    p_export = sub.add_parser("export", help="export contacts to CSV")
    p_export.add_argument("-o", "--output", metavar="FILE",
                          help="output file (default: stdout)")
    p_export.set_defaults(func=commands.cmd_export)

    # sync
    p_sync = sub.add_parser("sync", help="fetch contacts from URL or network path")
    p_sync.add_argument("url", nargs="?", help="URL or omit to use config.toml setting")
    p_sync.set_defaults(func=commands.cmd_sync)

    # init
    p_init = sub.add_parser("init", help="create ~/.fff/ with example contacts")
    p_init.set_defaults(func=commands.cmd_init)

    # where
    p_where = sub.add_parser("where", help="print path to contacts.toml")
    p_where.set_defaults(func=commands.cmd_where)

    # edit
    p_edit = sub.add_parser("edit", help="open contacts.toml in $EDITOR")
    p_edit.set_defaults(func=commands.cmd_edit)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not hasattr(args, "verbose"):
        args.verbose = False

    if args.command is None:
        contacts = store.load_contacts()
        if not contacts:
            parser.print_help()
            return 0
        oncall = [c for c in contacts if c.get("oncall", False)]
        if oncall:
            return commands.cmd_oncall(args)
        else:
            return commands.cmd_list(args)

    if args.command not in ("init", "where"):
        store.init_if_needed()

    return args.func(args)
