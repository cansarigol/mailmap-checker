import subprocess  # nosec B404 — required to invoke the git CLI
from pathlib import Path

from .models import Identity

_FORMAT = "%an <%ae>"


def get_identities(git_dir: Path | None = None) -> set[Identity]:
    cmd = ["git"]
    if git_dir:
        cmd.extend(["-C", str(git_dir)])
    cmd.extend(["log", f"--format={_FORMAT}"])
    # Arguments are fully hardcoded; no user input reaches this call.
    result = subprocess.run(  # nosec B603 # noqa: S603
        cmd, capture_output=True, text=True, check=True
    )
    return _parse_identities(result.stdout)


def _parse_identities(output: str) -> set[Identity]:
    identities: set[Identity] = set()
    for line in output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        identity = Identity.parse(line)
        if identity:
            identities.add(identity)
    return identities
