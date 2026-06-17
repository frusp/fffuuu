# fffuuu

**Offline-first SRE emergency contact directory.**
-Inspired by a talk by Alberto Massidda.

> When your infra is on fire, Confluence won't load, PagerDuty is down,
> and Slack is the thing that's broken — this still works.
> Because it's a local file.

Installed as **three aliases** — pick whichever comes out of your fingers at 3am:

```
fffuuu    # the canonical name
fck       # when you need to express yourself
sev       # when you're being professional about it
```

```
$ fck oncall

████████████████████████████████████████████████████████████████████████
  ███████ ███████ ██    ██     ██████
  ██      ██      ██    ██    ██    ██
  ███████ █████   ██    ██    ██    ██
       ██ ██       ██  ██     ██    ██
  ███████ ███████   ████       ██████
████████████████████████████████████████████████████████████████████████

── ON-CALL NOW (1 person) ───────────────────────────────────────────────

Ada Lovelace  [ON-CALL]
  role :  Senior SRE   team: platform
  phone:  +1-555-000-0001
  slack:  @ada
  email:  ada@example.com
```

---

## Why

SEV-0 tooling should have **zero network dependencies**. Every other
contact/escalation tool (PagerDuty, OpsGenie, Slack, your wiki) can
itself be the thing that's down. `fck` reads a local TOML file and
prints phone numbers. That's it.

Inspired by a talk by Alberto Massidda about an internal tool with the same philosophy.

---

## Install

```bash
pip install fffuuu
```

Or from source:

```bash
git clone https://github.com/frusp/fffuuu
cd fffuuu
pip install -e .
```

**Requires Python 3.11+. Zero runtime dependencies.**

After install, all three commands are available: `fffuuu`, `fck`, `sev`.

---

## Quickstart

```bash
fck init              # creates ~/.fff/ with example contacts
fck oncall            # who's on the hook right now  ← the 3am command
fck list              # everyone
fck list --by-team    # grouped by team
fck team platform     # one team
fck find alice        # search everything
fck teams             # list all teams with on-call counts
```

---

## Commands

| Command | What it does |
|---|---|
| `fck` | on-call if anyone is set, else list all |
| `fck oncall` | current on-call contacts with big red banner |
| `fck list` | all contacts |
| `fck list -t` | all contacts, grouped by team |
| `fck team <name>` | contacts for one team (partial match ok) |
| `fck teams` | all teams + on-call count |
| `fck find <query>` | full-text search across all fields |
| `fck add` | add a contact interactively |
| `fck set-oncall <name>` | mark someone as on-call |
| `fck set-oncall <name> --replace` | swap on-call (clears everyone else first) |
| `fck clear-oncall` | clear on-call for everyone |
| `fck clear-oncall <name>` | clear one person |
| `fck import <file>` | import from `.toml` or `.csv` |
| `fck export` | export to CSV (stdout or `-o file`) |
| `fck sync [url]` | pull fresh contacts from URL or network path |
| `fck edit` | open contacts.toml in `$EDITOR` |
| `fck where` | print path to contacts.toml (useful in scripts) |
| `fck init` | initialise `~/.fff/` with example contacts |

All read commands accept `-v` / `--verbose` to show the `notes` field.

Replace `fck` with `sev` or `fffuuu` — all three are identical.

---

## Data format

`~/.fff/contacts.toml` — edit it directly, it's just text:

```toml
# fffuuu contacts - human-readable emergency contact directory

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
notes   = "Escalation for platform. Will answer at any hour for SEV-0."
```

All fields except `name` are optional. Add custom fields freely — they're
preserved in the file and ignored by the tool.

---

## Keeping the team in sync

The file is just a file. A few options:

**Git repo** (recommended): put `contacts.toml` in an internal git repo.
Team members clone it once, then `git pull` keeps it fresh. History and
diffs come for free — you'll know who changed what and when.

**HTTP sync**: host the file anywhere internally and pull it on demand:
```bash
fck sync https://internal.company.com/sre/contacts.toml
# or set it once in ~/.fff/config.toml and just run:
fck sync
```

**Shared filesystem**:
```bash
fck sync /mnt/shared/sre/contacts.toml
```

**Cron** (combine with any of the above):
```
0 */4 * * *  fck sync   # refresh every 4 hours when network is up
```

`config.toml`:
```toml
[sync]
url = "https://your-internal-url/contacts.toml"
# or:
# path = "/mnt/shared/sre/contacts.toml"
```

---

## CSV import

```csv
name,role,team,phone,slack,email,oncall,notes
Alice Smith,Senior SRE,platform,+1-555-111-2222,@alice,alice@co.com,true,Primary on-call
Bob Jones,SRE,networking,+1-555-333-4444,@bob,bob@co.com,false,BGP specialist
```

```bash
fck import team.csv
```

---

## Environment variables

| Variable | Effect |
|---|---|
| `FFF_DIR` | Override data directory (default: `~/.fff`) |
| `NO_COLOR` | Disable ANSI colour output |
| `EDITOR` / `VISUAL` | Editor used by `fck edit` |

---

## Publishing checklist (for maintainers)

```bash
# build
pip install build twine
python -m build

# check
twine check dist/*

# upload to TestPyPI first
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ fffuuu

# upload to PyPI
twine upload dist/*
```

---

## AI development

This project is developed with AI coding agents. [`handoff.AI`](handoff.AI)
is the context file that every agent reads at the start of a session and
updates at the end. It contains the architecture, constraints, decisions, and
current state of the project — everything a new agent needs to pick up where
the last one left off.

If you're an AI agent working on this repo: **start with `handoff.AI`**.

## License

MIT — see [LICENSE](LICENSE).
