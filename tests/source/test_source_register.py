from pushsource import Source


def test_get_registered_partial():
    """Can register a source obtained via get_partial, then get source using registered scheme."""
    errata_example = Source.get_partial("errata:https://errata.example.com")
    Source.register_backend("errata-example", errata_example)

    # We should now be able to request sources using et_example scheme.
    # We're just verifying that the call obtains a source, without crashing.
    assert Source.get("errata-example:errata=ABC-123")
