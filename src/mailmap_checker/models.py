import re
from dataclasses import dataclass

_IDENTITY_RE = re.compile(r"^(.*?)\s*<([^>]+)>$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_NAME_MAX_LENGTH = 256
_EMAIL_MAX_LENGTH = 254
_SAFE_TEXT_RE = re.compile(r"^[\w\s.\-'+@/()]+$", re.UNICODE)


def _validate_email(email: str) -> bool:
    return (
        bool(email) and len(email) <= _EMAIL_MAX_LENGTH and bool(_EMAIL_RE.match(email))
    )


def _validate_name(name: str) -> bool:
    if not name:
        return True
    return len(name) <= _NAME_MAX_LENGTH and bool(_SAFE_TEXT_RE.match(name))


@dataclass(frozen=True)
class Identity:
    name: str
    email: str

    def __post_init__(self) -> None:
        if not _validate_email(self.email):
            raise ValueError(f"Invalid email: {self.email!r}")
        if not _validate_name(self.name):
            raise ValueError(f"Invalid name: {self.name!r}")

    def __str__(self) -> str:
        if self.name:
            return f"{self.name} <{self.email}>"
        return f"<{self.email}>"

    @classmethod
    def parse(cls, text: str) -> "Identity | None":
        match = _IDENTITY_RE.match(text)
        if not match:
            return None
        name = match.group(1).strip()
        email = match.group(2).strip()
        try:
            return cls(name=name, email=email)
        except ValueError:
            return None

    @property
    def normalized_email(self) -> str:
        return self.email.lower()

    @property
    def email_local_part(self) -> str:
        return self.email.split("@")[0].lower()


@dataclass
class MailmapEntry:
    canonical: Identity
    alias: Identity


@dataclass
class IdentityGroup:
    canonical: Identity | None
    identities: list[Identity]
    missing_entries: list[Identity]
