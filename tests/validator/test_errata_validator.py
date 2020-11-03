import pytest
from jsonschema import ValidationError

from pushsource._impl.backend.staged.staged_errata import VALIDATOR


def test_invalid_errata_metadata(caplog):
    """Top-level errata ID is logged when top-level validation fails."""

    with pytest.raises(ValidationError) as exc:
        VALIDATOR.validate(
            {"id": "RHBA-1234:56", "references": "oops, wrong type of references"},
            "some-advisory.json",
        )

    assert "RHBA-1234:56 (in some-advisory.json) is not valid" in caplog.messages


def test_invalid_package_metadata(caplog):
    """Package filename is logged when validation fails in pkglist."""

    with pytest.raises(ValidationError) as exc:
        VALIDATOR.validate(
            {
                "id": "RHBA-1234:56",
                "description": "test",
                "from": "test",
                "issued": "test",
                "rights": "test",
                "solution": "test",
                "summary": "test",
                "title": "test",
                "type": "test",
                "updated": "test",
                "pkglist": [
                    {
                        "name": "collection",
                        "packages": [
                            {
                                "filename": "some-pkg-1.0-1.noarch.rpm",
                                "sum": "oops, not valid checksum",
                            }
                        ],
                    }
                ],
            },
            "some-advisory.json",
        )

    assert (
        "some-pkg-1.0-1.noarch.rpm (in some-advisory.json) is not valid"
        in caplog.messages
    )
