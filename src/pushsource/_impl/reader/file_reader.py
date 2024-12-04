import os

from .base import ContentReader


class FileContentReader(ContentReader):
    """
    A file content reader that provides read-only, non-seekable access to a file at the given src.
    """

    def __init__(self, filepath):
        """
        Initialize with the path to the file.

        Parameters:
            filepath (str): Path to the file to be read.
        """
        self._filepath = filepath
        self._file_obj = None

    @property
    def name(self):
        """Returns the file path"""
        return self._filepath

    def read(self, size=-1):
        """
        Read up to `size` bytes from the file.

        Args:
            size (int): The number of bytes to read. If negative, reads the entire file.

        Returns:
            bytes: The content read from the file.
        """
        if self._file_obj is None:
            self._file_obj = open(self._filepath, "rb")
        return self._file_obj.read(size)

    def exist(self):
        """Returns True if the file exists at the given file path"""
        return os.path.exists(self._filepath)

    def close(self):
        if self._file_obj is not None:
            self._file_obj.close()
            self._file_obj = None

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


ContentReader.register_reader("file", FileContentReader)
