import os

from pytest import raises, fixture
from mock import patch

from pushsource import Source, ModuleMdPushItem

from .fake_koji import FakeKojiController


def test_koji_modules(fake_koji, koji_dir):
    """Koji source yields requested modules"""

    source = Source.get(
        "koji:https://koji.example.com/?module_build=foo-1.0-1", basedir=koji_dir
    )

    fake_koji.insert_rpms(["foo-1.0-1.x86_64.rpm"], build_nvr="foo-1.0-1")
    fake_koji.insert_modules(
        ["modulemd.x86_64.txt", "modulemd.s390x.txt"], build_nvr="foo-1.0-1"
    )

    # Eagerly fetch
    items = list(source)

    # It should have returned push items for the two modules
    assert len(items) == 2

    items = sorted(items, key=lambda pi: pi.name)

    assert items[0] == ModuleMdPushItem(
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

    assert items[1] == ModuleMdPushItem(
        name="modulemd.x86_64.txt",
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
