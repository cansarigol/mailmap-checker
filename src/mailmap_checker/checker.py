from .models import Identity, IdentityGroup, MailmapEntry


def find_gaps(
    identities: set[Identity],
    entries: list[MailmapEntry],
) -> list[IdentityGroup]:
    groups = _build_identity_groups(identities, entries)
    return _detect_missing_entries(groups, identities, entries)


def _build_identity_groups(
    identities: set[Identity],
    entries: list[MailmapEntry],
) -> dict[Identity, set[Identity]]:
    uf = _UnionFind()
    all_identities = set(identities)
    for entry in entries:
        all_identities.add(entry.canonical)
        all_identities.add(entry.alias)
    for identity in all_identities:
        uf.find(identity)
    for entry in entries:
        uf.union(entry.canonical, entry.alias)
    _union_by_normalized_email(uf, all_identities)
    _union_by_email_local_part(uf, all_identities)
    return uf.groups()


def _detect_missing_entries(
    groups: dict[Identity, set[Identity]],
    git_identities: set[Identity],
    entries: list[MailmapEntry],
) -> list[IdentityGroup]:
    # Email-only aliases (empty name in alias) match any name with that email
    email_only_aliases = {e.alias.normalized_email for e in entries if not e.alias.name}
    # Named aliases use case-insensitive comparison (per gitmailmap spec)
    named_aliases = {
        (e.alias.name.lower(), e.alias.normalized_email)
        for e in entries
        if e.alias.name
    }

    def is_covered(identity: Identity) -> bool:
        if identity.normalized_email in email_only_aliases:
            return True
        return (
            identity.name.lower(),
            identity.normalized_email,
        ) in named_aliases

    gaps: list[IdentityGroup] = []
    for members_set in groups.values():
        git_members = sorted(
            (m for m in members_set if m in git_identities),
            key=lambda i: (i.name, i.email),
        )
        if len(git_members) <= 1:
            continue
        canonical = _determine_canonical(git_members, members_set, entries)
        missing = [m for m in git_members if m != canonical and not is_covered(m)]
        if missing:
            gaps.append(
                IdentityGroup(
                    canonical=canonical,
                    identities=git_members,
                    missing_entries=missing,
                )
            )
    return sorted(gaps, key=lambda g: g.canonical.name if g.canonical else "")


def _determine_canonical(
    git_members: list[Identity],
    all_members: set[Identity],
    entries: list[MailmapEntry],
) -> Identity:
    # Email-only canonicals (empty name) match any identity with that email
    canonical_email_only = {
        e.canonical.normalized_email for e in entries if not e.canonical.name
    }
    canonical_named = {
        (e.canonical.name.lower(), e.canonical.normalized_email)
        for e in entries
        if e.canonical.name
    }

    def matches_canonical(member: Identity) -> bool:
        if member.normalized_email in canonical_email_only:
            return True
        return (
            member.name.lower(),
            member.normalized_email,
        ) in canonical_named

    # Prefer git members over mailmap-only identities
    for member in git_members:
        if matches_canonical(member):
            return member
    for member in all_members:
        if matches_canonical(member):
            return member
    return git_members[0]


def _union_by_normalized_email(uf: "_UnionFind", identities: set[Identity]) -> None:
    by_email: dict[str, list[Identity]] = {}
    for identity in identities:
        by_email.setdefault(identity.normalized_email, []).append(identity)
    for group in by_email.values():
        for i in range(1, len(group)):
            uf.union(group[0], group[i])


def _union_by_email_local_part(uf: "_UnionFind", identities: set[Identity]) -> None:
    by_local: dict[str, list[Identity]] = {}
    for identity in identities:
        by_local.setdefault(identity.email_local_part, []).append(identity)
    for group in by_local.values():
        if len(group) > 1:
            for i in range(1, len(group)):
                uf.union(group[0], group[i])


class _UnionFind:
    def __init__(self) -> None:
        self._parent: dict[Identity, Identity] = {}

    def find(self, x: Identity) -> Identity:
        if x not in self._parent:
            self._parent[x] = x
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])
        return self._parent[x]

    def union(self, x: Identity, y: Identity) -> None:
        root_x, root_y = self.find(x), self.find(y)
        if root_x != root_y:
            self._parent[root_x] = root_y

    def groups(self) -> dict[Identity, set[Identity]]:
        result: dict[Identity, set[Identity]] = {}
        for item in self._parent:
            root = self.find(item)
            result.setdefault(root, set()).add(item)
        return result
