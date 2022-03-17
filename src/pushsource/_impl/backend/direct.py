import os

from ..source import Source
from ..model import (
    FilePushItem,
    DirectoryPushItem,
    CompsXmlPushItem,
    RpmPushItem,
    ModuleMdPushItem,
    ModuleMdSourcePushItem,
    ProductIdPushItem,
)
from ..helpers import list_argument


class DirectSource(Source):
    # A source which directly constructs a single item from given arguments.
    #
    # For example:
    #   - "file:/some/file.txt"
    #   - will yield a FilePushItem(name="file.txt", src="/some/file.txt")
    #
    # Note that this class is not public API. Instances of this source can
    # be obtained only by URL, using the names registered toward the end
    # of this file.

    def __init__(self, item):
        self.__item = item

    def __iter__(self):
        yield self.__item

    @classmethod
    def new_source(cls, item_class, url, dest=None, **kwargs):
        # Make a new DirectSource instance using a specified PushItem
        # class, along with arguments passed by the caller in the pushsource
        # URL.
        #
        # Example:
        #
        # - if someone calls: Source.get("file:/somefile?dest=a,b&foo=bar")
        # - then:
        #   - item_class is FilePushItem (see end of this file)
        #   - url is "/somefile"
        #   - dest is "a,b"
        #   - kwargs is {"foo": "bar"}

        # Prepare attributes for constructing the item.
        #
        # Note, the attrs listed before update(kwargs) can be
        # overridden by the caller, while later ones can't.
        item_attrs = {}
        item_attrs["origin"] = "direct"
        item_attrs["name"] = os.path.basename(url)
        item_attrs.update(kwargs)
        item_attrs["src"] = url
        item_attrs["dest"] = sorted(list_argument(dest))
        item = item_class(**item_attrs)
        return cls(item)


def register(name, item_class):
    def factory(url, **kwargs):
        return DirectSource.new_source(item_class, url, **kwargs)

    Source.register_backend(name, factory)


register("file", FilePushItem)
register("dir", DirectoryPushItem)
register("rpm", RpmPushItem)
register("comps", CompsXmlPushItem)
register("modulemd", ModuleMdPushItem)
register("modulemd-src", ModuleMdSourcePushItem)
register("productid", ProductIdPushItem)
