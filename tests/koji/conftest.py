from pytest import fixture
from mock import patch

from pushsource._impl.backend import koji_source

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


@fixture(autouse=True)
def fast_retry(monkeypatch):
    # Force a custom retry policy so that tests which simulate errors
    # don't spent as much time retrying as they would in production.
    monkeypatch.setattr(koji_source, "RETRY_ARGS", {"max_sleep": 0.0001})
