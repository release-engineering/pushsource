class TinyCache(object):
    """A tiny specialized cache capable of reusing (very) recent values.

    These caches are meant to be used as attr field converters, with one
    cache created per cacheable field.

    Whenever a new value for that field is about to be saved, the cache
    will first be consulted. If the new value is equal to the last couple
    of values for the same field (across all constructed objects), then
    the value from cache will be returned instead.

    The caching strategy may seem odd, but it works out well due to the
    way push items tend to be constructed in practice. For example: it
    is common for every RPM in a push to use the same signing key. In
    that scenario, this cache will allow every signing_key field to
    reference exactly the same string rather than a copy.
    Similarly, it is common to construct many items having the same
    'dest'.

    Compared to a more conventional cache storing some values in a list
    or dict, this has the advantage that the cache size is always fixed
    and very small, meaning it is very unlikely that the cache overhead
    can exceed the savings from using the cache.

    Here are some measurements of the impact of this caching on a real
    data set of ~52,000 push items:

    +------------------+-----------+---------------+
    | case             | mem (KiB) | total objects |
    +==================+===========+===============+
    | no cache (min)   | 103928    | 261182        |
    | no cache (max)   | 120096    | 261420        |
    | tiny cache (min) | 98472     | 252582        |
    | tiny cache (max) | 109608    | 252466        |
    +------------------+-----------+---------------+

    We create about 10,000 less python objects in total and reduce
    push item memory usage between 5% .. 13%.

    It is of course only safe for use on immutable types.
    """

    __slots__ = ("last1", "last2", "cache_type", "converter")

    def __init__(self, cache_type, converter=lambda x: x):
        """Construct a cache.

        Arguments:
            cache_type
                Type(s) used for an isinstance() check.

                Only values of this type are eligible for caching;
                anything else will be returned as-is.

            converter
                A callable to convert input values before caching.

                TinyCache is meant to be used as an attrs field converter.
                This argument can be used to chain onto another converter
                where needed.
        """
        # Last two values. Note, the number of lastN here could be anything.
        # It was determined by experiment that N=2 is slightly better than
        # N=1.
        self.last1 = None
        self.last2 = None
        self.cache_type = cache_type
        self.converter = converter

    def __call__(self, value):
        value = self.converter(value)

        if not isinstance(value, self.cache_type):
            # Not eligible for caching
            return value

        # deref these here because we have no synchronization
        # across threads and we don't want this to change between
        # our equality check and returning it.
        # Note: this is thread-safe, but multi-threaded code
        # might lower the cache hit rate.
        last1 = self.last1
        last2 = self.last2

        if value == last1:
            return last1
        if value == last2:
            return last2

        self.last1 = last2
        self.last2 = value
        return value
