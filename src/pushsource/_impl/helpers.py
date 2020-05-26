import six


def list_argument(value):
    """Convert an argument into a list:

    - if the value is already a list, it's returned verbatim
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
    """
    if isinstance(value, list):
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
