from mailmap_checker.checker import find_gaps
from mailmap_checker.models import Identity, MailmapEntry


class TestFindGapsFullyMapped:
    def test_no_gaps_when_all_mapped(self):
        canonical = Identity("Alice Johnson", "Alice.Johnson@acme.com")
        alias = Identity("alice.j", "alice.j@oldcorp.com")
        identities = {canonical, alias}
        entries = [MailmapEntry(canonical=canonical, alias=alias)]
        assert find_gaps(identities, entries) == []

    def test_single_identity_no_gap(self):
        identities = {Identity("Alice", "alice@example.com")}
        assert find_gaps(identities, []) == []

    def test_unrelated_identities_no_gap(self):
        identities = {
            Identity("Alice", "alice@example.com"),
            Identity("Bob", "bob@other.com"),
        }
        assert find_gaps(identities, []) == []


class TestFindGapsByEmail:
    def test_same_email_different_name(self):
        identities = {
            Identity("Alice Johnson", "alice@example.com"),
            Identity("alice.j", "alice@example.com"),
        }
        gaps = find_gaps(identities, [])
        assert len(gaps) == 1
        assert len(gaps[0].missing_entries) == 1

    def test_same_email_case_insensitive(self):
        identities = {
            Identity("Alice", "Alice@Example.COM"),
            Identity("alice", "alice@example.com"),
        }
        gaps = find_gaps(identities, [])
        assert len(gaps) == 1


class TestFindGapsByLocalPart:
    def test_same_local_part_different_domain(self):
        identities = {
            Identity("Alice Johnson", "alice.johnson@acme.com"),
            Identity("Alice Johnson", "alice.johnson@oldcorp.com"),
        }
        gaps = find_gaps(identities, [])
        assert len(gaps) == 1
        assert len(gaps[0].missing_entries) == 1


class TestFindGapsCanonicalDetermination:
    def test_uses_existing_canonical_from_entries(self):
        canonical = Identity("Alice Johnson", "Alice.Johnson@acme.com")
        mapped_alias = Identity("alice.j", "alice.j@oldcorp.com")
        unmapped_alias = Identity("Alice", "alice.johnson@acme.com")
        identities = {canonical, mapped_alias, unmapped_alias}
        entries = [MailmapEntry(canonical=canonical, alias=mapped_alias)]
        gaps = find_gaps(identities, entries)
        assert len(gaps) == 1
        assert gaps[0].canonical == canonical
        assert gaps[0].missing_entries == [unmapped_alias]

    def test_uses_mailmap_canonical_not_in_git_log(self):
        """Canonical from mailmap is not a git identity but should be used."""
        mailmap_canonical = Identity("Alice Johnson", "alice@acme.com")
        alias1 = Identity("old1", "old1@x.com")
        alias2 = Identity("old2", "old2@x.com")
        identities = {alias1, alias2}
        entries = [
            MailmapEntry(canonical=mailmap_canonical, alias=alias1),
            MailmapEntry(canonical=mailmap_canonical, alias=alias2),
        ]
        gaps = find_gaps(identities, entries)
        assert gaps == []

    def test_falls_back_to_first_identity_when_no_canonical(self):
        id_a = Identity("AAA", "shared@a.com")
        id_b = Identity("BBB", "shared@b.com")
        identities = {id_a, id_b}
        gaps = find_gaps(identities, [])
        assert len(gaps) == 1
        assert gaps[0].canonical == id_a


class TestFindGapsMailmapOnlyIdentities:
    def test_mailmap_entry_not_in_git_log(self):
        git_identity = Identity("alice", "alice.j@oldcorp.com")
        mailmap_canonical = Identity("Alice Johnson", "Alice.Johnson@acme.com")
        identities = {git_identity}
        entries = [MailmapEntry(canonical=mailmap_canonical, alias=git_identity)]
        assert find_gaps(identities, entries) == []


