import os

from pushsource import Source, ProductIdPushItem

DATADIR = os.path.join(os.path.dirname(__file__), "data")


def test_staged_unsupported(caplog):
    staged_dir = os.path.join(DATADIR, "unsupported")
    source = Source.get("staged:" + staged_dir)

    files = list(source)

    # It should not find anything
    assert files == []

    # But it should log about some unsupported files
    for path in ["dest2/DOCKER/dimg1", "dest2/DOCKER/dimg2"]:
        msg = "Unsupported content found: %s" % os.path.join(staged_dir, path)
        assert msg in caplog.messages
