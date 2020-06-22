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


def test_koji_nobuild(fake_koji):
    """koji source referencing nonexistent build will fail"""

    source = Source.get("koji:https://koji.example.com/?module_build=notexist-1.2.3")
    with raises(ValueError) as exc_info:
        list(source)

    assert "Module build not found in koji: notexist-1.2.3" in str(exc_info.value)


def test_koji_exceptions(fake_koji):
    """Exceptions raised during calls to koji are propagated"""

    source = Source.get("koji:https://koji.example.com/?module_build=error-1.2.3")

    error = RuntimeError("simulated error")
    fake_koji.build_data["error-1.2.3"] = error

    with raises(Exception) as exc_info:
        list(source)

    # It should have propagated *exactly* the exception from koji
    assert exc_info.value is error


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
        "id": 1234,
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


def test_koji_rpm_by_int(fake_koji, koji_dir):
    """Koji source yields requested RPM by ID"""

    source = Source.get(
        "koji:https://koji.example.com/",
        basedir=koji_dir,
        # source is expected to accept both real ints and integer strings,
        # the latter coming from URLs.
        rpm=["12345", 23456],
    )

    # It should not have done anything yet (lazy loading)
    assert not fake_koji.last_url

    # Insert some data. Keys are using real integers, which tests that
    # the source is converting integer strings to real integers before calling
    # to koji.
    fake_koji.rpm_data[12345] = {
        "arch": "x86_64",
        "name": "foo",
        "version": "1.0",
        "release": "1",
        "build_id": 1234,
    }
    fake_koji.rpm_data[23456] = {
        "arch": "noarch",
        "name": "foo",
        "version": "1.0",
        "release": "1",
        "build_id": 1234,
    }
    fake_koji.build_data[1234] = {
        "id": 1234,
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

    # It should have yielded the two RPMs.
    assert items[0] == RpmPushItem(
        name="foo-1.0-1.noarch.rpm",
        state="PENDING",
        src="%s/vol/somevol/packages/foobuild/1.0/1.el8/noarch/foo-1.0-1.noarch.rpm"
        % koji_dir,
        build="foobuild-1.0-1.el8",
    )
    assert items[1] == RpmPushItem(
        name="foo-1.0-1.x86_64.rpm",
        state="PENDING",
        src="%s/vol/somevol/packages/foobuild/1.0/1.el8/x86_64/foo-1.0-1.x86_64.rpm"
        % koji_dir,
        build="foobuild-1.0-1.el8",
    )


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
        "id": 1234,
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
    expected_path = (
        "%s/vol/somevol/packages/foobuild/1.0/1.el8/data/signed/abc123/x86_64/foo-1.0-1.x86_64.rpm"
        % koji_dir
    )
    expected_msg = "RPM not found in koji at path(s): %s" % expected_path
    assert expected_msg in caplog.messages


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
        "id": 1234,
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


def test_koji_cache(fake_koji, koji_dir):
    """Koji source can reuse a cache to avoid repeated calls."""

    cache = {}

    source_ctor = Source.get_partial(
        "koji:https://koji.example.com/?rpm=foo-1.0-1.x86_64.rpm&module_build=foo-1.0-1",
        basedir=koji_dir,
        cache=cache,
    )

    fake_koji.insert_rpms(["foo-1.0-1.x86_64.rpm"], build_nvr="foo-1.0-1")
    fake_koji.insert_modules(
        ["modulemd.x86_64.txt", "modulemd.s390x.txt"], build_nvr="foo-1.0-1"
    )

    # Get push items from one source
    items1 = sorted(list(source_ctor()), key=repr)

    # It should have three items (1 RPM, two modulemds)
    assert len(items1) == 3

    # Now wipe out all the fake_koji data
    fake_koji.reset()

    # Get push items from a new source.
    # It should succeed even though no test data is defined
    items2 = sorted(list(source_ctor()), key=repr)

    # They should give identical results
    assert items1 == items2

    # It should have stored something in the cache
    assert cache
