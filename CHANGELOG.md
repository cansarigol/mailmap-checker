# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-04-02

### Added

- `check` command — scans Git history and exits non-zero when unmapped identities are found.
- `init` command — creates a `.mailmap` file and runs a full check.
- `fix` command — generates suggested `.mailmap` entries (`--dry-run` to preview).
- Identity grouping via Union-Find: same email (case-insensitive) and same email local-part across domains.
- Pre-commit hook integration (`mailmap-check`).

[0.1.0]: https://github.com/cansarigol/mailmap-checker/releases/tag/v0.1.0
