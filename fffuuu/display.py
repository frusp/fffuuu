"""
Output formatting for fffuuu.
Designed to be readable at 3am on a terminal with bad contrast.
No external deps (no rich, no colorama).
Falls back to plain text if not a TTY.
"""
import sys
import os
import shutil


def _use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FFF_NO_COLOR"):
        return False
    return sys.stdout.isatty()


USE_COLOR = _use_color()

# ANSI codes
RESET  = "\033[0m"  if USE_COLOR else ""
BOLD   = "\033[1m"  if USE_COLOR else ""
DIM    = "\033[2m"  if USE_COLOR else ""
RED    = "\033[91m" if USE_COLOR else ""
YELLOW = "\033[93m" if USE_COLOR else ""
GREEN  = "\033[92m" if USE_COLOR else ""
CYAN   = "\033[96m" if USE_COLOR else ""
WHITE  = "\033[97m" if USE_COLOR else ""


def terminal_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns


def hr(char="─") -> str:
    return char * min(terminal_width(), 72)


def print_contact(c: dict, verbose: bool = False) -> None:
    name  = c.get("name",  "?")
    role  = c.get("role",  "")
    team  = c.get("team",  "")
    phone = c.get("phone", "")
    slack = c.get("slack", "")
    email = c.get("email", "")
    oncall = c.get("oncall", False)
    notes  = c.get("notes", "")

    oncall_tag = f" {GREEN}{BOLD}[ON-CALL]{RESET}" if oncall else ""

    print(f"{BOLD}{WHITE}{name}{RESET}{oncall_tag}")
    print(f"  {DIM}role :{RESET}  {role}   {DIM}team:{RESET} {CYAN}{team}{RESET}")

    if phone:
        print(f"  {DIM}phone:{RESET}  {YELLOW}{BOLD}{phone}{RESET}")
    if slack:
        print(f"  {DIM}slack:{RESET}  {slack}")
    if email:
        print(f"  {DIM}email:{RESET}  {email}")
    if verbose and notes:
        print(f"  {DIM}notes:{RESET}  {DIM}{notes}{RESET}")


def print_header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{text}{RESET}")
    print(hr())


def print_section(team: str, contacts: list[dict], verbose: bool = False) -> None:
    print_header(f"team: {team.upper()}")
    for c in contacts:
        print_contact(c, verbose=verbose)
        print()


def print_oncall_banner() -> None:
    w = min(terminal_width(), 72)
    print(RED + "█" * w + RESET)
    print(f"{RED}{BOLD}  ███████ ███████ ██    ██     ██████  {RESET}")
    print(f"{RED}{BOLD}  ██      ██      ██    ██    ██    ██ {RESET}")
    print(f"{RED}{BOLD}  ███████ █████   ██    ██    ██    ██ {RESET}")
    print(f"{RED}{BOLD}       ██ ██       ██  ██     ██    ██ {RESET}")
    print(f"{RED}{BOLD}  ███████ ███████   ████       ██████  {RESET}")
    print(RED + "█" * w + RESET)
    print()


def err(msg: str) -> None:
    print(f"{RED}[fff] {msg}{RESET}", file=sys.stderr)


def ok(msg: str) -> None:
    print(f"{GREEN}[fff] {msg}{RESET}")


def warn(msg: str) -> None:
    print(f"{YELLOW}[fff] {msg}{RESET}")


def info(msg: str) -> None:
    print(f"{DIM}[fff] {msg}{RESET}")
