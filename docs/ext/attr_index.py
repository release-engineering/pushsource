# An extension to add an index of attributes within class docs.
#
# For classes using attrs, this will produce a list under the class description
# of the form:
#
#  Attributes:
#    - base-attr [inherited]
#    - other-base-attr [inherited]
#    - my-own-attr
#    - my-other-attr
#    - (...etc)
#
# The motivation is to make it easier to navigate around our quite large set
# of attributes and also to improve visibility of inherited attributes on
# subclasses (without duplicating their entire doc strings).
#
# In principle it works on all attrs-using classes, but is primarily of use
# for PushItem subclasses.


def find_owning_class(klass, attr_name):
    # Given an attribute name and a class on which it was found, return
    # the class which owns that attribute (as opposed to inheriting it)
    for candidate in klass.__mro__:
        if not hasattr(candidate, "__attrs_attrs__"):
            continue

        attr = getattr(candidate.__attrs_attrs__, attr_name)
        if not attr.inherited:
            # It belongs here
            return candidate


def add_attr_index(app, what, name, obj, options, lines):
    if not hasattr(obj, "__attrs_attrs__"):
        return

    attrs = sorted(
        obj.__attrs_attrs__, key=lambda attr: (not attr.inherited, attr.name)
    )
    if not attrs:
        return

    # We've got some attributes. Let's produce an index of them, linking to both
    # the inherited and local attributes.

    lines.extend(["", "**Attributes:**", ""])
    for attr in attrs:
        if attr.inherited:
            klass = find_owning_class(obj, attr.name)
            if klass:
                line = "* :meth:`~pushsource.%s.%s` *[inherited]*" % (
                    klass.__name__,
                    attr.name,
                )
        else:
            line = "* :meth:`%s`" % attr.name

        lines.append(line)
    lines.extend(["", ""])


def setup(app):
    # entrypoint invoked by sphinx when extension is loaded
    app.connect("autodoc-process-docstring", add_attr_index)
