import re
from pathlib import Path

from .models import Identity, MailmapEntry

_IDENTITY_RE = re.compile(r"([^<]*?)\s*<([^>]+)>")
_MAX_FILE_SIZE = 1_048_576  # 1 MB
_MAX_LINE_LENGTH = 1024


def parse_mailmap(path: Path) -> list[MailmapEntry]:
    if not path.exists():
        return []
    if path.stat().st_size > _MAX_FILE_SIZE:
        raise ValueError(f".mailmap exceeds maximum size of {_MAX_FILE_SIZE} bytes")
    entries = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if len(stripped) > _MAX_LINE_LENGTH:
                continue
            entry = _parse_line(stripped)
            if entry:
                entries.append(entry)
    return entries


def _parse_line(line: str) -> MailmapEntry | None:
    matches = _IDENTITY_RE.findall(line)
    if len(matches) == 2:
        canonical = Identity.parse(f"{matches[0][0].strip()} <{matches[0][1].strip()}>")
        alias = Identity.parse(f"{matches[1][0].strip()} <{matches[1][1].strip()}>")
        if canonical and alias:
            return MailmapEntry(canonical=canonical, alias=alias)
        return None
    if len(matches) == 1:
        canonical = Identity.parse(f"{matches[0][0].strip()} <{matches[0][1].strip()}>")
        if canonical:
            return MailmapEntry(canonical=canonical, alias=canonical)
    return None
