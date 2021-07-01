from pushsource import Source, PushItem

# Just some basic push items for test

ITEMS = [PushItem(name="item1"), PushItem(name="item2")]


class BasicInheritedSource(Source):
    # A source which simply yields some stuff and didn't implement enter/exit
    def __init__(self):
        pass

    def __iter__(self):
        for item in ITEMS:
            yield item


class CustomSource(Source):
    # A more complex source for testing with get_partial and custom enter/exit
    def __init__(self, a, b, c, spy):
        self.a = a
        self.b = b
        self.c = c
        self.spy = spy

    def __enter__(self):
        self.spy.append("enter %s" % ([self.a, self.b, self.c]))
        return self

    def __exit__(self, *_args):
        self.spy.append("exit %s" % ([self.a, self.b, self.c]))

    def __iter__(self):
        for item in ITEMS:
            yield item


def test_basic_inherited_source():
    """Basic inherited push source can be used via with statement."""
    Source.register_backend("basic", BasicInheritedSource)

    with Source.get("basic:") as source:
        assert list(source) == ITEMS


def test_basic_iterable_source():
    """Basic push source returning non-class iterable can be used via with statement."""
    Source.register_backend("iterable", lambda *_: ITEMS)

    # Even though lists don't have enter/exit, it should be automatically wrapped here
    # so that it works.
    with Source.get("iterable:") as source:
        assert list(source) == ITEMS


def test_custom_source():
    """A push source with args, custom enter/exit and used with get_partial works."""
    Source.register_backend("custom-base", CustomSource)

    spy = []
    Source.register_backend("custom-spy", Source.get_partial("custom-base:", spy=spy))

    Source.register_backend("custom1", Source.get_partial("custom-spy:", a=123))
    Source.register_backend("custom2", Source.get_partial("custom1:", b=234))
    Source.register_backend("custom3", Source.get_partial("custom2:", c=456))

    # Now use the source while going through multiple layers.
    with Source.get("custom3:") as source:
        assert list(source) == ITEMS

    # the enter/exit should propagate all the way through, just once.
    assert spy == ["enter [123, 234, 456]", "exit [123, 234, 456]"]