class TestFindGapsEmailOnlyAlias:
    def test_format3_email_only_alias_no_false_positive(self):
        """Format 3: Proper Name <proper@email> <commit@email>"""
        canonical = Identity("Alice Johnson", "alice@acme.com")
        alias = Identity("", "alice@oldcorp.com")
        git_id = Identity("old alice", "alice@oldcorp.com")
        identities = {canonical, git_id}
        entries = [MailmapEntry(canonical=canonical, alias=alias)]
        gaps = find_gaps(identities, entries)
        assert gaps == []

    def test_format2_email_only_replacement_no_false_positive(self):
        """Format 2: <proper@email> <commit@email>"""
        canonical = Identity("", "alice@acme.com")
        alias = Identity("", "alice@oldcorp.com")
        git_id1 = Identity("Alice", "alice@acme.com")
        git_id2 = Identity("old alice", "alice@oldcorp.com")
        identities = {git_id1, git_id2}
        entries = [MailmapEntry(canonical=canonical, alias=alias)]
        gaps = find_gaps(identities, entries)
        assert gaps == []

    def test_email_only_alias_covers_multiple_names(self):
        """An email-only alias should cover all identities with that email."""
        canonical = Identity("Alice Johnson", "alice@acme.com")
        alias = Identity("", "alice@oldcorp.com")
        git_id1 = Identity("Alice", "alice@oldcorp.com")
        git_id2 = Identity("alice.j", "alice@oldcorp.com")
        identities = {canonical, git_id1, git_id2}
        entries = [MailmapEntry(canonical=canonical, alias=alias)]
        gaps = find_gaps(identities, entries)
        assert gaps == []


class TestFindGapsCaseInsensitive:
    def test_alias_name_case_insensitive(self):
        """Spec: names are matched case-insensitively."""
        canonical = Identity("Alice Johnson", "alice@acme.com")
        alias = Identity("ALICE", "alice@oldcorp.com")
        git_id = Identity("alice", "alice@oldcorp.com")
        identities = {canonical, git_id}
        entries = [MailmapEntry(canonical=canonical, alias=alias)]
        gaps = find_gaps(identities, entries)
        assert gaps == []

    def test_canonical_lookup_case_insensitive(self):
        """Canonical determination should be case-insensitive."""
        mailmap_canonical = Identity("Alice Johnson", "Alice@ACME.COM")
        git_id1 = Identity("Alice Johnson", "alice@acme.com")
        git_id2 = Identity("alice", "alice@oldcorp.com")
        identities = {git_id1, git_id2}
        entries = [MailmapEntry(canonical=mailmap_canonical, alias=mailmap_canonical)]
        gaps = find_gaps(identities, entries)
        assert len(gaps) == 1
        assert gaps[0].canonical == git_id1


class TestFindGapsEdgeCases:
    def test_empty_identities(self):
        assert find_gaps(set(), []) == []

    def test_empty_identities_with_entries(self):
        canonical = Identity("Alice", "alice@acme.com")
        alias = Identity("old", "old@acme.com")
        entries = [MailmapEntry(canonical=canonical, alias=alias)]
        assert find_gaps(set(), entries) == []

    def test_gaps_sorted_by_canonical_name(self):
        id_z1 = Identity("Zara", "zara@a.com")
        id_z2 = Identity("Zara", "zara@b.com")
        id_a1 = Identity("Ahmed", "ahmed@a.com")
        id_a2 = Identity("Ahmed", "ahmed@b.com")
        identities = {id_z1, id_z2, id_a1, id_a2}
        gaps = find_gaps(identities, [])
        assert len(gaps) == 2
        assert gaps[0].canonical.name == "Ahmed"
        assert gaps[1].canonical.name == "Zara"

    def test_multiple_missing_in_one_group(self):
        canonical = Identity("Alice Johnson", "Alice.Johnson@acme.com")
        alias1 = Identity("alice", "alice.johnson@oldcorp.com")
        alias2 = Identity("Alice J", "alice.johnson@legacy.com")
        identities = {canonical, alias1, alias2}
        entries = [MailmapEntry(canonical=canonical, alias=canonical)]
        gaps = find_gaps(identities, entries)
        assert len(gaps) == 1
        assert len(gaps[0].missing_entries) == 2
