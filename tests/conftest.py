import copy
from pytest import fixture

from pushsource import Source


@fixture(autouse=True)
def clean_backends():
    """Reset any modifications of Source._BACKENDS performed during tests."""
    backends = copy.deepcopy(Source._BACKENDS)
    yield
    Source._BACKENDS = backends
