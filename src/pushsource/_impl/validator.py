import logging

import jsonschema

from .schema import get_schema


LOG = logging.getLogger("pushsource")


class Validator(object):
    """A helper to validate jsonschemas with some friendlier
    log messages applied on validation errors.
    """

    def __init__(self, schema_name, ids=None):
        """Obtain a validator.

        Arguments:

            schema_name (str)
                Name of schema within pushsource library to be used by
                this validator (e.g. "errata")

            ids (list[str])
                A list of attributes which can be used to identify user-meaningful
                objects in validated data.

                When validation fails, the innermost found object having any of these
                attributes will be considered the most relevant object to report to
                the user, and the attribute value will be included in a log message.

                Example: if validation fails on an object like this:

                  {'object1': {'filename': 'foobar', 'metadata': {... FAILS HERE}}}

                ... and if 'ids' contains 'filename', then the validation failure
                will be logged as "foobar is not valid".
        """
        self._schema = get_schema(schema_name)
        self._ids = ids or []

    def _get_subobject_label(self, data, error):
        # Given data which has failed validation plus the validation error,
        # try to obtain and return the most user-meaningful label for the
        # piece which failed validation.

        # This is where the error occurred, for example if:
        #      data = {'foo': [{'bar': <something invalid>}]}
        # then path = ['foo', 0, 'bar']
        #
        # note: 'absolute_path' was 'path' in jsonschema <= 2.3.0.
        path = list(getattr(error, "absolute_path", error.path))

        # Build up a list of objects we were validating.
        sub = data
        objects = [sub]
        while path:
            sub = sub[path[0]]
            objects.append(sub)
            path = path[1:]

        # Reverse the list, then we have the objects in order from
        # innermost to outermost being validated, e.g. if:
        #      data = {'foo': [{'bar': <something invalid>}]}
        # then
        #      objects = [<bar dict>, <list containing bar dict>, <foo dict>]
        objects.reverse()

        # Only dicts are able to be checked
        objects = [o for o in objects if isinstance(o, dict)]

        # The innermost object which contains one of our configured 'ids'
        # is the most meaningful object to the user.
        for o in objects:
            for label in self._ids:
                if o.get(label):
                    return o[label]

    def validate(self, data, data_label):
        """Validate an object against the configured schema.

        This method behaves the same as `jsonschema.validate`, except that
        if a validation error occurs, a user-oriented message is logged at
        ERROR level before an exception is raised.

        The idea is that a typical end-user has a better chance of understanding
        a basic error message pointing at which piece of data failed validation,
        than they do of understanding the jsonschema ValidationError in raw form.

        Arguments:

            data (object)
                Any object to be validated.

            data_label (str)
                A label for the data being validated.

                This should be a brief string which would make sense to the end-user
                which will help identify the data failing validation.

                For example, if you are validating JSON loaded from a file,
                passing the filename as data_label would be reasonable - it will tell
                the user which file failed validation.
        """

        try:
            jsonschema.validate(data, self._schema)
        except jsonschema.ValidationError as error:
            label = self._get_subobject_label(data, error)

            if label:
                # We found some meaningful label for the particular
                # item failing validation - great, mention that object
                # (and also the containing object)
                label = "%s (in %s)" % (label, data_label)
            else:
                # We didn't find anything, oh well...
                # Just mention the outermost object.
                label = data_label

            LOG.error("%s is not valid", label)

            raise
