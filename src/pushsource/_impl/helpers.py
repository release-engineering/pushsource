import os
import logging
import time
from concurrent.futures import wait, FIRST_COMPLETED

from urllib.parse import urlparse, ParseResult

LOG = logging.getLogger("pushsource")


def list_argument(value, retain_none=False):
    """Convert an argument into a list:

    - if the value is already a list, it's returned verbatim
    - if the value is None and retain_none is False, an empty list is returned
    - if the value is None and retain_none is True, None is returned
    - if the value is a string, it's split on ","
    - otherwise, the value is wrapped in a list

    This function is intended for use in :class:`~pushsource.Source` constructors
    to ease the processing of arguments passed via URL.

    Parameters:
        value
            Any value.

    Returns:
        list
            ``value`` converted to or wrapped into a list.
        None
            if input was None and retain_none is True.
    """
    if isinstance(value, list):
        return value
    if value is None and retain_none:
        return value
    if not value:
        return []
    if isinstance(value, str):
        return value.split(",")
    return [value]


def try_int(value):
    """Convert strings into integers where possible.

    This function is intended for use in :class:`~pushsource.Source` constructors
    to ease the processing of arguments passed via URL.

    Parameters:
        value
            Any value.

    Returns:
        int
            ``value`` converted to an integer, if it was a string representation
            of an integer.
        other
            ``value`` unmodified, in any other case.
    """
    if not isinstance(value, str):
        return value
    try:
        return int(value)
    except ValueError:
        return value


def try_bool(value):
    """Convert values into booleans where possible.

    This function is intended for use in :class:`~pushsource.Source` constructors
    to ease the processing of arguments passed via URL (which always arrive as a string).

    Parameters:
        value
            Any value.

    Returns:
        bool
            ``value`` converted to a boolean, if it was a string representation
            of a boolean.
        other
            ``value`` unmodified, in any other case.
    """
    if not isinstance(value, str):
        return value

    value = value.lower()
    if value in ["1", "true", "yes"]:
        return True
    if value in ["", "0", "false", "no"]:
        return False
    raise ValueError("Expected a boolean, got %s" % repr(value))


def force_https(url):
    """Force ``url`` to use https as its scheme.

    Parameters:
        url: str
            A string representation of a URL.

    Returns:
        str
            ``url`` with its scheme replaced with https.

    Throws:
        Any potential error thrown by the urlparse function during parsing.
    """
    parsed = urlparse(url)
    with_https = ParseResult("https", *parsed[1:])
    return with_https.geturl()


def as_completed_with_timeout_reset(futures, timeout):
    """
    Yields any finished future within time alloted by timeout, raises TimeoutError otherwise.
    Futures are allowed to continue over timeout, if any processing in caller is slow.
    Timeout is not applied to futures themselves but rather to wait() call, which means
    that this function allows to yield all quicker futures and tries to wait for slow ones.

    Parameters:
        futures: List[Future]
            list of futures

        timeout: int or float
            Timeout used for wait() calls

    Returns:
        Future
            finished Future object

    Throws:
        TimeoutError, if waiting for some Future to finish in wait() call takes more
        time than given timeout.
    """
    total_futures = len(futures)
    pending = futures
    while pending:
        finished, pending = wait(pending, timeout=timeout, return_when=FIRST_COMPLETED)
        # no future finished in timeout given, raise TimeoutError
        if not finished:
            raise TimeoutError(
                "%d (of %d) futures unfinished" % (len(pending), total_futures)
            )

        for fs in finished:
            yield fs


def wait_exist(path, timeout, poll_rate):
    """
    Wait until a file begins to exist or until a timeout is reached.

    Args:
        path (str):
            Path to check.
        timeout (int):
            Maximum time to wait.
        poll_rate (int):
            How often to check for file's existence.
    """
    max_attempts = timeout // poll_rate
    for i in range(max_attempts + 1):
        if os.path.exists(path):
            break
        if i == max_attempts:
            if max_attempts > 0:
                LOG.warning(
                    "File %s is missing after %s seconds",
                    path,
                    timeout,
                )
            break
        LOG.info(
            "Waiting for %s seconds for file %s to appear",
            poll_rate,
            path,
        )
        time.sleep(poll_rate)
