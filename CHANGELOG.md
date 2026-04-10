# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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

[0.2.1]: https://github.com/cansarigol/mailmap-checker/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/cansarigol/mailmap-checker/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/cansarigol/mailmap-checker/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/cansarigol/mailmap-checker/releases/tag/v0.1.0
