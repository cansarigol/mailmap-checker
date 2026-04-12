from mailmap_checker.fixer import apply_fixes, generate_entries
from mailmap_checker.models import Identity, IdentityGroup


class TestGenerateEntries:
    def test_generates_mailmap_lines(self):
        gaps = [
            IdentityGroup(
                canonical=Identity("Alice Johnson", "Alice.Johnson@acme.com"),
                identities=[
                    Identity("Alice Johnson", "Alice.Johnson@acme.com"),
                    Identity("alice.j", "alice@oldcorp.com"),
                ],
                missing_entries=[
                    Identity("alice.j", "alice@oldcorp.com"),
                ],
            ),
        ]
        entries = generate_entries(gaps)
        assert entries == [
            "Alice Johnson <Alice.Johnson@acme.com> alice.j <alice@oldcorp.com>"
        ]

    def test_multiple_missing_entries(self):
        gaps = [
            IdentityGroup(
                canonical=Identity("Alice", "alice@acme.com"),
                identities=[],
                missing_entries=[
                    Identity("old1", "old1@x.com"),
                    Identity("old2", "old2@x.com"),
                ],
            ),
        ]
        entries = generate_entries(gaps)
        assert len(entries) == 2

    def test_skips_group_without_canonical(self):
        gaps = [
            IdentityGroup(canonical=None, identities=[], missing_entries=[]),
        ]
        assert generate_entries(gaps) == []

    def test_empty_gaps(self):
        assert generate_entries([]) == []


class TestApplyFixesInsertion:
    def test_inserts_after_existing_canonical_group(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Alice <alice@acme.com> OldAlice <old@acme.com>\n"
            "\n"
            "Bob <bob@acme.com> OldBob <old-bob@acme.com>\n"
        )
        apply_fixes(
            mailmap,
            ["Alice <alice@acme.com> alice.j <alice@oldcorp.com>"],
        )
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@acme.com> OldAlice <old@acme.com>"
        assert lines[1] == ("Alice <alice@acme.com> alice.j <alice@oldcorp.com>")
        assert lines[3] == "Bob <bob@acme.com> OldBob <old-bob@acme.com>"

    def test_inserts_after_last_line_of_canonical(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Alice <alice@acme.com> A1 <a1@x.com>\n"
            "Alice <alice@acme.com> A2 <a2@x.com>\n"
            "\n"
            "Bob <bob@acme.com> B1 <b1@x.com>\n"
        )
        apply_fixes(
            mailmap,
            ["Alice <alice@acme.com> A3 <a3@x.com>"],
        )
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@acme.com> A1 <a1@x.com>"
        assert lines[1] == "Alice <alice@acme.com> A2 <a2@x.com>"
        assert lines[2] == "Alice <alice@acme.com> A3 <a3@x.com>"
        assert lines[4] == "Bob <bob@acme.com> B1 <b1@x.com>"

    def test_multiple_canonicals_insert_at_correct_positions(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Alice <alice@acme.com> A1 <a1@x.com>\n\nBob <bob@acme.com> B1 <b1@x.com>\n"
        )
        apply_fixes(
            mailmap,
            [
                "Alice <alice@acme.com> A2 <a2@x.com>",
                "Bob <bob@acme.com> B2 <b2@x.com>",
            ],
        )
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@acme.com> A1 <a1@x.com>"
        assert lines[1] == "Alice <alice@acme.com> A2 <a2@x.com>"
        assert lines[3] == "Bob <bob@acme.com> B1 <b1@x.com>"
        assert lines[4] == "Bob <bob@acme.com> B2 <b2@x.com>"


