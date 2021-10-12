import six

# in py2 TimeoutError is not built-in exception
if six.PY2:
    from concurrent.futures import TimeoutError  # pylint: disable=redefined-builtin

import pytest

from pushsource._impl.helpers import as_completed_with_timeout_reset
from more_executors.futures import f_return
from more_executors import Executors
from time import sleep


def test_as_completed_with_timeout_reset():
    # tests correctly yielded futures from as_completed_with_timeout_reset()
    futures = [f_return(1), f_return(2)]
    current = set()
    for ft in as_completed_with_timeout_reset(futures, timeout=1):
        value = ft.result()
        current.add(value)

    expected = set([1, 2])
    assert current == expected


def test_as_completed_with_timeout_reset_raises_timeout_error():
    # tests raised TimeoutError when futures are slow
    executor = Executors.thread_pool(1)
    ft_1 = executor.submit(sleep, 1)
    ft_2 = executor.submit(sleep, 0.5)

    futures = [ft_1, ft_2]
    with pytest.raises(TimeoutError) as exc:
        for _ in as_completed_with_timeout_reset(futures, timeout=0.1):
            pass

    assert str(exc.value) == "2 (of 2) futures unfinished"


def test_as_completed_with_timeout_reset_slow_caller():
    # simulates slow caller, as_completed_with_timeout_reset() won't raise
    # spurious TimeoutError
    executor = Executors.thread_pool(1)
    ft_1 = executor.submit(sleep, 0.2)
    ft_2 = executor.submit(sleep, 0.3)

    futures = [ft_1, ft_2]
    for ft in as_completed_with_timeout_reset(futures, timeout=0.5):
        ft.result()
        # simulate slow caller
        sleep(1.5)
    # no exception raised
