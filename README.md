# mailmap-checker

[![PyPI version](https://img.shields.io/pypi/v/mailmap-checker)](https://pypi.org/project/mailmap-checker/)
[![Python versions](https://img.shields.io/pypi/pyversions/mailmap-checker)](https://pypi.org/project/mailmap-checker/)
[![CI](https://github.com/cansarigol/mailmap-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/cansarigol/mailmap-checker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A pre-commit hook that detects unmapped Git identities by comparing your `.mailmap` against the full commit history. It groups authors by email address and email local-part so duplicates are caught even across domain changes.

## How it works

The checker scans `git log` for all unique author identities and groups them using two rules:

**Rule 1 — Same email (case-insensitive)**

Identities that share the exact same email address are the same person.

```
Alice Johnson <alice@acme.com>
alice.j       <alice@acme.com>   ← same email, grouped together
```

**Rule 2 — Same email local-part (different domain)**

Identities whose email local-part (the part before `@`) matches are likely the same person who changed companies or used a different address.

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

> **Note:** When no `.mailmap` exists, the tool picks the alphabetically first identity as the canonical. In this case it chose `Alice J <alice.johnson@personal.net>`, but the actual preferred identity is likely `Alice Johnson <alice.johnson@acme.com>`. The `.mailmap` format places the canonical (left) and the alias (right) on each line. After running `fix`, open `.mailmap` and swap the canonical if needed:
>
> ```
> Alice Johnson <alice.johnson@acme.com> Alice Johnson <alice.johnson@oldcorp.com>
> Alice Johnson <alice.johnson@acme.com> Alice J <alice.johnson@personal.net>
> ```

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

### Standalone

```bash
pip install mailmap-checker
```

## Usage

### `check`

Scan all Git authors and exit non-zero if any identity is missing from `.mailmap`.

```bash
mailmap-checker check
```

### `init`

Create a `.mailmap` file (if it does not exist) and run a full check.

```bash
mailmap-checker init
```

### `fix`

Preview or apply suggested `.mailmap` entries.

```bash
# Preview
mailmap-checker fix --dry-run

# Apply
mailmap-checker fix
```

All commands accept `--mailmap <path>` to use a custom file path.

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
