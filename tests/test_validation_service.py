"""T-1 — ValidationService unit tests. Traces: FR-1, SEC-2."""

from __future__ import annotations

import pytest

from astranotes.errors import ValidationError
from astranotes.models.note import Note
from astranotes.services.validation import MAX_TITLE, ValidationService


@pytest.fixture
def validator() -> ValidationService:
    return ValidationService()


@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_rejects_empty_or_whitespace_title(validator: ValidationService, title: str) -> None:
    with pytest.raises(ValidationError):
        validator.validate(Note.new(title=title, body="b"))


def test_accepts_title_at_boundary(validator: ValidationService) -> None:
    validator.validate(Note.new(title="x" * MAX_TITLE, body="b"))  # exactly 200 is allowed


def test_rejects_title_over_boundary(validator: ValidationService) -> None:
    with pytest.raises(ValidationError):
        validator.validate(Note.new(title="x" * (MAX_TITLE + 1), body="b"))


def test_rejects_body_over_one_megabyte(validator: ValidationService) -> None:
    with pytest.raises(ValidationError):
        validator.validate(Note.new(title="ok", body="a" * (1024 * 1024 + 1)))


@pytest.mark.parametrize("passphrase", ["short", "elevenchars"])
def test_rejects_short_passphrase(validator: ValidationService, passphrase: str) -> None:
    with pytest.raises(ValidationError):
        validator.validate_passphrase(passphrase)


def test_accepts_twelve_char_passphrase(validator: ValidationService) -> None:
    validator.validate_passphrase("twelvecharss")  # exactly 12
