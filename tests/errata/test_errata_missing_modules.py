from pytest import raises
from mock import patch
from pushsource import Source


@patch(
    "pushsource._impl.backend.koji_source.rpmlib.get_keys_from_header",
    return_value="fd431d51",
)
@patch("pushsource._impl.backend.koji_source.rpmlib.get_rpm_header")
def test_errata_modules_via_koji(
    mock_get_rpm_header,
    mock_get_keys_from_headers,
    fake_errata_tool,
    fake_koji,
    koji_dir,
):
    """Errata source gives an error if ET requested modules which don't exist in koji"""

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

    # Insert archives referenced by build and we deliberately leave out
    # a couple of the modules which ET expects to exist
    fake_koji.insert_modules(
        ["modulemd.aarch64.txt", "modulemd.ppc64le.txt"],
        build_nvr="postgresql-12-8010120191120141335.e4e244f9",
    )

    # Getting push items should fail
    with raises(ValueError) as exc_info:
        list(source)

    # It should tell us exactly why.
    assert (
        "koji build postgresql-12-8010120191120141335.e4e244f9 does not contain "
        "modulemd.s390x.txt, modulemd.x86_64.txt (requested by advisory RHEA-2020:0346)"
    ) in str(exc_info)
