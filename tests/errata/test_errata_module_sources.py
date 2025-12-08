import os

import pytest

from pushsource import Source, ModuleMdSourcePushItem
from mock import patch

@pytest.fixture
def source_factory(fake_errata_tool, fake_koji, koji_dir):
    ctor = Source.get_partial(
        "errata:https://errata.example.com",
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
        build_nvr="postgresql-12.1-2.module+el8.1.1+4794+c82b6e09",
    )

    # Insert archives referenced by build
    fake_koji.insert_modules(
        [
            "modulemd.aarch64.txt",
            "modulemd.ppc64le.txt",
            "modulemd.s390x.txt",
            "modulemd.x86_64.txt",
            "modulemd.src.txt",
        ],
        build_nvr="postgresql-12-8010120191120141335.e4e244f9",
    )

    yield ctor

@patch("pushsource._impl.backend.koji_source.rpmlib.get_keys_from_header", return_value="fd431d51")
@patch("pushsource._impl.backend.koji_source.rpmlib.get_rpm_header")
def test_errata_module_sources(mock_get_rpm_header, mock_get_keys_from_headers, source_factory, koji_dir):
    """Errata source can provide ModuleMdSourcePushItems, typical scenario."""

    source = source_factory(errata="RHEA-2020:0346")

    items = list(source)

    src_items = [i for i in items if isinstance(i, ModuleMdSourcePushItem)]

    # Should have found that one item
    assert src_items == [
        ModuleMdSourcePushItem(
            name="modulemd.src.txt",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/postgresql/12/8010120191120141335.e4e244f9",
                "files/module/modulemd.src.txt",
            ),
            dest=[
                # It should be pointing at the path from get_ftp_paths response
                "/ftp/pub/redhat/linux/enterprise/AppStream-8.1.1.MAIN/en/os/modules/"
            ],
            md5sum=None,
            sha256sum=None,
            origin="RHEA-2020:0346",
            build="postgresql-12-8010120191120141335.e4e244f9",
            signing_key=None,
        )
    ]

@patch("pushsource._impl.backend.koji_source.rpmlib.get_keys_from_header", return_value="fd431d51")
@patch("pushsource._impl.backend.koji_source.rpmlib.get_rpm_header")
def test_errata_module_sources_no_ftp_paths(mock_get_rpm_header, mock_get_keys_from_headers, source_factory):
    """Errata source skips ModuleMdSourcePushItems if ET does not request any
    FTP paths for modules."""

    source = source_factory(errata="RHEA-2020:0346-no-module-ftp-paths")

    items = list(source)

    src_items = [i for i in items if isinstance(i, ModuleMdSourcePushItem)]

    # Should not have found anything since ET reported no dests for modules in FTP paths
    assert src_items == []

@patch("pushsource._impl.backend.koji_source.rpmlib.get_keys_from_header", return_value="fd431d51")
@patch("pushsource._impl.backend.koji_source.rpmlib.get_rpm_header")
def test_errata_module_sources_no_cdn_list(mock_get_rpm_header, mock_get_keys_from_headers, source_factory, caplog):
    """Errata source skips ModuleMdSourcePushItems if ET does not present those
    modules in get_advisory_cdn_file_list."""

    source = source_factory(errata="RHEA-2020:0346-no-cdn-list")

    items = list(source)

    src_items = [i for i in items if isinstance(i, ModuleMdSourcePushItem)]

    # Should not have found anything since ET didn't return the modules in the file list
    assert src_items == []

    # Should warn us about the unusual situation.
    assert (
        "Erratum RHEA-2020:0346: ignoring module(s) from ftp_paths "
        "due to absence in cdn_file_list: postgresql-12-8010120191120141335.e4e244f9"
        in caplog.text
    )

@patch("pushsource._impl.backend.koji_source.rpmlib.get_keys_from_header", return_value="fd431d51")
@patch("pushsource._impl.backend.koji_source.rpmlib.get_rpm_header")
def test_errata_module_missing_sources(mock_get_rpm_header, mock_get_keys_from_headers, source_factory, fake_koji):
    """Errata source gives fatal error if ET requests some FTP paths for modules,
    yet no module sources exist on koji build."""
    source = source_factory(errata="RHEA-2020:0346")

    fake_koji.remove_archive(
        "modulemd.src.txt", "postgresql-12-8010120191120141335.e4e244f9"
    )

    # It should raise.
    with pytest.raises(ValueError) as exc_info:
        list(source)

    # It should tell us exactly what the problem was.
    assert (
        "Erratum RHEA-2020:0346: missing modulemd sources on koji build(s): "
        "postgresql-12-8010120191120141335.e4e244f9"
    ) in str(exc_info)
