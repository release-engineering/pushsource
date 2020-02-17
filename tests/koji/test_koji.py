import os

from pytest import raises, fixture
from mock import patch

from pushsource import Source, RpmPushItem

from .fake_koji import FakeKojiController


@fixture
def fake_koji():
    controller = FakeKojiController()
    with patch("koji.ClientSession") as mock_session:
        mock_session.side_effect = controller.session
        yield controller


@fixture
def koji_dir(tmpdir):
    yield str(tmpdir.mkdir("koji"))


def test_koji_needs_url():
    """Can't obtain source without giving URL"""

    with raises(TypeError):
        Source.get("koji:")


def test_get_koji():
    """Can obtain a koji source"""

    assert Source.get("koji:https://koji.example.com/")


def test_koji_empty():
    """Empty koji source yields no push items"""

    source = Source.get("koji:https://koji.example.com/")
    assert list(source) == []


def test_koji_rpms(fake_koji, koji_dir):
    """Koji source yields requested RPMs"""

    source = Source.get(
        "koji:https://koji.example.com/?rpm=foo-1.0-1.x86_64.rpm,notfound-2.0-1.noarch.rpm",
        basedir=koji_dir,
    )

    # It should not have done anything yet (lazy loading)
    assert not fake_koji.last_url

    # Insert some data
    fake_koji.rpm_data["foo-1.0-1.x86_64.rpm"] = {
        "arch": "x86_64",
        "name": "foo",
        "version": "1.0",
        "release": "1",
        "build_id": 1234,
    }
    fake_koji.build_data[1234] = {
        "name": "foobuild",
        "version": "1.0",
        "release": "1.el8",
        "nvr": "foobuild-1.0-1.el8",
        "volume_name": "somevol",
    }

    # Eagerly fetch
    items = list(source)

    # It should have constructed a session for the given URL
    assert fake_koji.last_url == "https://koji.example.com/"

    # It should have returned push items for the two RPMs
    assert len(items) == 2

    items = sorted(items, key=lambda pi: pi.name)

    # For present RPM, a push item should be yielded using the koji metadata.
    assert items[0] == RpmPushItem(
        name="foo-1.0-1.x86_64.rpm",
        state="PENDING",
        src="%s/vol/somevol/packages/foobuild/1.0/1.el8/x86_64/foo-1.0-1.x86_64.rpm"
        % koji_dir,
        build="foobuild-1.0-1.el8",
    )

    # For missing RPMs, a push item should be yielded with NOTFOUND state.
    assert items[1] == RpmPushItem(name="notfound-2.0-1.noarch.rpm", state="NOTFOUND")


def test_koji_missing_signing_key(fake_koji, koji_dir, caplog):
    """RPM is NOTFOUND if requested signing key is not available."""

    source = Source.get(
        "koji:https://koji.example.com/?rpm=foo-1.0-1.x86_64.rpm&signing_key=abc123",
        basedir=koji_dir,
    )

    fake_koji.rpm_data["foo-1.0-1.x86_64.rpm"] = {
        "arch": "x86_64",
        "name": "foo",
        "version": "1.0",
        "release": "1",
        "build_id": 1234,
    }
    fake_koji.build_data[1234] = {
        "name": "foobuild",
        "version": "1.0",
        "release": "1.el8",
        "nvr": "foobuild-1.0-1.el8",
        "volume_name": "somevol",
    }

    # Eagerly fetch
    items = list(source)

    # It should be counted as NOTFOUND...
    assert items == [RpmPushItem(name="foo-1.0-1.x86_64.rpm", state="NOTFOUND")]

    # ...for this reason
    assert (
        "RPM not found in koji with signing key(s) abc123: foo-1.0-1.x86_64.rpm"
        in caplog.messages
    )


def test_koji_uses_signing_key(fake_koji, koji_dir, caplog):
    """RPM uses first existing of specified signing keys."""

    source = Source.get(
        "koji:https://koji.example.com/?rpm=foo-1.0-1.x86_64.rpm",
        basedir=koji_dir,
        signing_key=["ABC123", None, "DEF456"],
    )

    fake_koji.rpm_data["foo-1.0-1.x86_64.rpm"] = {
        "arch": "x86_64",
        "name": "foo",
        "version": "1.0",
        "release": "1",
        "build_id": 1234,
    }
    fake_koji.build_data[1234] = {
        "name": "foobuild",
        "version": "1.0",
        "release": "1.el8",
        "nvr": "foobuild-1.0-1.el8",
        "volume_name": "somevol",
    }

    signed_rpm_path = os.path.join(
        koji_dir,
        "vol/somevol/packages/foobuild/1.0/1.el8",
        "data/signed/def456/x86_64/foo-1.0-1.x86_64.rpm",
    )

    # Make the signed RPM exist (contents not relevant here)
    os.makedirs(os.path.dirname(signed_rpm_path))
    open(signed_rpm_path, "wb")

    # Eagerly fetch
    items = list(source)

    # It should have found the RPM using the signing key we created within testdata
    assert items[0] == RpmPushItem(
        name="foo-1.0-1.x86_64.rpm",
        state="PENDING",
        src=signed_rpm_path,
        build="foobuild-1.0-1.el8",
        signing_key="def456",
    )
