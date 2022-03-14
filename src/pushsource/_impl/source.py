import inspect
import functools
from threading import Lock

import pkg_resources

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


class SourceWrapper(object):
    # Internal class to ensure that all source instances support enter/exit
    # for with statements even if underlying instance doesn't implement it
    # (since it originally was not mandatory).
    def __init__(self, delegate):
        self.__delegate = delegate

    def __iter__(self):
        return self.__delegate.__iter__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @classmethod
    def _maybe_wrap(cls, delegate):
        if hasattr(delegate, "__enter__"):
            # no wrapping needed
            return delegate
        # wrap with a no-op enter/exit
        return cls(delegate)


class Source(object):
    """A source of push items.

    This base class defines the interface for all pushsource backends.
    Instances of a specific backend can be obtained using
    the :meth:`~pushsource.Source.get` method.

    Though not mandatory, instances of ``Source`` are preferably used
    via ``with`` statements to ensure that all resources are cleaned up
    when no longer needed, as in example:

    .. code-block:: python

        with Source.get('some-url') as source:
            for item in source:
                do_something(item)

    Note that the items produced by a source are not bound to the lifecycle
    of a source instance, so it's safe to store them and continue using
    them beyond the end of the ``with`` statement.
    """

    _BACKENDS = {}
    _BACKENDS_RESET = {}
    _INIT_LOCK = Lock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __iter__(self):
        """Iterate over the push items contained within this source.

        Yields a series of :class:`~pushsource.PushItem` instances.
        """
        raise NotImplementedError()

    @classmethod
    def __ensure_init(cls):
        # ensures backends are initialized; this is a one-time operation
        # the first time get() is called.
        if not cls._BACKENDS_RESET:
            with cls._INIT_LOCK:
                if not cls._BACKENDS_RESET:
                    cls.__load_entrypoints()
                    cls._BACKENDS_RESET = cls._BACKENDS.copy()

    @classmethod
    def __load_entrypoints(cls):
        for ep in pkg_resources.iter_entry_points("pushsource"):
            # Note we're just trying to import the entry point's module, not
            # call any method.
            # resolve vs load is for different versions of pkg_resources.
            # Result is assigned to a var to avoid a pylint warning.
            _ = ep.resolve() if hasattr(ep, "resolve") else ep.load(require=False)

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
        cls.__ensure_init()

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

        # We need to know whether the source backend accepts a 'url' argument,
        # in which case the next block should kick in. If the backend is a partial
        # created by us, this info may be available in __pushsource_accepts_url.
        # See commentary a bit later where this is set.
        accepts_url = getattr(klass, "__pushsource_accepts_url", "url" in sig.args)

        if accepts_url and parsed.path is not query:
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
            kwargs = url_kwargs.copy()
            kwargs.update(inner_kwargs)
            return SourceWrapper._maybe_wrap(klass(*inner_args, **kwargs))

        # If the source accepts a 'url' argument, that affects how source
        # URLs are parsed, as described in the "Implementing a backend"
        # docs. This must be carried through when partially binding a source.
        # Stash it in this attribute which we can read back later.
        #
        # TODO: please drop this when python2 goes away.
        # In modern versions of python, functools.wraps already propagates
        # the signature of the wrapped function, so it is likely possible
        # to drop this and slightly change above code to use inspect.signature,
        # then it will "just work".
        setattr(partial_source, "__pushsource_accepts_url", accepts_url)

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

    @classmethod
    def reset(cls):
        """Reset the library to the default configuration.

        This method will undo the effect of any prior calls to
        :meth:`~pushsource.Source.register_backend`, restoring only the
        default backends provided by the pushsource library.

        This may be used from within tests to ensure a known state.

        .. versionadded:: 2.6.0
        """
        cls.__ensure_init()
        cls._BACKENDS = cls._BACKENDS_RESET.copy()
