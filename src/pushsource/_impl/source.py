import inspect
import functools

from six.moves.urllib import parse


def getfullargspec(x):
    # Helper for py2 vs py3 differences.

    if not hasattr(inspect, "getfullargspec"):  # pragma: no cover
        # 1. Must use older, deprecated getargspec.
        # 2. getfullargspec works fine when called on a class and
        #    returns spec of constructor, but getargspec complains.
        #    Make it work more like getfullargspec.
        if isinstance(x, type):
            x = x.__init__
        return inspect.getargspec(x)  # pylint: disable=deprecated-method

    return inspect.getfullargspec(x)


class SourceUrlError(ValueError):
    """Errors of this type are raised when an invalid URL is provided
    to :meth:`~pushsource.Source.get` and related methods.
    """


class Source(object):
    """A source of push items.

    This base class defines the interface for all pushsource backends.
    Instances of a specific backend can be obtained using
    the :meth:`~pushsource.Source.get` method.
    """

    _BACKENDS = {}

    def __iter__(self):
        """Iterate over the push items contained within this source.

        Yields a series of :class:`~pushsource.PushItem` instances.
        """
        raise NotImplementedError()

    @classmethod
    def get(cls, source_url, **kwargs):
        """Obtain a push source from the given URL.

        Parameters:
            source_url (str)
                Specifies a push source backend and associated arguments.
                For information about push source URLs, see
                :ref:`urls`.

            kwargs (dict)
                Any additional keyword arguments to be passed into
                the backend.

        Raises:
            SourceUrlError
                If ``source_url`` is not a valid push source URL.

        Returns:
            :class:`~pushsource.Source`
                A new Source instance initialized with the given arguments.
        """
        return cls.get_partial(source_url, **kwargs)()

    @classmethod
    def get_partial(cls, source_url, **kwargs):
        """Obtain a push source constructor from the given URL and arguments.

        This method returns a constructor for a push source (rather than a push source
        instance directly) so that additional arguments may be provided later.

        One of the primary uses of this method is to provide your own preconfigured
        aliases for existing backends, as described in :ref:`binding`.

        Parameters:
            source_url (str)
                Specifies a push source backend and associated arguments.
                For information about push source URLs, see
                :ref:`urls`.

            kwargs (dict)
                Any additional keyword arguments to be passed into
                the backend.

        Raises:
            SourceUrlError
                If ``source_url`` is not a valid push source URL.

        Returns:
            callable
                A callable which accepts any number of keyword arguments
                and returns a :class:`~pushsource.Source`.
        """
        parsed = parse.urlparse(source_url)
        scheme = parsed.scheme

        if not scheme:
            raise SourceUrlError("Not a valid source URL: %s" % source_url)

        if scheme not in cls._BACKENDS:
            raise SourceUrlError(
                "Requested source '%s' but there is no registered backend '%s'"
                % (source_url, scheme)
            )

        klass = cls._BACKENDS[scheme]

        query = parsed.query

        # To make simple URLs less ugly, we'll allow the '?' to be omitted if needed.
        # Example: if "fedkoji" is a source pointing at fedora koji,
        # allow the caller to pass: fedkoji:rpm=python3-3.7.5-2.fc31.x86_64.rpm
        # instead of requiring:     fedkoji:?rpm=python3-3.7.5-2.fc31.x86_64.rpm
        if not query and not parsed.netloc and "=" in parsed.path:
            query = parsed.path

        url_kwargs = parse.parse_qs(query)

        # parse_qs forces everything into lists even if only a single term was given.
        #
        # e.g. arg1=foo&arg1=bar&arg2=baz => {'arg1': ['foo', 'bar'], 'arg2': ['baz']}
        #
        # This is annoying to deal with in source backends, so we'll unwrap anything
        # which had only a single element.
        for key in url_kwargs.keys():
            value = url_kwargs[key]
            if isinstance(value, list) and len(value) == 1:
                url_kwargs[key] = value[0]

        sig = getfullargspec(klass)

        if "url" in sig.args and parsed.path is not query:
            # If the source accepts a url argument, then the 'path' part
            # of the URL we were provided is itself required to be a URL.
            #
            # For example:
            #
            #  errata:https://errata.example.com/foo/bar?arg1=val&arg2=val...
            #
            # The "https://errata.example.com/foo/bar" part was parsed as 'path'
            # above, and is now provided to the source as a URL.
            url_kwargs["url"] = parsed.path

        # Coerce some standard arguments to the right type.
        for (key, converter) in [("threads", int), ("timeout", int)]:
            if key in url_kwargs:
                url_kwargs[key] = converter(url_kwargs[key])

        # TODO: check for some common mistakes here?

        url_kwargs.update(kwargs)

        @functools.wraps(klass)
        def partial_source(*inner_args, **inner_kwargs):
            url_kwargs.update(inner_kwargs)
            return klass(*inner_args, **url_kwargs)

        return partial_source

    @classmethod
    def register_backend(cls, name, factory):
        """Register a new pushsource backend.

        This method allows registering additional backends beyond those
        shipped with the pushsource library. See :ref:`implementing` for
        more information.

        Parameters:
            name (str)
                The name of a backend. This should be a brief unique identifying
                string.

                If a backend of the given name is already registered, it will be
                overwritten.

            factory (callable)
                A callable used to create new instances of the backend.
                When invoked, this callable must return an object which implements
                the :class:`~pushsource.Source` interface.

        Raises:
            TypeError
                If ``factory`` is not callable.
        """
        if not callable(factory):
            raise TypeError("expected callable, got: %s" % repr(factory))

        cls._BACKENDS[name] = factory
