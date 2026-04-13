import subprocess  # nosec B404 — required to invoke the git CLI
from pathlib import Path

from .models import Identity

_FORMAT = "%an <%ae>%n%cn <%ce>"


def get_identities(git_dir: Path | None = None) -> set[Identity]:
    result = _run_git_log(git_dir)
    return _parse_identities(result.stdout)


def get_identity_counts(git_dir: Path | None = None) -> dict[Identity, int]:
    result = _run_git_log(git_dir)
    return _count_identities(result.stdout)


def _run_git_log(git_dir: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = ["git"]
    if git_dir:
        cmd.extend(["-C", str(git_dir)])
    cmd.extend(["log", f"--format={_FORMAT}"])
    # Arguments are fully hardcoded; no user input reaches this call.
    return subprocess.run(  # nosec B603 # noqa: S603
        cmd, capture_output=True, text=True, check=True
    )


def get_mailmap_file_config(git_dir: Path | None = None) -> str | None:
    cmd = ["git"]
    if git_dir:
        cmd.extend(["-C", str(git_dir)])
    cmd.extend(["config", "mailmap.file"])
    # Arguments are fully hardcoded; no user input reaches this call.
    result = subprocess.run(  # nosec B603 # noqa: S603
        cmd, capture_output=True, text=True
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def get_mailmap_blob_config(git_dir: Path | None = None) -> str | None:
    cmd = ["git"]
    if git_dir:
        cmd.extend(["-C", str(git_dir)])
    cmd.extend(["config", "mailmap.blob"])
    # Arguments are fully hardcoded; no user input reaches this call.
    result = subprocess.run(  # nosec B603 # noqa: S603
        cmd, capture_output=True, text=True
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def read_mailmap_blob(git_dir: Path | None, ref: str) -> str | None:
    cmd = ["git"]
    if git_dir:
        cmd.extend(["-C", str(git_dir)])
    cmd.extend(["cat-file", "blob", ref])
    # Arguments are fully hardcoded; no user input reaches this call.
    result = subprocess.run(  # nosec B603 # noqa: S603
        cmd, capture_output=True, text=True
    )
    if result.returncode == 0:
        return result.stdout
    return None


def _parse_identities(output: str) -> set[Identity]:
    identities: set[Identity] = set()
    for line in set(output.splitlines()):
        line = line.strip()
        if not line:
            continue
        identity = Identity.parse(line)
        if identity:
            identities.add(identity)
    return identities


def _count_identities(output: str) -> dict[Identity, int]:
    counts: dict[Identity, int] = {}
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        identity = Identity.parse(line)
        if identity:
            counts[identity] = counts.get(identity, 0) + 1
    return counts
