from pytest import raises, fixture
from mock import patch

from .fake_errata_tool import FakeErrataToolController

from pushsource import Source, ErratumPushItem, ErratumReference, RpmPushItem


@fixture
def fake_errata_tool():
    controller = FakeErrataToolController()
    with patch("pushsource._impl.backend.errata_source.ServerProxy") as mock_proxy:
        mock_proxy.side_effect = controller.proxy
        yield controller


def test_errata_files_needs_koji_url(fake_errata_tool):
    """Can't obtain errata referring to files if koji source URL is missing"""

    source = Source.get("errata:https://errata.example.com?errata=RHSA-2020:0509")

    with raises(Exception) as exc:
        list(source)

    assert "A Koji source is required but none is specified" in str(exc.value)


def test_errata_missing_koji_rpms(fake_errata_tool):
    """Can't obtain errata if referenced RPMs are not in koji"""

    class AllMissingKojiSource(object):
        def __init__(self, **kwargs):
            pass

        def __iter__(self):
            yield RpmPushItem(
                name="sudo-1.8.25p1-4.el8_0.3.x86_64.rpm", state="NOTFOUND"
            )
            yield RpmPushItem(
                name="sudo-1.8.25p1-4.el8_0.3.ppc64le.rpm", state="NOTFOUND"
            )

    Source.register_backend("missingkoji", AllMissingKojiSource)

    source = Source.get(
        "errata:https://errata.example.com?errata=RHSA-2020:0509",
        koji_source="missingkoji:",
    )

    with raises(Exception) as exc:
        list(source)

    # It should raise because an RPM referred by ET was not found in koji
    assert (
        "Advisory refers to sudo-1.8.25p1-4.el8_0.3.x86_64.rpm but RPM was not found in koji"
        in str(exc.value)
    )


def test_errata_mismatch_koji_rpms(fake_errata_tool):
    """Can't obtain errata if referenced RPMs in koji belong to wrong build"""

    class BadKojiSource(object):
        def __init__(self, **kwargs):
            pass

        def __iter__(self):
            yield RpmPushItem(
                name="sudo-1.8.25p1-4.el8_0.3.x86_64.rpm",
                state="PENDING",
                build="some-unexpected-build-1.2.3",
            )

    Source.register_backend("badkoji", BadKojiSource)

    source = Source.get(
        "errata:https://errata.example.com?errata=RHSA-2020:0509",
        koji_source="badkoji:",
    )

    with raises(Exception) as exc:
        list(source)

    # It should raise because RPM was found, but in a different build
    # than the one expected by ET
    assert "Push item NVR is wrong" in str(exc.value)
