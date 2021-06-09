from pytest import fixture
from mock import patch

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
