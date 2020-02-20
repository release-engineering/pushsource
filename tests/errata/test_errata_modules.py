import os
from pytest import raises, fixture
from mock import patch

from .fake_errata_tool import FakeErrataToolController
from ..koji.fake_koji import FakeKojiController

from pushsource import (
    Source,
    ErratumPushItem,
    ErratumPackage,
    ErratumPackageCollection,
    ErratumReference,
    RpmPushItem,
    ModulemdPushItem,
)


@fixture
def fake_errata_tool():
    controller = FakeErrataToolController()
    with patch("pushsource._impl.backend.errata_source.ServerProxy") as mock_proxy:
        mock_proxy.side_effect = controller.proxy
        yield controller


@fixture
def fake_koji():
    controller = FakeKojiController()
    with patch("koji.ClientSession") as mock_session:
        mock_session.side_effect = controller.session
        yield controller


@fixture
def koji_dir(tmpdir):
    yield str(tmpdir.mkdir("koji"))


def test_errata_modules_via_koji(fake_errata_tool, fake_koji, koji_dir):
    """Errata source containing a module yields modules & RPMs taken
    from koji source"""

    source = Source.get(
        "errata:https://errata.example.com",
        errata="RHEA-2020:0346",
        koji_source="koji:https://koji.example.com?basedir=%s" % koji_dir,
    )

    rpm_filenames = [
        "pgaudit-1.4.0-4.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "pgaudit-1.4.0-4.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "pgaudit-1.4.0-4.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "pgaudit-1.4.0-4.module+el8.1.1+4794+c82b6e09.src.rpm",
        "pgaudit-1.4.0-4.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "pgaudit-debuginfo-1.4.0-4.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "pgaudit-debuginfo-1.4.0-4.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "pgaudit-debuginfo-1.4.0-4.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "pgaudit-debuginfo-1.4.0-4.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "pgaudit-debugsource-1.4.0-4.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "pgaudit-debugsource-1.4.0-4.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "pgaudit-debugsource-1.4.0-4.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "pgaudit-debugsource-1.4.0-4.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgres-decoderbufs-0.10.0-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgres-decoderbufs-0.10.0-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgres-decoderbufs-0.10.0-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgres-decoderbufs-0.10.0-2.module+el8.1.1+4794+c82b6e09.src.rpm",
        "postgres-decoderbufs-0.10.0-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgres-decoderbufs-debuginfo-0.10.0-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgres-decoderbufs-debuginfo-0.10.0-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgres-decoderbufs-debuginfo-0.10.0-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgres-decoderbufs-debuginfo-0.10.0-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgres-decoderbufs-debugsource-0.10.0-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgres-decoderbufs-debugsource-0.10.0-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgres-decoderbufs-debugsource-0.10.0-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgres-decoderbufs-debugsource-0.10.0-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-12.1-2.module+el8.1.1+4794+c82b6e09.src.rpm",
        "postgresql-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-contrib-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-contrib-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-contrib-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-contrib-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-contrib-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-contrib-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-contrib-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-contrib-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-debugsource-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-debugsource-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-debugsource-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-debugsource-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-docs-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-docs-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-docs-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-docs-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-docs-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-docs-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-docs-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-docs-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-plperl-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-plperl-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-plperl-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-plperl-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-plperl-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-plperl-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-plperl-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-plperl-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-plpython3-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-plpython3-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-plpython3-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-plpython3-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-plpython3-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-plpython3-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-plpython3-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-plpython3-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-pltcl-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-pltcl-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-pltcl-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-pltcl-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-pltcl-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-pltcl-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-pltcl-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-pltcl-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-server-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-server-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-server-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-server-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-server-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-server-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-server-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-server-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-server-devel-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-server-devel-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-server-devel-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-server-devel-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-server-devel-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-server-devel-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-server-devel-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-server-devel-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-static-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-static-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-static-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-static-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-test-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-test-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-test-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-test-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-test-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-test-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-test-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-test-rpm-macros-12.1-2.module+el8.1.1+4794+c82b6e09.noarch.rpm",
        "postgresql-upgrade-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-upgrade-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-upgrade-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-upgrade-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-upgrade-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-upgrade-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-upgrade-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-upgrade-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-upgrade-devel-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-upgrade-devel-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-upgrade-devel-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-upgrade-devel-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-upgrade-devel-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.aarch64.rpm",
        "postgresql-upgrade-devel-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
        "postgresql-upgrade-devel-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.s390x.rpm",
        "postgresql-upgrade-devel-debuginfo-12.1-2.module+el8.1.1+4794+c82b6e09.x86_64.rpm",
        "postgresql-test-12.1-2.module+el8.1.1+4794+c82b6e09.ppc64le.rpm",
    ]

    # Insert koji RPMs referenced by this advisory
    fake_koji.insert_rpms(
        rpm_filenames,
        koji_dir=koji_dir,
        signing_key="fd431d51",
        build_nvr="postgresql-12-8010120191120141335.e4e244f9",
    )

    # Insert archives referenced by build
    fake_koji.insert_modules(
        [
            "modulemd.aarch64.txt",
            "modulemd.ppc64le.txt",
            "modulemd.s390x.txt",
            "modulemd.x86_64.txt",
            # Also insert some other modules which are NOT referenced by ET,
            # to show that these are correctly filtered out
            "modulemd.src.txt",
            "some-other-module.yaml",
        ],
        build_nvr="postgresql-12-8010120191120141335.e4e244f9",
    )

    items = list(source)

    errata_items = [i for i in items if isinstance(i, ErratumPushItem)]
    rpm_items = [i for i in items if isinstance(i, RpmPushItem)]
    modulemd_items = [i for i in items if isinstance(i, ModulemdPushItem)]

    # It should have found the one advisory
    assert len(errata_items) == 1
    errata_item = errata_items[0]

    # Validate a few of the advisory fields
    assert str(errata_item) == "RHEA-2020:0346: new module: postgresql:12"

    # Notably, advisory pkglist should contain one collection per module
    assert len(errata_item.pkglist) == 4

    modules = [str(collection.module) for collection in errata_item.pkglist]
    assert sorted(modules) == [
        "postgresql:12:8010120191120141335:e4e244f9:aarch64",
        "postgresql:12:8010120191120141335:e4e244f9:ppc64le",
        "postgresql:12:8010120191120141335:e4e244f9:s390x",
        "postgresql:12:8010120191120141335:e4e244f9:x86_64",
    ]

    # It should have found all the RPMs
    found_rpm_names = [item.name for item in rpm_items]
    assert sorted(found_rpm_names) == sorted(rpm_filenames)

    # It should have found the modulemd files
    assert sorted(modulemd_items, key=lambda item: item.src) == [
        ModulemdPushItem(
            name="modulemd.aarch64.txt",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/postgresql/12/8010120191120141335.e4e244f9",
                "files/module/modulemd.aarch64.txt",
            ),
            dest=["rhel-8-for-aarch64-appstream-rpms__8"],
            md5sum=None,
            sha256sum=None,
            origin="RHEA-2020:0346",
            build="postgresql-12-8010120191120141335.e4e244f9",
            signing_key=None,
        ),
        ModulemdPushItem(
            name="modulemd.ppc64le.txt",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/postgresql/12/8010120191120141335.e4e244f9",
                "files/module/modulemd.ppc64le.txt",
            ),
            dest=["rhel-8-for-ppc64le-appstream-rpms__8"],
            md5sum=None,
            sha256sum=None,
            origin="RHEA-2020:0346",
            build="postgresql-12-8010120191120141335.e4e244f9",
            signing_key=None,
        ),
        ModulemdPushItem(
            name="modulemd.s390x.txt",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/postgresql/12/8010120191120141335.e4e244f9",
                "files/module/modulemd.s390x.txt",
            ),
            dest=["rhel-8-for-s390x-appstream-rpms__8"],
            md5sum=None,
            sha256sum=None,
            origin="RHEA-2020:0346",
            build="postgresql-12-8010120191120141335.e4e244f9",
            signing_key=None,
        ),
        ModulemdPushItem(
            name="modulemd.x86_64.txt",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/postgresql/12/8010120191120141335.e4e244f9",
                "files/module/modulemd.x86_64.txt",
            ),
            dest=["rhel-8-for-x86_64-appstream-rpms__8"],
            md5sum=None,
            sha256sum=None,
            origin="RHEA-2020:0346",
            build="postgresql-12-8010120191120141335.e4e244f9",
            signing_key=None,
        ),
    ]
