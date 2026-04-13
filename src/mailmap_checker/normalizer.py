from dataclasses import dataclass
from pathlib import Path

from .fixer import has_group_separators
from .models import Identity, MailmapEntry
from .parser import parse_mailmap


@dataclass
class NormalizeStats:
    original_entries: int
    normalized_entries: int
    format1_collapses: int
    duplicates_removed: int


def normalize_file(
    path: Path, *, dry_run: bool = False
) -> tuple[str, bool, NormalizeStats]:
    content = path.read_text(encoding="utf-8")
    has_trailing_newline = content.endswith("\n")
    header = _extract_header(content)
    entries = parse_mailmap(path)
    use_separators = has_group_separators(content.splitlines(keepends=True))
    normalized, stats = normalize_entries(entries)
    lines = render_normalized(normalized, use_separators=use_separators)
    new_content = header + "".join(lines)
    if not has_trailing_newline and new_content.endswith("\n"):
        new_content = new_content.rstrip("\n")
    changed = new_content != content
    if changed and not dry_run:
        path.write_text(new_content, encoding="utf-8")
    return new_content, changed, stats


def normalize_entries(
    entries: list[MailmapEntry],
) -> tuple[list[MailmapEntry], NormalizeStats]:
    groups: dict[str, tuple[Identity, list[MailmapEntry]]] = {}
    for entry in entries:
        key = entry.canonical.normalized_email
        if key not in groups:
            groups[key] = (entry.canonical, [])
        groups[key][1].append(entry)

    result: list[MailmapEntry] = []
    total_collapses = 0
    total_duplicates = 0
    for canonical, group_entries in groups.values():
        normalized, collapses, duplicates = _normalize_group(canonical, group_entries)
        result.extend(normalized)
        total_collapses += collapses
        total_duplicates += duplicates

    sorted_result = sorted(result, key=_entry_sort_key)
    stats = NormalizeStats(
        original_entries=len(entries),
        normalized_entries=len(sorted_result),
        format1_collapses=total_collapses,
        duplicates_removed=total_duplicates,
    )
    return sorted_result, stats


def render_normalized(
    entries: list[MailmapEntry],
    *,
    use_separators: bool,
) -> list[str]:
    lines: list[str] = []
    prev_canonical_key: str | None = None
    for entry in entries:
        current_key = entry.canonical.normalized_email
        if use_separators and prev_canonical_key and current_key != prev_canonical_key:
            lines.append("\n")
        lines.append(_render_entry(entry) + "\n")
        prev_canonical_key = current_key
    return lines


def _extract_header(content: str) -> str:
    header_lines: list[str] = []
    for line in content.splitlines(keepends=True):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            header_lines.append(line)
        else:
            break
    return "".join(header_lines)


def _normalize_group(
    canonical: Identity,
    entries: list[MailmapEntry],
) -> tuple[list[MailmapEntry], int, int]:
    """Returns (normalized_entries, format1_collapses, duplicates_removed)."""
    same_email: set[tuple[str, str]] = set()
    diff_email: list[MailmapEntry] = []
    has_format1 = False

    canonical_email = canonical.normalized_email
    for entry in entries:
        if not entry.alias.name and entry.alias.normalized_email == canonical_email:
            has_format1 = True
            continue
        if entry.alias.normalized_email == canonical_email:
            alias_key = (entry.alias.name.lower(), entry.alias.normalized_email)
            same_email.add(alias_key)
        else:
            diff_email.append(entry)

    collapses = len(same_email)  # named same-email aliases collapsed to Format 1
    result: list[MailmapEntry] = []
    if same_email or has_format1:
        result.append(
            MailmapEntry(
                canonical=canonical,
                alias=Identity(name="", email=canonical.email),
            )
        )
    duplicates = 0
    seen: set[tuple[str, str]] = set()
    for entry in diff_email:
        dedup_key = (entry.alias.name.lower(), entry.alias.normalized_email)
        if dedup_key in seen:
            duplicates += 1
            continue
        seen.add(dedup_key)
        result.append(entry)

    return result, collapses, duplicates


def _render_entry(entry: MailmapEntry) -> str:
    is_format1 = (
        not entry.alias.name
        and entry.alias.normalized_email == entry.canonical.normalized_email
    )
    if is_format1:
        return str(entry.canonical)
    return f"{entry.canonical} {entry.alias}"


def _entry_sort_key(entry: MailmapEntry) -> tuple[str, str, int, str, str]:
    is_format1 = (
        not entry.alias.name
        and entry.alias.normalized_email == entry.canonical.normalized_email
    )
    return (
        entry.canonical.name.lower(),
        entry.canonical.normalized_email,
        0 if is_format1 else 1,
        entry.alias.name.lower(),
        entry.alias.normalized_email,
    )
