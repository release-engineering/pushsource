import hashlib

from pytest import raises
from mock import patch

from pushsource import PushItem


def test_with_checksums_noop():
    """with_checksums does nothing if sums are already present"""
    item = PushItem(
        name="item",
        src="nonexistent-file",
        md5sum="d3b07384d113edec49eaa6238ad5ff00",
        sha256sum="49ae93732fcf8d63fe1cce759664982dbd5b23161f007dba8561862adc96d063",
    )
    assert item.with_checksums() is item


def test_with_checksums_nosrc():
    """with_checksums does nothing on file-less item"""
    item = PushItem(name="item")

    assert item.with_checksums() is item


def test_with_checksums_read_fails():
    """with_checksums propagates error if referenced file can't be read"""
    with raises(Exception) as exc_info:
        PushItem(name="item", src="file-does-not-exist").with_checksums()

    # exact type and message is not verified due to py2 vs py3 differences.
    assert "file-does-not-exist" in str(exc_info.value)


def test_with_checksums_reads_content(tmpdir):
    """with_checksums reads file to calculate checksums"""
    tmpfile = tmpdir.join("somefile")
    tmpfile.write(b"some data")

    item = PushItem(name="item", src=str(tmpfile))
    item_sums = item.with_checksums()

    # Original item should be untouched
    assert not item.md5sum
    assert not item.sha256sum

    # with_checksums output should have correct sums filled in
    assert item_sums.md5sum == "1e50210a0202497fb79bc38b6ade6c34"
    assert (
        item_sums.sha256sum
        == "1307990e6ba5ca145eb35e99182a9bec46531bc54ddf656a602c780fa0240dee"
    )


def test_with_checksums_partial(tmpdir):
    """with_checksums only calculates checksums of missing types"""

    tmpfile = tmpdir.join("somefile")
    tmpfile.write(b"some data")

    item = PushItem(
        name="item", src=str(tmpfile), md5sum="1e50210a0202497fb79bc38b6ade6c34"
    )

    hashlib_new = hashlib.new
    computed_types = []

    def patched_hashlib_new(hash_type):
        computed_types.append(hash_type)
        return hashlib_new(hash_type)

    with patch("hashlib.new", new=patched_hashlib_new):
        item_sums = item.with_checksums()

    # with_checksums output should have correct sums
    assert item_sums.md5sum == "1e50210a0202497fb79bc38b6ade6c34"
    assert (
        item_sums.sha256sum
        == "1307990e6ba5ca145eb35e99182a9bec46531bc54ddf656a602c780fa0240dee"
    )

    # Only sha256 should have been calculated, since md5 was already present
    assert computed_types == ["sha256"]
