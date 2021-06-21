import six


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
    if isinstance(value, six.string_types):
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
    if not isinstance(value, six.string_types):
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
    if not isinstance(value, six.string_types):
        return value

    value = value.lower()
    if value in ["1", "true", "yes"]:
        return True
    elif value in ["", "0", "false", "no"]:
        return False
    raise ValueError("Expected a boolean, got %s" % repr(value))
