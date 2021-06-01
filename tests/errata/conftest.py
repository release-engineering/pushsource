from pytest import fixture
from mock import patch

from .fake_errata_tool import FakeErrataToolController
from ..koji.fake_koji import FakeKojiController


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
