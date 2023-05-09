# A replacement for kobo.rpmlib to give a decent error message
# when rpm bindings are not available.

# importer is expected to put a more specific cause here.
CAUSE = RuntimeError("unknown error")

MESSAGE = "kobo.rpmlib is not available (consider 'pip install rpmdyn')"


def not_available(*_args, **_kwargs):
    raise RuntimeError(MESSAGE) from CAUSE


get_rpm_header = not_available
get_keys_from_header = not_available
