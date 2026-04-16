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

Identities whose email local-part (the part before `@`) **and name** match are likely the same person who changed companies or used a different address. Local-parts shorter than 8 characters are automatically skipped to reduce false positives.

```
Alice Johnson <alice.johnson@acme.com>
Alice Johnson <alice.johnson@oldcorp.com>    ← same local-part + name, grouped
```

Once groups are built, the checker looks for identities that are **not mapped** in `.mailmap`. If a group has more than one identity and any of them is missing from the file, the hook fails and reports the gap.

### Example

Given these identities in git history and an empty `.mailmap`:

```
Alice Johnson <alice.johnson@acme.com>
Alice Johnson <alice.johnson@oldcorp.com>
alice.j       <alice.johnson@acme.com>
```

`mailmap-checker check` detects the gap:

```
  Canonical: Alice Johnson <alice.johnson@acme.com> (42 commits)
    - Alice Johnson <alice.johnson@oldcorp.com> (15 commits)
    - alice.j <alice.johnson@acme.com> (3 commits)

Found 2 unmapped identities in 1 group (canonical chosen by name heuristic
— prefers names that start with a letter and contain a space
(e.g. 'Jane Doe' over 'jdoe')).

Tip: Use --by-commit-count to choose canonical by highest commit count.
```

`mailmap-checker fix --dry-run` suggests entries to add:

```
Suggested .mailmap entries (canonical chosen by name heuristic):

  Alice Johnson <alice.johnson@acme.com> Alice Johnson <alice.johnson@oldcorp.com>
  Alice Johnson <alice.johnson@acme.com> alice.j <alice.johnson@acme.com>
```

### Disabling local-part matching

If Rule 2 produces false positives on very large repositories, disable it with `--no-local-part-matching`.

### Mailmap source resolution

Just like Git itself, `mailmap-checker` reads and merges entries from multiple sources:

1. **`--mailmap <path>`** — explicit path (highest priority)
2. **`mailmap.file`** Git config — `git config mailmap.file` (used when no explicit `--mailmap` is given)
3. **`.mailmap`** in the repository root (default fallback)
4. **`mailmap.blob`** Git config — `git config mailmap.blob` (e.g. `HEAD:.mailmap`, read from a Git object)

Entries from all applicable sources are merged before checking. This means a project that stores mappings in a committed blob, a separate file, or the default `.mailmap` will all be handled correctly.

### Shared emails (different people, same address)

When two different people share the same email address (e.g. a generic workstation account), the checker automatically detects this from the `.mailmap` file. If the same email is mapped to different canonical identities, the checker knows they are different people and does not group them together.

```
# .mailmap — two different people share user@workstation.local
Alice Johnson <alice@acme.com> admin <user@workstation.local>
Bob Smith <bob@acme.com> Bob Smith <user@workstation.local>
```

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
| `mailmap-normalize` | Deduplicate, collapse to Format 1, and sort entries |

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

Preview or apply suggested `.mailmap` entries. New entries are inserted in **sorted order** and the existing blank-line style of the file is preserved (separator-style files keep separators; compact files stay compact).

The canonical identity for each group is chosen by a **name heuristic** — preferring names that look like real person names (e.g. `Alice Johnson`) over usernames (`alicej`), git config artifacts (`--global`), or handle-style names (`@username`). Use `--by-commit-count` to choose the identity with the most commits instead.

```bash
# Preview
mailmap-checker fix --dry-run

# Apply
mailmap-checker fix

# Choose canonical by commit count
mailmap-checker fix --by-commit-count
```

### `normalize`

Deduplicate, collapse same-email aliases to [Format 1](https://git-scm.com/docs/gitmailmap) (`Proper Name <email>`), and sort entries alphabetically. Does not require git — operates only on the `.mailmap` file.

```bash
# Preview
mailmap-checker normalize --dry-run

# Apply
mailmap-checker normalize
```

### Common options

| Flag | Description |
|---|---|
| `--mailmap <path>` | Custom `.mailmap` file path (default: `git config mailmap.file`, then `.mailmap`) |
| `--git-dir <path>` | Path to git repository (default: current directory) |
| `--no-local-part-matching` | Disable grouping by email local-part across domains |
| `--by-commit-count` | Choose canonical identity by highest commit count instead of name heuristic |

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
