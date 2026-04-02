# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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

[0.1.1]: https://github.com/cansarigol/mailmap-checker/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/cansarigol/mailmap-checker/releases/tag/v0.1.0
