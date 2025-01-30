from io import BufferedReader, SEEK_SET, UnsupportedOperation


class PushItemReader(BufferedReader):
    # Internal class to ensure that the file-like content object returned by
    # the push items are read-only and non-seekable with a name attribute.
    def __init__(self, raw, name, **kwargs):
        super(PushItemReader, self).__init__(raw, **kwargs)
        self._name = name

    @property
    def name(self):
        return self._name

    def seekable(self):
        return False

    def seek(self, offset, whence=SEEK_SET):
        raise UnsupportedOperation(f"Seek unsupported while reading {self.name}")
