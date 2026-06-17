# Changelog

## 0.1.0 (2026-06-17)

Initial release.

- Offline-first SRE emergency contact directory
- Data stored as human-readable TOML in `~/.fff/contacts.toml`
- Commands: `oncall`, `list`, `team`, `teams`, `find`, `add`, `set-oncall`,
  `clear-oncall`, `import`, `export`, `sync`, `edit`, `where`, `init`
- Import from `.toml` or `.csv`
- Export to CSV
- Optional sync from URL or network path
- ANSI colour output with `NO_COLOR` / `FFF_DIR` env var support
- Zero runtime dependencies (Python 3.11+ stdlib only)
- Installed as three aliases: `fffuuu`, `fck`, `sev`
