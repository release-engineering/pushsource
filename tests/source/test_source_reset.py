from pytest import raises

from pushsource import Source, SourceUrlError


def test_reset_removes_custom_backend():
    """reset removes a custom registered backend."""

    created = []
    source_instance = object()

    def source_factory(*args, **kwargs):
        created.append(True)
        return source_instance

    Source.register_backend("mytest", source_factory)

    # I can get an instance of it now
    assert Source.get("mytest:")
    assert len(created) == 1

    # But if I reset...
    Source.reset()

    # Then I can't get it any more
    with raises(SourceUrlError) as exc_info:
        Source.get("mytest:")
    assert len(created) == 1

    assert "no registered backend 'mytest'" in str(exc_info)


def test_reset_restores_overridden_backend():
    """reset restores the original backend for anything which has been
    overridden."""

    # I can get an instance of a built-in backend, like 'staged'.
    # Note: doesn't matter that we're pointing at nonexistent directory
    # (reading doesn't happen until we iterate)
    Source.get("staged:/notexist")

    created = []
    source_instance = object()

    def source_factory(*args, **kwargs):
        created.append(True)
        return source_instance

    # Can override the built-in 'staged' backend.
    Source.register_backend("staged", source_factory)

    # Now it will use what I registered
    assert Source.get("staged:/notexist")
    assert len(created) == 1

    # But if I reset...
    Source.reset()

    # Then I'm not getting what I registered any more, but I'm
    # still getting something OK
    new_src = Source.get("staged:/notexist")
    assert new_src
    assert new_src is not source_instance
    assert len(created) == 1
