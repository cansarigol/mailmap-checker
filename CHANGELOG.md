# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.5] - 2026-04-13

### Added

- `normalize` command: deduplicate, collapse same-email aliases to Format 1, and sort `.mailmap` entries alphabetically. Preserves comments, blank-line style, and trailing newline. Supports `--dry-run`.
- `mailmap-normalize` pre-commit hook.
- **Mailmap source merging** (matching Git behavior): entries are now read from all applicable sources — `--mailmap` / `mailmap.file` config, root `.mailmap`, and `mailmap.blob` config — and merged before checking. Previously only a single file was read.

## [0.3.4] - 2026-04-12

### Fixed

- **Format 1 mailmap entries (`Proper Name <email>`) now correctly cover all identities with that email**, regardless of the committer name. Previously these were treated as named aliases, causing widespread false positives on repositories that use Format 1 extensively.

## [0.3.3] - 2026-04-12

### Added

- `--by-commit-count` flag: choose canonical identity by highest commit count instead of name heuristic.
- Commit counts are now shown next to each identity in check and fix output.
- Strategy description in output explains how the canonical identity was chosen, with a tip to try `--by-commit-count`.

### Fixed

- Local-part matching now requires the name to match as well, preventing false positives where different people share a common local-part (e.g. `jonathan@`).
- Fixer now respects the existing `.mailmap` blank-line style: files that use blank-line separators between groups keep that format; compact files stay compact.

## [0.3.0] - 2026-04-10

### Added

- Sorted insertion: new `.mailmap` entries are now inserted in alphabetical order instead of appended at the end, keeping the file sorted.
- Blank line separators between canonical groups when the existing `.mailmap` uses that style.
- Smarter canonical selection: prefers real names (e.g. `Alice Johnson`) over git config artifacts (`--global`), usernames (`alicej`), or handle-style names (`@username`).

## [0.2.1] - 2026-04-10

### Added

- `--no-local-part-matching` flag to disable local-part grouping.
- Minimum local-part length filter (8 characters): short local-parts like `admin@`, `mail@`, `alex@` are now ignored to prevent false positives on large repositories.

## [0.2.0] - 2026-04-10

### Added

- Committer identity support: scans both author (`%an`/`%ae`) and committer (`%cn`/`%ce`) identities from Git history.
- `mailmap.file` Git config support: automatically reads the `mailmap.file` configuration when no explicit `--mailmap` is given.
- Python 3.14 support.

### Fixed

- Format 2/3 false positives: email-only alias entries (`<proper@email> <commit@email>` and `Name <proper@email> <commit@email>`) no longer report already-mapped identities as missing.
- Case-insensitive name matching: alias and canonical lookups now compare names case-insensitively, per the [gitmailmap](https://git-scm.com/docs/gitmailmap) specification.

## [0.1.1] - 2026-04-02

### Added

- `mailmap-fix` and `mailmap-fix-dry-run` pre-commit hooks.

### Fixed

- Windows compatibility: explicit UTF-8 encoding for `.mailmap` read/write operations.
- Windows compatibility: cross-platform path handling in `--git-dir`.
- GitHub Actions Node.js 20 deprecation warnings (updated to v6).

## [0.1.0] - 2026-04-02

### Added

- `check` command — scans Git history and exits non-zero when unmapped identities are found.
- `init` command — creates a `.mailmap` file and runs a full check.
- `fix` command — generates suggested `.mailmap` entries (`--dry-run` to preview).
- Identity grouping via Union-Find: same email (case-insensitive) and same email local-part across domains.
- Pre-commit hook integration (`mailmap-check`).

[0.3.5]: https://github.com/cansarigol/mailmap-checker/compare/v0.3.4...v0.3.5
[0.3.4]: https://github.com/cansarigol/mailmap-checker/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/cansarigol/mailmap-checker/compare/v0.3.2...v0.3.3
[0.3.1]: https://github.com/cansarigol/mailmap-checker/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/cansarigol/mailmap-checker/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/cansarigol/mailmap-checker/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/cansarigol/mailmap-checker/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/cansarigol/mailmap-checker/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/cansarigol/mailmap-checker/releases/tag/v0.1.0
