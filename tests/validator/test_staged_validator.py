import pytest
from jsonschema import ValidationError

from pushsource._impl.backend.staged.staged_utils import VALIDATOR


def test_invalid_root(caplog):
    """Validator logs appropriately if root element is invalid."""

    with pytest.raises(ValidationError):
        VALIDATOR.validate({}, "foo data")

    assert "foo data is not valid" in caplog.messages


def test_invalid_file_metadata(caplog):
    """When the entry for a specific file is invalid, the relative_path is logged."""

    with pytest.raises(ValidationError) as exc:
        VALIDATOR.validate(
            {
                "header": {"version": "0.2"},
                "payload": {
                    "files": [
                        {
                            "relative_path": "my/great/file.iso",
                            "sha256sum": "b5bb9d8014a0f9b1d61e21e796d78dccdf1352f23cd32812f4850b878ae4944c",
                            "filename": "some-file.iso",
                            "attributes": {"oops": "not valid"},
                        }
                    ]
                },
            },
            "some-file.json",
        )

    assert "my/great/file.iso (in some-file.json) is not valid" in caplog.messages
