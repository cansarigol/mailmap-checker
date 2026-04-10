import argparse
import sys
from pathlib import Path

from .checker import find_gaps
from .fixer import apply_fixes, generate_entries
from .git import get_identities, get_mailmap_file_config
from .parser import parse_mailmap

_DEFAULT_MAILMAP = ".mailmap"
_MAILMAP_HEADER = "# Canonical identity → historical aliases\n"


def main() -> None:
    raise SystemExit(run())


def run(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not hasattr(args, "handler"):
        args.parser.print_help()
        return 1
    return args.handler(args)


def _resolve_paths(args: argparse.Namespace) -> tuple[Path, Path | None]:
    git_dir = Path(args.git_dir) if args.git_dir else None
    if args.mailmap != _DEFAULT_MAILMAP:
        return Path(args.mailmap), git_dir
    configured = get_mailmap_file_config(git_dir)
    if configured:
        return Path(configured), git_dir
    if git_dir:
        return git_dir / _DEFAULT_MAILMAP, git_dir
    return Path(_DEFAULT_MAILMAP), git_dir


def _handle_check(args: argparse.Namespace) -> int:
    mailmap_path, git_dir = _resolve_paths(args)
    entries = parse_mailmap(mailmap_path)
    identities = get_identities(git_dir)
    gaps = find_gaps(identities, entries)
    if not gaps:
        sys.stdout.write("All identities are properly mapped.\n")
        return 0
    _print_gaps(gaps)
    return 1


def _handle_init(args: argparse.Namespace) -> int:
    mailmap_path, _ = _resolve_paths(args)
    if mailmap_path.exists():
        sys.stdout.write(f"'{mailmap_path}' already exists.\n")
    else:
        mailmap_path.write_text(_MAILMAP_HEADER, encoding="utf-8")
        sys.stdout.write(f"Created '{mailmap_path}'.\n")
    return _handle_check(args)


def _handle_fix(args: argparse.Namespace) -> int:
    mailmap_path, git_dir = _resolve_paths(args)
    entries = parse_mailmap(mailmap_path)
    identities = get_identities(git_dir)
    gaps = find_gaps(identities, entries)
    if not gaps:
        sys.stdout.write("No fixes needed.\n")
        return 0
    new_entries = generate_entries(gaps)
    if args.dry_run:
        sys.stdout.write("Suggested .mailmap entries:\n\n")
        for entry in new_entries:
            sys.stdout.write(f"  {entry}\n")
        return 1
    apply_fixes(mailmap_path, new_entries)
    sys.stdout.write(f"Added {len(new_entries)} entries to '{mailmap_path}'.\n")
    return 0


def _print_gaps(gaps: list) -> None:
    total_missing = sum(len(g.missing_entries) for g in gaps)
    sys.stdout.write(
        f"Found {total_missing} unmapped identities in {len(gaps)} groups:\n\n"
    )
    for group in gaps:
        sys.stdout.write(f"  Canonical: {group.canonical}\n")
        for identity in group.missing_entries:
            sys.stdout.write(f"    - {identity}\n")
    sys.stdout.write(
        "\nRun 'mailmap-checker fix --dry-run' to see suggested entries,\n"
        "or use the 'mailmap-fix-dry-run' pre-commit hook.\n"
    )


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--mailmap", default=_DEFAULT_MAILMAP, help="Path to .mailmap file"
    )
    parser.add_argument(
        "--git-dir",
        default=None,
        help="Path to git repository (default: current directory)",
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mailmap-checker",
        description="Check and maintain .mailmap completeness.",
    )
    parser.set_defaults(parser=parser)
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser(
        "check", help="Check all identities against .mailmap"
    )
    _add_common_args(check_parser)
    check_parser.set_defaults(handler=_handle_check)

    init_parser = subparsers.add_parser(
        "init", help="Create .mailmap and run initial check"
    )
    _add_common_args(init_parser)
    init_parser.set_defaults(handler=_handle_init)

    fix_parser = subparsers.add_parser("fix", help="Generate and apply .mailmap fixes")
    _add_common_args(fix_parser)
    fix_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show suggested entries without applying",
    )
    fix_parser.set_defaults(handler=_handle_fix)

    return parser.parse_args(argv)
