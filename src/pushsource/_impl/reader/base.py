import logging

from io import BufferedIOBase
from urllib import parse

LOG = logging.getLogger("pushsource")


class ContentReader(BufferedIOBase):
    """
    The base class defines the interface for all the content readers that read
    from various sources like a mounted fs, S3 bucket etc. The readers are
    buffered and non-seekable.

    Instances for a specific reader could be obtained from the method
    :meth:`~pushsource.ContentReader.get`
    Instances of ``ContentReader`` are preferably used via ``with`` statements
    to enusre the file/object is closed and all the resources are cleaned up
    when no longer required.

    .. code-block:: python

        with ContentReader.get('file:file-path') as reader:
            reader.read(size)

    """

    _READERS = {}

    @property
    def name(self):
        """Name or identifier of the object"""
        raise NotImplementedError()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def read(self, size=-1):
        """Read and return up to `size` bytes. If `size` is negative, read until EOF."""
        raise NotImplementedError()

    def read1(self, size=-1):
        """Read and return up to `size` bytes. If `size` is negative, read until EOF."""
        return self.read(size)

    def readable(self):
        """Return True if the stream is readable."""
        return True

    def writable(self):
        """Return False to indicate the stream is not writable."""
        return False

    def seekable(self):
        """Return False to indicate the stream is not seekable."""
        return False

    def exist(self):
        """Return whether the object exist to be read"""
        raise NotImplementedError()

    @classmethod
    def register_reader(cls, content_type, reader):
        """Register a new content reader.

        This method allows registering a new content reader for the content type

        Parameters:
            content_type (str)
                The content type the reader handles. This should be a unique identifying
                string.

                If the given content type is already registered, it will be
                overwritten.

            factory (callable)
                A callable used to create new instances of the reader.
                When invoked, this callable must return an object which implements
                the :class:`~pushsource.ContentReader` interface.

        Raises:
            TypeError
                If ``factory`` is not callable.
        """
        if not callable(reader):
            raise TypeError("expected callable, got: %s" % repr(reader))

        cls._READERS[content_type] = reader

    @classmethod
    def get(cls, path, *args, **kwargs):
        """Obtain a content reader for the given path.

        Parameters:
            path (str)
                Specifies the content reader type, content source and
                associated arguments.

            args (list)
                Any additional arguments to be passed into the content reader

            kwargs (dict)
                Any additional keyword arguments to be passed into the content
                reader.

        Raises:
            ValueError
                If ``path`` is not a valid.

        Returns:
            :class:`~pushsource.ContentReader`
                A new ContentReader instance initialized for the given path with the
                arguments and keyword arguments.
        """
        parsed = parse.urlparse(path)
        content_type = parsed.scheme

        if not content_type:
            raise ValueError("Not a valid path for content reader: %s", path)

        if content_type not in cls._READERS:
            raise ValueError(
                f"Requested {content_type} reader but there's no such registerd reader"
            )

        return cls._READERS[content_type](parsed.path, *args, **kwargs)
