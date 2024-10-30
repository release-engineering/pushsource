import logging
from functools import partial

from os import scandir

LOG = logging.getLogger("pushsource")


class TypeHandler(object):
    # Decorator for handling specific file directories (e.g. "FILES", "ISOS" etc)
    HANDLERS = {}

    def __init__(self, type_name, accepts=lambda entry: entry.is_file()):
        self.type_name = type_name
        self.accepts = accepts

    def __call__(self, fn):
        TypeHandler.HANDLERS[self.type_name] = (fn, self.accepts)
        return fn


handles_type = TypeHandler


class StagedBaseMixin(object):
    # Helper mixin for staged classes handling specific pieces of content.
    _FILE_TYPES = {}

    def __init__(self, *args, **kwargs):
        super(StagedBaseMixin, self).__init__(*args, **kwargs)
        self._FILE_TYPES = self._FILE_TYPES.copy()
        for typename in TypeHandler.HANDLERS:
            fn, accepts = TypeHandler.HANDLERS[typename]
            bound_fn = partial(fn, self)
            self._FILE_TYPES[typename] = partial(
                self.__mixin_push_items, delegate=bound_fn, accepts=accepts
            )

    def __mixin_push_items(self, leafdir, metadata, delegate, accepts):
        out = []

        LOG.debug("Looking for files in %s", leafdir)

        for entry in scandir(leafdir.path):
            if accepts(entry):
                item = delegate(leafdir, metadata, entry)
                if item:
                    out.append(item)

        return out
