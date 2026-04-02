import pytest

from mailmap_checker.models import Identity, MailmapEntry


@pytest.fixture()
def canonical_identity():
    return Identity("Alice Johnson", "Alice.Johnson@acme.com")


@pytest.fixture()
def alias_identity():
    return Identity("alice.j", "alice.j@oldcorp.com")


@pytest.fixture()
def sample_entry(canonical_identity, alias_identity):
    return MailmapEntry(canonical=canonical_identity, alias=alias_identity)
