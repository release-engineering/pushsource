from pytest import raises

from pushsource import Source


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


def test_staged_bad_metadata(tmpdir):
    """Trying to use staged source with corrupt metadata file raises"""
    tmpdir.join("staged.json").write("'oops, not valid json'")

    source = Source.get("staged:%s" % tmpdir)

    with raises(ValueError):
        list(source)
