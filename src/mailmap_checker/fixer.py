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
    matched, unmatched = _classify_groups(lines, grouped)
    _insert_matched(lines, matched)
    _insert_sorted(lines, unmatched)
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


def _classify_groups(
    lines: list[str],
    grouped: dict[str, list[str]],
) -> tuple[list[tuple[int, list[str]]], list[tuple[str, list[str]]]]:
    matched: list[tuple[int, list[str]]] = []
    unmatched: list[tuple[str, list[str]]] = []
    for canonical_prefix, entries in grouped.items():
        insert_at = _find_last_match(lines, canonical_prefix)
        if insert_at is not None:
            matched.append((insert_at, entries))
        else:
            unmatched.append((canonical_prefix, entries))
    return matched, unmatched


def _insert_matched(
    lines: list[str],
    insertions: list[tuple[int, list[str]]],
) -> None:
    for idx, entries in sorted(insertions, reverse=True):
        for i, entry in enumerate(entries):
            lines.insert(idx + i, entry + "\n")


def _has_group_separators(lines: list[str]) -> bool:
    saw_content = False
    saw_blank_after_content = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if saw_content:
                saw_blank_after_content = True
            continue
        if stripped.startswith("#"):
            continue
        if saw_blank_after_content:
            return True
        saw_content = True
    return False


def _find_sorted_position(lines: list[str], canonical_prefix: str) -> int:
    prefix_lower = canonical_prefix.strip().lower()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.lower() > prefix_lower:
            return i
    return len(lines)


def _insert_sorted(
    lines: list[str],
    groups: list[tuple[str, list[str]]],
) -> None:
    if not groups:
        return
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    use_separators = _has_group_separators(lines)
    sorted_groups = sorted(groups, key=lambda g: g[0].lower())
    by_pos: dict[int, list[list[str]]] = {}
    for canonical_prefix, entries in sorted_groups:
        pos = _find_sorted_position(lines, canonical_prefix)
        by_pos.setdefault(pos, []).append(entries)
    for pos in sorted(by_pos, reverse=True):
        block: list[str] = []
        for entries in by_pos[pos]:
            block.extend(entry + "\n" for entry in entries)
        if pos > 0 and pos < len(lines) and not lines[pos - 1].strip():
            block.append("\n")
        elif use_separators and pos == len(lines) and pos > 0:
            block.insert(0, "\n")
        for i, line in enumerate(block):
            lines.insert(pos + i, line)
