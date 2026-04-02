from pathlib import Path

from .models import IdentityGroup


def generate_entries(gaps: list[IdentityGroup]) -> list[str]:
    lines: list[str] = []
    for group in gaps:
        if not group.canonical:
            continue
        lines.extend(
            f"{group.canonical} {identity}" for identity in group.missing_entries
        )
    return lines


def apply_fixes(mailmap_path: Path, new_entries: list[str]) -> None:
    lines = _read_lines(mailmap_path)
    grouped = _group_by_canonical(new_entries)
    insertions, appends = _plan_insertions(lines, grouped)
    _apply_insertions(lines, insertions)
    _apply_appends(lines, appends)
    mailmap_path.write_text("".join(lines), encoding="utf-8")


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def _extract_canonical_prefix(entry: str) -> str:
    end = entry.index(">")
    return entry[: end + 1]


def _group_by_canonical(entries: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for entry in entries:
        prefix = _extract_canonical_prefix(entry)
        grouped.setdefault(prefix, []).append(entry)
    return grouped


def _find_last_match(lines: list[str], canonical_prefix: str) -> int | None:
    last_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith(canonical_prefix):
            last_idx = i + 1
    return last_idx


def _plan_insertions(
    lines: list[str],
    grouped: dict[str, list[str]],
) -> tuple[list[tuple[int, list[str]]], list[str]]:
    insertions: list[tuple[int, list[str]]] = []
    appends: list[str] = []
    for canonical_prefix, entries in grouped.items():
        insert_at = _find_last_match(lines, canonical_prefix)
        if insert_at is not None:
            insertions.append((insert_at, entries))
        else:
            appends.extend(entries)
    return insertions, appends


def _apply_insertions(
    lines: list[str],
    insertions: list[tuple[int, list[str]]],
) -> None:
    for idx, entries in sorted(insertions, reverse=True):
        for i, entry in enumerate(entries):
            lines.insert(idx + i, entry + "\n")


def _apply_appends(lines: list[str], appends: list[str]) -> None:
    if not appends:
        return
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    if lines:
        lines.append("\n")
    lines.extend(entry + "\n" for entry in appends)