class TestApplyFixesSorted:
    def test_appends_after_last_entry_when_sorted_later(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@acme.com> A1 <a1@x.com>\n")
        apply_fixes(
            mailmap,
            ["Bob <bob@acme.com> OldBob <old-bob@x.com>"],
        )
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@acme.com> A1 <a1@x.com>"
        assert lines[1] == "Bob <bob@acme.com> OldBob <old-bob@x.com>"

    def test_inserts_in_sorted_position_between_entries(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Alice <alice@acme.com> A1 <a1@x.com>\n"
            "\n"
            "Charlie <charlie@acme.com> C1 <c1@x.com>\n"
        )
        apply_fixes(
            mailmap,
            ["Bob <bob@acme.com> B1 <b1@x.com>"],
        )
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@acme.com> A1 <a1@x.com>"
        assert lines[1] == ""
        assert lines[2] == "Bob <bob@acme.com> B1 <b1@x.com>"
        assert lines[3] == ""
        assert lines[4] == "Charlie <charlie@acme.com> C1 <c1@x.com>"

    def test_inserts_before_first_entry_when_sorted_earlier(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Bob <bob@acme.com> B1 <b1@x.com>\n")
        apply_fixes(
            mailmap,
            ["Alice <alice@acme.com> A1 <a1@x.com>"],
        )
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@acme.com> A1 <a1@x.com>"
        assert lines[1] == "Bob <bob@acme.com> B1 <b1@x.com>"

    def test_creates_new_file(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        apply_fixes(
            mailmap,
            ["Alice <alice@acme.com> old <old@x.com>"],
        )
        assert mailmap.read_text() == "Alice <alice@acme.com> old <old@x.com>\n"

    def test_handles_missing_trailing_newline(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("# header")
        apply_fixes(
            mailmap,
            ["Alice <alice@acme.com> old <old@x.com>"],
        )
        content = mailmap.read_text()
        assert content.startswith("# header\n")
        assert "Alice <alice@acme.com> old <old@x.com>" in content

    def test_empty_existing_file(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        apply_fixes(
            mailmap,
            ["Alice <alice@acme.com> old <old@x.com>"],
        )
        assert mailmap.read_text() == "Alice <alice@acme.com> old <old@x.com>\n"

    def test_multiple_groups_no_separator(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@acme.com> A1 <a1@x.com>\n")
        apply_fixes(
            mailmap,
            [
                "Bob <bob@acme.com> OldBob <old@x.com>",
                "Bob <bob@acme.com> OldBob2 <old2@x.com>",
                "Charlie <charlie@acme.com> OldCharlie <old@x.com>",
            ],
        )
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@acme.com> A1 <a1@x.com>"
        assert lines[1] == "Bob <bob@acme.com> OldBob <old@x.com>"
        assert lines[2] == "Bob <bob@acme.com> OldBob2 <old2@x.com>"
        assert lines[3] == "Charlie <charlie@acme.com> OldCharlie <old@x.com>"

    def test_preserves_existing_blank_lines(self, tmp_path):
        """When file uses blank-line separators, new entries get them too."""
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Alice <alice@acme.com> A1 <a1@x.com>\n"
            "\n"
            "Charlie <charlie@acme.com> C1 <c1@x.com>\n"
        )
        apply_fixes(
            mailmap,
            ["Dave <dave@acme.com> D1 <d1@x.com>"],
        )
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@acme.com> A1 <a1@x.com>"
        assert lines[1] == ""
        assert lines[2] == "Charlie <charlie@acme.com> C1 <c1@x.com>"
        assert lines[3] == ""
        assert lines[4] == "Dave <dave@acme.com> D1 <d1@x.com>"

    def test_separator_file_adds_blank_before_appended(self, tmp_path):
        """Appending to a separator-style file adds blank line before new entries."""
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Alice <alice@acme.com> A1 <a1@x.com>\n\nBob <bob@acme.com> B1 <b1@x.com>\n"
        )
        apply_fixes(
            mailmap,
            ["Charlie <charlie@acme.com> C1 <c1@x.com>"],
        )
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@acme.com> A1 <a1@x.com>"
        assert lines[1] == ""
        assert lines[2] == "Bob <bob@acme.com> B1 <b1@x.com>"
        assert lines[3] == ""
        assert lines[4] == "Charlie <charlie@acme.com> C1 <c1@x.com>"

    def test_compact_file_stays_compact(self, tmp_path):
        """When file has no blank-line separators, new entries don't add them."""
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Alice <alice@acme.com> A1 <a1@x.com>\n"
            "Charlie <charlie@acme.com> C1 <c1@x.com>\n"
        )
        apply_fixes(
            mailmap,
            ["Dave <dave@acme.com> D1 <d1@x.com>"],
        )
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@acme.com> A1 <a1@x.com>"
        assert lines[1] == "Charlie <charlie@acme.com> C1 <c1@x.com>"
        assert lines[2] == "Dave <dave@acme.com> D1 <d1@x.com>"
        assert len(lines) == 3

    def test_sorted_at_different_positions(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Bob <bob@acme.com> B1 <b1@x.com>\n")
        apply_fixes(
            mailmap,
            [
                "Alice <alice@acme.com> A1 <a1@x.com>",
                "Charlie <charlie@acme.com> C1 <c1@x.com>",
            ],
        )
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@acme.com> A1 <a1@x.com>"
        assert lines[1] == "Bob <bob@acme.com> B1 <b1@x.com>"
        assert lines[2] == "Charlie <charlie@acme.com> C1 <c1@x.com>"


class TestApplyFixesMixed:
    def test_insert_and_append_together(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@acme.com> A1 <a1@x.com>\n")
        apply_fixes(
            mailmap,
            [
                "Alice <alice@acme.com> A2 <a2@x.com>",
                "Bob <bob@acme.com> B1 <b1@x.com>",
            ],
        )
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <alice@acme.com> A1 <a1@x.com>"
        assert lines[1] == "Alice <alice@acme.com> A2 <a2@x.com>"
        assert lines[2] == "Bob <bob@acme.com> B1 <b1@x.com>"
