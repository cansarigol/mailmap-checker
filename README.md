# mailmap-checker

[![PyPI version](https://img.shields.io/pypi/v/mailmap-checker)](https://pypi.org/project/mailmap-checker/)
[![Python versions](https://img.shields.io/pypi/pyversions/mailmap-checker)](https://pypi.org/project/mailmap-checker/)
[![CI](https://github.com/cansarigol/mailmap-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/cansarigol/mailmap-checker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A pre-commit hook that detects unmapped Git identities by comparing your `.mailmap` against the full commit history. It groups authors and committers by email address and email local-part so duplicates are caught even across domain changes.

Follows the [gitmailmap](https://git-scm.com/docs/gitmailmap) specification: all four mapping formats are supported, and both names and emails are matched case-insensitively.

## How it works

The checker scans `git log` for all unique author **and committer** identities and groups them using two rules:

**Rule 1 — Same email (case-insensitive)**

Identities that share the exact same email address are the same person.

```
Alice Johnson <alice@acme.com>
alice.j       <alice@acme.com>   ← same email, grouped together
```

**Rule 2 — Same email local-part (different domain)**

Identities whose email local-part (the part before `@`) matches are likely the same person who changed companies or used a different address. Local-parts shorter than 8 characters are automatically skipped to reduce false positives.

```
Alice Johnson <alice.johnson@acme.com>
Alice Johnson <alice.johnson@oldcorp.com>    ← same local-part, grouped
Alice J       <alice.johnson@personal.net>   ← same local-part, grouped
```

Once groups are built, the checker looks for identities that are **not mapped** in `.mailmap`. If a group has more than one identity and any of them is missing from the file, the hook fails and reports the gap.

### Example

Given these three identities in git history and an empty `.mailmap`:

```
Alice Johnson <alice.johnson@acme.com>
Alice Johnson <alice.johnson@oldcorp.com>
Alice J       <alice.johnson@personal.net>
```

`mailmap-checker check` detects the gap:

```
Found 2 unmapped identities in 1 group:

  Canonical: Alice J <alice.johnson@personal.net>
    - Alice Johnson <alice.johnson@acme.com>
    - Alice Johnson <alice.johnson@oldcorp.com>
```

`mailmap-checker fix --dry-run` suggests entries to add:

```
Suggested .mailmap entries:

  Alice J <alice.johnson@personal.net> Alice Johnson <alice.johnson@acme.com>
  Alice J <alice.johnson@personal.net> Alice Johnson <alice.johnson@oldcorp.com>
```

> **Note:** When no `.mailmap` exists, the tool picks the alphabetically first identity as the canonical. In this case it chose `Alice J <alice.johnson@personal.net>`, but the actual preferred identity is likely `Alice Johnson <alice.johnson@acme.com>`. After running `fix`, open `.mailmap` and swap the canonical if needed:
>
> ```
> Alice Johnson <alice.johnson@acme.com> Alice Johnson <alice.johnson@oldcorp.com>
> Alice Johnson <alice.johnson@acme.com> Alice J <alice.johnson@personal.net>
> ```

### Disabling local-part matching

If Rule 2 produces false positives on very large repositories, disable it with `--no-local-part-matching`.

## Installation

### Pre-commit hook (recommended)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/cansarigol/mailmap-checker
    rev: ""  # run: pre-commit autoupdate
    hooks:
      - id: mailmap-check
```

Then run `pre-commit autoupdate` to pin the latest release.

#### Available hooks

| Hook ID | Description |
|---|---|
| `mailmap-check` | Fail if any identity is missing from `.mailmap` |
| `mailmap-fix` | Automatically add missing entries to `.mailmap` |
| `mailmap-fix-dry-run` | Preview suggested entries without modifying the file |

### Standalone

```bash
pip install mailmap-checker
```

## Usage

### `check`

Scan all Git authors and committers and exit non-zero if any identity is missing from `.mailmap`.

```bash
mailmap-checker check
```

### `init`

Create a `.mailmap` file (if it does not exist) and run a full check.

```bash
mailmap-checker init
```

### `fix`

Preview or apply suggested `.mailmap` entries. New entries are inserted in **sorted order** (not appended at the end), and canonical groups are separated by blank lines.

The canonical identity for each group is chosen by preferring names that look like real person names (e.g. `Alice Johnson`) over usernames (`alicej`), git config artifacts (`--global`), or handle-style names (`@username`).

```bash
# Preview
mailmap-checker fix --dry-run

# Apply
mailmap-checker fix
```

### Common options

| Flag | Description |
|---|---|
| `--mailmap <path>` | Custom `.mailmap` file path (default: `git config mailmap.file`, then `.mailmap`) |
| `--git-dir <path>` | Path to git repository (default: current directory) |
| `--no-local-part-matching` | Disable grouping by email local-part across domains |

## Contributing

```bash
git clone https://github.com/cansarigol/mailmap-checker.git
cd mailmap-checker
uv sync
uv run poe setup   # installs pre-commit and commit-msg hooks
uv run poe check    # lint + security + tests
```

Commits must follow [Conventional Commits](https://www.conventionalcommits.org/) with a required scope (e.g. `feat(cli): add --verbose flag`).

## License

[MIT](LICENSE)
