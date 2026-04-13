from mailmap_checker.models import Identity, MailmapEntry
from mailmap_checker.normalizer import (
    normalize_entries,
    normalize_file,
    render_normalized,
)


class TestNormalizeEntries:
    def test_collapses_same_email_to_format1(self):
        canonical = Identity("Alice", "alice@acme.com")
        alias = Identity("alice.j", "alice@acme.com")
        entries = [MailmapEntry(canonical=canonical, alias=alias)]
        result, stats = normalize_entries(entries)
        assert len(result) == 1
        assert result[0].canonical == canonical
        assert result[0].alias.name == ""
        assert result[0].alias.normalized_email == canonical.normalized_email
        assert stats.format1_collapses == 1

    def test_preserves_different_email(self):
        canonical = Identity("Alice", "alice@acme.com")
        alias = Identity("alice.j", "alice@old.com")
        entries = [MailmapEntry(canonical=canonical, alias=alias)]
        result, _ = normalize_entries(entries)
        assert len(result) == 1
        assert result[0].alias == alias

    def test_mixed_same_and_different_email(self):
        canonical = Identity("Alice", "alice@acme.com")
        same = Identity("alice.j", "alice@acme.com")
        diff = Identity("old", "old@other.com")
        entries = [
            MailmapEntry(canonical=canonical, alias=same),
            MailmapEntry(canonical=canonical, alias=diff),
        ]
        result, stats = normalize_entries(entries)
        assert len(result) == 2
        assert result[0].alias.name == ""  # Format 1
        assert result[1].alias == diff
        assert stats.format1_collapses == 1

    def test_existing_format1_preserved(self):
        canonical = Identity("Alice", "alice@acme.com")
        alias = Identity("", "alice@acme.com")
        entries = [MailmapEntry(canonical=canonical, alias=alias)]
        result, stats = normalize_entries(entries)
        assert len(result) == 1
        assert result[0].alias.name == ""
        assert stats.format1_collapses == 0

    def test_deduplicates_identical_entries(self):
        canonical = Identity("Alice", "alice@acme.com")
        alias = Identity("old", "old@x.com")
        entries = [
            MailmapEntry(canonical=canonical, alias=alias),
            MailmapEntry(canonical=canonical, alias=alias),
        ]
        result, stats = normalize_entries(entries)
        assert len(result) == 1
        assert stats.duplicates_removed == 1

    def test_deduplicates_case_insensitive(self):
        canonical = Identity("Alice", "alice@acme.com")
        alias1 = Identity("Old", "old@x.com")
        alias2 = Identity("old", "Old@X.COM")
        entries = [
            MailmapEntry(canonical=canonical, alias=alias1),
            MailmapEntry(canonical=canonical, alias=alias2),
        ]
        result, stats = normalize_entries(entries)
        assert len(result) == 1
        assert stats.duplicates_removed == 1

    def test_multiple_same_email_aliases_collapse(self):
        canonical = Identity("Alice", "alice@acme.com")
        entries = [
            MailmapEntry(canonical=canonical, alias=Identity("a1", "alice@acme.com")),
            MailmapEntry(canonical=canonical, alias=Identity("a2", "alice@acme.com")),
            MailmapEntry(canonical=canonical, alias=Identity("a3", "alice@acme.com")),
        ]
        result, stats = normalize_entries(entries)
        assert len(result) == 1
        assert result[0].alias.name == ""
        assert stats.format1_collapses == 3

    def test_sorts_groups_alphabetically(self):
        bob = Identity("Bob", "bob@x.com")
        alice = Identity("Alice", "alice@x.com")
        entries = [
            MailmapEntry(canonical=bob, alias=Identity("b", "bob@x.com")),
            MailmapEntry(canonical=alice, alias=Identity("a", "alice@x.com")),
        ]
        result, _ = normalize_entries(entries)
        assert result[0].canonical == alice
        assert result[1].canonical == bob

    def test_format1_comes_first_in_group(self):
        canonical = Identity("Alice", "alice@acme.com")
        entries = [
            MailmapEntry(canonical=canonical, alias=Identity("old", "old@x.com")),
            MailmapEntry(canonical=canonical, alias=Identity("a1", "alice@acme.com")),
        ]
        result, _ = normalize_entries(entries)
        assert len(result) == 2
        assert result[0].alias.name == ""  # Format 1 first
        assert result[1].alias == Identity("old", "old@x.com")

    def test_empty_input(self):
        result, stats = normalize_entries([])
        assert result == []
        assert stats.original_entries == 0
        assert stats.normalized_entries == 0


