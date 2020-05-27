import os

from pytest import raises
from jsonschema import ValidationError

from pushsource import Source


DATADIR = os.path.join(os.path.dirname(__file__), "data")


def test_staged_notexist(tmpdir):
    """Trying to use staged source of nonexistent directory does not work"""
    notexist = str(tmpdir.join("some/notexist/dir"))
    source = Source.get("staged:%s" % notexist)

    with raises(OSError):
        list(source)


def test_staged_empty_no_metadata(tmpdir):
    """Trying to use staged source of empty directory does not work"""
    empty = str(tmpdir.mkdir("empty"))
    source = Source.get("staged:%s" % empty)

    with raises(IOError):
        list(source)


def test_staged_empty_with_metadata(tmpdir):
    """Trying to use staged source of empty directory with valid metadata silently yields nothing"""
    empty = tmpdir.mkdir("empty")
    empty.join("staged.json").write('{"header": {"version": "0.2"}}')
    source = Source.get("staged:%s" % empty)

    assert list(source) == []


def test_staged_no_header_metadata(tmpdir):
    """Loading a metadata file with no header will fail."""
    empty = tmpdir.mkdir("empty")
    empty.join("pub-mapfile.json").write("{}")
    source = Source.get("staged:%s" % empty)

    with raises(ValidationError) as exc_info:
        list(source)


def test_staged_dupe_metadata():
    """Loading a metadata file with duplicate entries will fail."""
    staged_dir = os.path.join(DATADIR, "dupe_meta")
    source = Source.get("staged:%s" % staged_dir)

    with raises(ValueError) as exc_info:
        list(source)

    assert "dest1/ISOS/test.txt listed twice in staged.yaml" in str(exc_info.value)


def test_staged_file_with_no_metadata(tmpdir):
    """Trying to use staged source where a staged file is missing metadata will raise"""
    staged = tmpdir.mkdir("staged")
    staged.join("staged.json").write('{"header": {"version": "0.2"}}')
    staged.mkdir("dest").mkdir("FILES").join("some-file").write("some-content")

    source = Source.get("staged:%s" % staged)

    with raises(ValueError) as exc_info:
        list(source)

    assert "No metadata available for dest/FILES/some-file in staged.json" in str(
        exc_info.value
    )


def test_staged_bad_metadata(tmpdir):
    """Trying to use staged source with corrupt metadata file raises"""
    tmpdir.join("staged.json").write("'oops, not valid json'")

    source = Source.get("staged:%s" % tmpdir)

    with raises(ValueError):
        list(source)
