import pytest

from mailmap_checker.models import Identity, IdentityGroup, MailmapEntry


class TestIdentity:
    def test_str_with_name(self):
        identity = Identity("Alice Johnson", "alice@example.com")
        assert str(identity) == "Alice Johnson <alice@example.com>"

    def test_str_without_name(self):
        identity = Identity("", "alice@example.com")
        assert str(identity) == "<alice@example.com>"

    def test_normalized_email(self):
        identity = Identity("Alice", "Alice.Johnson@ACME.COM")
        assert identity.normalized_email == "alice.johnson@acme.com"

    def test_email_local_part(self):
        identity = Identity("Alice", "Alice.Johnson@acme.com")
        assert identity.email_local_part == "alice.johnson"

    def test_frozen(self):
        identity = Identity("Alice", "alice@example.com")
        with pytest.raises(AttributeError):
            identity.name = "Other"  # type: ignore[misc]

    def test_equality_and_hash(self):
        first = Identity("Alice", "alice@example.com")
        second = Identity("Alice", "alice@example.com")
        assert first == second
        assert hash(first) == hash(second)
        assert len({first, second}) == 1

    def test_inequality(self):
        first = Identity("Alice", "alice@a.com")
        second = Identity("Alice", "alice@b.com")
        assert first != second


class TestIdentityValidation:
    def test_rejects_empty_email(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Identity("Alice", "")

    def test_rejects_email_without_at(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Identity("Alice", "not-an-email")

    def test_rejects_email_without_domain(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Identity("Alice", "alice@")

    def test_rejects_email_without_tld(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Identity("Alice", "alice@example")

    def test_rejects_name_with_angle_brackets(self):
        with pytest.raises(ValueError, match="Invalid name"):
            Identity("<script>alert(1)</script>", "alice@example.com")

    def test_rejects_name_exceeding_max_length(self):
        with pytest.raises(ValueError, match="Invalid name"):
            Identity("A" * 257, "alice@example.com")

    def test_rejects_email_exceeding_max_length(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Identity("Alice", "a" * 250 + "@b.com")

    def test_allows_empty_name(self):
        identity = Identity("", "alice@example.com")
        assert identity.name == ""

    def test_allows_unicode_name(self):
        identity = Identity("Ünsal Özgür", "unsal@example.com")
        assert identity.name == "Ünsal Özgür"

    def test_allows_hyphenated_name(self):
        identity = Identity("Mary-Jane O'Dell", "mary@example.com")
        assert identity.name == "Mary-Jane O'Dell"

    def test_allows_noreply_email(self):
        identity = Identity("Alice", "12345+alice@users.noreply.github.com")
        assert identity.email == "12345+alice@users.noreply.github.com"


class TestIdentityParse:
    def test_valid_identity(self):
        identity = Identity.parse("Alice Johnson <alice@example.com>")
        assert identity == Identity("Alice Johnson", "alice@example.com")

    def test_email_only(self):
        identity = Identity.parse("<alice@example.com>")
        assert identity == Identity("", "alice@example.com")

    def test_invalid_format(self):
        assert Identity.parse("no angle brackets") is None

    def test_invalid_email_returns_none(self):
        assert Identity.parse("Alice <not-an-email>") is None

    def test_invalid_name_returns_none(self):
        assert Identity.parse("<script> <alice@example.com>") is None


class TestMailmapEntry:
    def test_creation(self, canonical_identity, alias_identity):
        entry = MailmapEntry(canonical=canonical_identity, alias=alias_identity)
        assert entry.canonical == canonical_identity
        assert entry.alias == alias_identity


class TestIdentityGroup:
    def test_creation(self, canonical_identity, alias_identity):
        group = IdentityGroup(
            canonical=canonical_identity,
            identities=[canonical_identity, alias_identity],
            missing_entries=[alias_identity],
        )
        assert group.canonical == canonical_identity
        assert len(group.identities) == 2
        assert group.missing_entries == [alias_identity]

    def test_none_canonical(self):
        group = IdentityGroup(canonical=None, identities=[], missing_entries=[])
        assert group.canonical is None
