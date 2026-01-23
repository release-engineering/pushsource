import sys

import attr


def add_attr_types(app, what, name, obj, options, lines):
    # If we are generating docs for an attr.ib-defined attribute
    # where 'type' has been set, append this type info to the
    # doc string in the format understood by sphinx.

    if what != "attribute":
        # not an attribute => nothing to do
        return

    if ":type:" in "".join(lines):
        # type has already been documented explicitly, don't
        # try to override it
        return

    components = name.split(".")
    if len(components) != 3 or components[0] != "pushsource":
        # We are looking specifically for public fields of the form:
        # pushsource.<class_name>.<attr_name>
        # For any other cases we'll do nothing.
        return

    klass_name, field_name = components[1:]
    klass = getattr(sys.modules["pushsource"], klass_name)

    if not attr.has(klass):
        # not an attrs-using class, nothing to do
        return

    field = attr.fields_dict(klass).get(field_name)
    if not field:
        # not an attr.ib
        return

    type = field.type
    if not type:
        # no type hint declared, can't do anything
        return

    # phew, after all the above we know we're documenting an attrs-based
    # field and we know exactly what type it is, so add it to the end of
    # the doc string.
    lines.extend(["", ":type: %s" % type.__name__])


def setup(app):
    # entrypoint invoked by sphinx when extension is loaded
    app.connect("autodoc-process-docstring", add_attr_types)
