from mock import patch

from pushsource import Source


def test_loads_entrypoints(monkeypatch):
    """Source.get ensures 'pushsource' entry points are loaded."""

    # Forcibly set the Source class back to uninitialized state.
    monkeypatch.setattr(Source, "_BACKENDS", {})
    monkeypatch.setattr(Source, "_BACKENDS_RESET", {})

    # Let's set up that some custom backends have registered entry points.
    created1 = []
    created2 = []

    class Backend1(object):
        def __init__(self):
            created1.append(True)

        @classmethod
        def load(cls):
            Source.register_backend("backend1", Backend1)

    class Backend2(object):
        def __init__(self):
            created2.append(True)

        @classmethod
        def load(cls):
            Source.register_backend("backend2", Backend2)

    with patch("pushsource._impl.source.entry_points") as ep:
        ep.return_value = [Backend1, Backend2]

        # I should be able to get instances of those two backends
        assert Source.get("backend1:")
        assert Source.get("backend2:")

    # It should have found them via the expected entry point group
    ep.assert_called_once_with(group="pushsource")

    # Should have created one instance of each
    assert created1 == [True]
    assert created2 == [True]

    # These should also be retained over a reset()
    Source.reset()
    assert Source.get("backend1:")
    assert Source.get("backend2:")
