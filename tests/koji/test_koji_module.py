import os
import shutil
import textwrap

from pytest import raises, fixture
from mock import patch

from pushsource import Source, ModuleMdPushItem, ModuleMdSourcePushItem

from .fake_koji import FakeKojiController

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def test_koji_modules(fake_koji, koji_dir):
    """Koji source yields requested modules"""

    source = Source.get(
        "koji:https://koji.example.com/?module_build=foo-1.0-1", basedir=koji_dir
    )

    fake_koji.insert_rpms(["foo-1.0-1.x86_64.rpm"], build_nvr="foo-1.0-1")
    fake_koji.insert_modules(
        ["modulemd.x86_64.txt", "modulemd.s390x.txt", "modulemd.src.txt"],
        build_nvr="foo-1.0-1",
    )

    # Set up an existing modulemd file for one of the items and not the others.
    modulemd_path = os.path.join(
        koji_dir, "packages/foo/1.0/1/files/module/modulemd.x86_64.txt"
    )
    os.makedirs(os.path.dirname(modulemd_path))
    shutil.copy(os.path.join(DATA_DIR, "modulemd-varnish-x86_64.yaml"), modulemd_path)

    # Eagerly fetch
    items = list(source)

    # It should have returned push items for the modules
    assert len(items) == 3

    items = sorted(items, key=lambda pi: pi.name)

    assert items[0] == ModuleMdPushItem(
        # For this module, the file didn't exist and we used the filename as module name
        # since metadata is unavailable.
        name="modulemd.s390x.txt",
        state="PENDING",
        src=os.path.join(
            koji_dir, "packages/foo/1.0/1/files/module/modulemd.s390x.txt"
        ),
        dest=[],
        md5sum=None,
        sha256sum=None,
        origin=None,
        build="foo-1.0-1",
        signing_key=None,
    )

    assert items[1] == ModuleMdSourcePushItem(
        # For this module, no attempt was made to parse it since it's a modulemd
        # source file rather than a built module.
        name="modulemd.src.txt",
        state="PENDING",
        src=os.path.join(koji_dir, "packages/foo/1.0/1/files/module/modulemd.src.txt"),
        dest=[],
        md5sum=None,
        sha256sum=None,
        origin=None,
        build="foo-1.0-1",
        signing_key=None,
    )

    assert items[2] == ModuleMdPushItem(
        # For this module, the file existed and was parseable, so we use the
        # proper NSVCA as the push item name.
        name="varnish:6.0:3220200215073318:43bbeeef:x86_64",
        state="PENDING",
        src=os.path.join(
            koji_dir, "packages/foo/1.0/1/files/module/modulemd.x86_64.txt"
        ),
        dest=[],
        md5sum=None,
        sha256sum=None,
        origin=None,
        build="foo-1.0-1",
        signing_key=None,
    )


def test_koji_multiple_in_stream(fake_koji, koji_dir, caplog):
    """Koji source fails if referenced modulemd file contains multiple modules.

    This isn't something expected to happen in practice. The point of this test is to
    ensure that, if it *does* happen, we fail in a controlled manner rather than
    something odd like silently using the first module in the stream.
    """

    source = Source.get(
        "koji:https://koji.example.com/?module_build=foo-1.0-1", basedir=koji_dir
    )

    fake_koji.insert_rpms(["foo-1.0-1.x86_64.rpm"], build_nvr="foo-1.0-1")
    fake_koji.insert_modules(["modulemd.x86_64.txt"], build_nvr="foo-1.0-1")

    # Set up a modulemd stream with multiple documents for this file.
    modulemd_path = os.path.join(
        koji_dir, "packages/foo/1.0/1/files/module/modulemd.x86_64.txt"
    )
    os.makedirs(os.path.dirname(modulemd_path))
    shutil.copy(os.path.join(DATA_DIR, "modulemd-multiple.yaml"), modulemd_path)

    # Trying to fetch the items should fail
    with raises(Exception) as exc_info:
        list(source)

    # We should find a relevant message from YAML parser
    assert "expected a single document in the stream" in str(exc_info)

    # It should have told us exactly which file in which build couldn't be parsed
    expected_message = (
        "In koji build foo-1.0-1, cannot load module metadata from " + modulemd_path
    )
    assert expected_message in caplog.messages


def test_koji_bad_modulemd(fake_koji, koji_dir, caplog):
    """Koji source logs and raises exception on unparseable modulemd file"""

    source = Source.get(
        "koji:https://koji.example.com/?module_build=foo-1.0-1", basedir=koji_dir
    )

    fake_koji.insert_rpms(["foo-1.0-1.x86_64.rpm"], build_nvr="foo-1.0-1")
    fake_koji.insert_modules(
        ["modulemd.x86_64.txt", "modulemd.s390x.txt"], build_nvr="foo-1.0-1"
    )

    # Write invalid modulemd here.
    modulemd_path = os.path.join(
        koji_dir, "packages/foo/1.0/1/files/module/modulemd.x86_64.txt"
    )
    os.makedirs(os.path.dirname(modulemd_path))
    with open(modulemd_path, "wt") as f:
        f.write("This ain't no valid modulemd")

    # Trying to fetch the items should fail
    with raises(Exception):
        list(source)

    # And it should have told us exactly which file in which build couldn't be parsed
    expected_message = (
        "In koji build foo-1.0-1, cannot load module metadata from " + modulemd_path
    )
    assert expected_message in caplog.messages


def test_koji_modules_filter_filename(fake_koji, koji_dir):
    """Koji source can filter modules by filename"""

    source = Source.get(
        "koji:https://koji.example.com/?module_build=foo-1.0-1",
        basedir=koji_dir,
        module_filter_filename="modulemd.x86_64.txt,modulemd.aarch64.txt",
    )

    fake_koji.insert_rpms(["foo-1.0-1.x86_64.rpm"], build_nvr="foo-1.0-1")
    fake_koji.insert_modules(
        ["modulemd.x86_64.txt", "modulemd.aarch64.txt", "modulemd.s390x.txt"],
        build_nvr="foo-1.0-1",
    )

    # Eagerly fetch
    items = list(source)

    # It should have returned push items for the two modules which matched filter
    assert len(items) == 2

    item_names = sorted([item.name for item in items])

    # Should be only those two matching the filter
    assert item_names == ["modulemd.aarch64.txt", "modulemd.x86_64.txt"]