class TestRenderNormalized:
    def test_format1_renders_correctly(self):
        entry = MailmapEntry(
            canonical=Identity("Alice", "alice@acme.com"),
            alias=Identity("", "alice@acme.com"),
        )
        lines = render_normalized([entry], use_separators=False)
        assert lines == ["Alice <alice@acme.com>\n"]

    def test_format4_renders_correctly(self):
        entry = MailmapEntry(
            canonical=Identity("Alice", "alice@acme.com"),
            alias=Identity("old", "old@x.com"),
        )
        lines = render_normalized([entry], use_separators=False)
        assert lines == ["Alice <alice@acme.com> old <old@x.com>\n"]

    def test_separators_between_groups(self):
        e1 = MailmapEntry(
            canonical=Identity("Alice", "alice@x.com"),
            alias=Identity("", "alice@x.com"),
        )
        e2 = MailmapEntry(
            canonical=Identity("Bob", "bob@x.com"),
            alias=Identity("", "bob@x.com"),
        )
        lines = render_normalized([e1, e2], use_separators=True)
        assert lines == [
            "Alice <alice@x.com>\n",
            "\n",
            "Bob <bob@x.com>\n",
        ]

    def test_no_separator_within_group(self):
        canonical = Identity("Alice", "alice@acme.com")
        e1 = MailmapEntry(
            canonical=canonical,
            alias=Identity("", "alice@acme.com"),
        )
        e2 = MailmapEntry(
            canonical=canonical,
            alias=Identity("old", "old@x.com"),
        )
        lines = render_normalized([e1, e2], use_separators=True)
        assert lines == [
            "Alice <alice@acme.com>\n",
            "Alice <alice@acme.com> old <old@x.com>\n",
        ]

    def test_compact_no_separators(self):
        e1 = MailmapEntry(
            canonical=Identity("Alice", "alice@x.com"),
            alias=Identity("", "alice@x.com"),
        )
        e2 = MailmapEntry(
            canonical=Identity("Bob", "bob@x.com"),
            alias=Identity("", "bob@x.com"),
        )
        lines = render_normalized([e1, e2], use_separators=False)
        assert lines == [
            "Alice <alice@x.com>\n",
            "Bob <bob@x.com>\n",
        ]


class TestNormalizeFile:
    def test_full_normalization(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Bob <bob@x.com> old-bob <bob@x.com>\n"
            "Alice <alice@x.com> old-alice <alice@x.com>\n"
        )
        new_content, changed, stats = normalize_file(mailmap)
        assert changed
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@x.com>"
        assert lines[1] == "Bob <bob@x.com>"
        assert stats.format1_collapses == 2
        assert stats.original_entries == 2
        assert stats.normalized_entries == 2

    def test_preserves_header_comments(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("# Header comment\n\nBob <bob@x.com> old <bob@x.com>\n")
        normalize_file(mailmap)
        content = mailmap.read_text()
        assert content.startswith("# Header comment\n\n")

    def test_preserves_trailing_newline(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@x.com> old <alice@x.com>\n")
        normalize_file(mailmap)
        assert mailmap.read_text().endswith("\n")

    def test_preserves_no_trailing_newline(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@x.com> old <alice@x.com>")
        normalize_file(mailmap)
        assert not mailmap.read_text().endswith("\n")

    def test_preserves_separator_style(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Bob <bob@x.com> old-bob <bob@x.com>\n"
            "\n"
            "Alice <alice@x.com> old-alice <alice@x.com>\n"
        )
        normalize_file(mailmap)
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@x.com>"
        assert lines[1] == ""
        assert lines[2] == "Bob <bob@x.com>"

    def test_preserves_compact_style(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Bob <bob@x.com> old-bob <bob@x.com>\n"
            "Alice <alice@x.com> old-alice <alice@x.com>\n"
        )
        normalize_file(mailmap)
        content = mailmap.read_text()
        assert "\n\n" not in content

    def test_already_normalized(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@x.com>\n")
        _, changed, _ = normalize_file(mailmap)
        assert not changed

    def test_dry_run_does_not_modify(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        original = "Bob <bob@x.com> old <bob@x.com>\nAlice <alice@x.com>\n"
        mailmap.write_text(original)
        _, changed, _ = normalize_file(mailmap, dry_run=True)
        assert changed
        assert mailmap.read_text() == original

    def test_email_only_alias_preserved(self, tmp_path):
        """Format 3: Alice <new@x.com> <old@x.com> is preserved."""
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@new.com> <alice@old.com>\n")
        normalize_file(mailmap)
        content = mailmap.read_text()
        assert "Alice <alice@new.com> <alice@old.com>" in content
