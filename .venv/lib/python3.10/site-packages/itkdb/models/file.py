from __future__ import annotations

import html
import logging
import mimetypes
import zipfile
from email.message import EmailMessage
from pathlib import Path
from shutil import copyfile
from tempfile import NamedTemporaryFile
from typing import IO

import requests

from itkdb.typing import Self
from itkdb.utils import get_mimetype, sizeof_fmt

log = logging.getLogger(__name__)


class BinaryFile(requests.Response):
    """
    Base class for handling files.

    !!! note "Added in version 0.4.0"

    !!! note "Changed in version 0.6.10"
        - added `__enter__` and `__exit__` methods that map to the underlying `Response` object

    """

    def __init__(self, fptr: IO[bytes], suggested_filename=None, mimetype=None):
        super().__init__()
        self.status_code = 200
        self.fptr = fptr

        self._suggested_filename = suggested_filename
        self._mimetype = mimetype

    @property
    def filename(self) -> str:
        """
        Filename of file on disk.
        """
        return self.fptr.name

    @property
    def suggested_filename(self) -> str | None:
        """
        Suggested filename.
        """
        return self._suggested_filename

    @property
    def extension(self) -> str | None:
        """
        Extension of file.

        Return the extension of the file in this order:
            1. extension using the (suggested) filename taken from response headers (if filename has extension)
            2. extension using mimetype from object initialization
            3. extension using mimetype guessed from file content itself
        """
        if self.suggested_filename and "." in self.suggested_filename:
            extension = self.suggested_filename
        elif self.mimetype:
            if self.mimetype != self.content_type:
                log.warning(
                    "MIME type specified '%s' does not match what the content looks like '%s'. Will return extension based off provided MIME type.",
                    self.mimetype,
                    self.content_type,
                )
            extension = mimetypes.guess_extension(self.mimetype)
        else:
            extension = mimetypes.guess_extension(self.content_type)

        if extension:
            return extension.split(".")[-1].lower()
        return None

    @property
    def size(self) -> int:
        """
        Size of file in bytes.
        """
        # move to end of buffer, returns position
        _size = self.fptr.seek(0, 2)
        # reset back to beginning
        self.fptr.seek(0)
        return _size

    @property
    def size_fmt(self) -> str:
        """
        Human-readable size of file.
        """
        return sizeof_fmt(self.size)

    @property
    def mimetype(self) -> str | None:
        """
        Mimetype of the file.
        """
        return self._mimetype

    @property
    def content(self) -> bytes:
        """
        Raw bytes of the content.
        """
        position = self.fptr.tell()
        content = self.fptr.read()
        self.fptr.seek(position)
        return content

    @property
    def content_type(self) -> str:
        """
        Mimetype of the content.
        """
        return get_mimetype(None, self.fptr)

    def __repr__(self) -> str:
        cls = type(self)
        module = cls.__module__
        qualname = cls.__qualname__

        return f"<{module}.{qualname}(suggested_filename={self.suggested_filename}, size={self.size_fmt} [{self.size} bytes]) file-like object at {self.filename}>"

    def __len__(self) -> int:
        return self.size

    def save(self, filename=None) -> int:
        """
        Save the file.
        """
        new_filename = filename or self.suggested_filename
        if new_filename is None:
            msg = "Please set a filename to save to first."
            raise ValueError(msg)

        copyfile(self.filename, Path(new_filename))
        log.info("Written %s (%d bytes) to %s", self.size_fmt, self.size, new_filename)
        return self.size

    @classmethod
    def from_response(cls, response) -> Self:
        """
        Factory to create BinaryFile-like object from requests.Response.
        """
        if isinstance(response, BinaryFile):
            # Translation already done
            return response

        mimetype = response.headers.get("content-type")
        content_disposition = response.headers.get("content-disposition", "")
        # NB: cgi module deprecated in 3.11
        msg = EmailMessage()
        msg["content-disposition"] = content_disposition
        filename = msg["content-disposition"].params.get("filename")

        temp_fp = (
            NamedTemporaryFile()  # pylint: disable=consider-using-with # noqa: SIM115
        )
        for chunk in response.iter_content(chunk_size=512 * 1024):
            temp_fp.write(chunk)

        temp_fp.seek(0)
        response.close()
        binary = cls(temp_fp, suggested_filename=filename, mimetype=mimetype)

        # from https://github.com/psf/requests/blob/a6cf27a77f6f5dd6116096e95c16e7c1a616b419/src/requests/adapters.py#L359-L394
        for attr in [
            "status_code",
            "headers",
            "encoding",
            "raw",
            "reason",
            "request",
            "url",
        ]:
            setattr(binary, attr, getattr(response, attr))

        return binary

    def __del__(self) -> None:
        if not self.fptr.closed:
            self.fptr.close()


class ImageFile(BinaryFile):
    """
    Class to handle image files.

    !!! note "Changed in version 0.4.0"
    """

    def _repr_png_(self) -> bytes | None:
        if self.extension == "png":
            return self.content
        return None

    def _repr_jpeg_(self) -> bytes | None:
        if self.extension in ["jpeg", "jpg"]:
            return self.content
        return None

    def _repr_svg_(self) -> bytes | None:
        if self.extension == "svg":
            return self.content
        return None


class TextFile(BinaryFile):
    """
    Class to handle text files.

    !!! note "Changed in version 0.4.0"
    """

    def _repr_html_(self):
        return (b"<pre>" + self.content + b"</pre>").decode("utf-8")


class ZipFile(zipfile.ZipFile):
    """
    Class to handle zip files.

    !!! note "Added in version 0.4.0"

    """

    def __init__(self, binary_file):
        self._file = binary_file
        super().__init__(self._file.fptr)

    def _repr_html_(self):
        return (
            html.escape(repr(self))
            + "<ul><li>"
            + "</li><li>".join(html.escape(repr(x)) for x in self.filelist)
            + "</li></ul>"
        )

    @classmethod
    def from_response(cls, response):
        """
        Factory to create BinaryFile-like object from requests.Response.
        """
        return cls(BinaryFile.from_response(response))

    # below should be synced with BinaryFile
    # NB: filename is actually used by ZipFile
    @property
    def suggested_filename(self):
        """
        Suggested filename.
        """
        return self._file.suggested_filename

    @property
    def extension(self):
        """
        Extension of file. See BinaryFile.extension.
        """
        return self._file.extension

    @property
    def size(self):
        """
        Size of file in bytes.
        """
        return self._file.size

    @property
    def size_fmt(self) -> str:
        """
        Human-readable size of file.
        """
        return self._file.size_fmt

    @property
    def mimetype(self) -> str:
        """
        Mimetype of the file.
        """
        return self._file.mimetype

    @property
    def content(self) -> bytes:
        """
        Raw bytes of the content.
        """
        return self._file.content

    @property
    def content_type(self) -> str:
        """
        Mimetype of the content.
        """
        return self._file.content_type

    def __repr__(self) -> str:
        cls = type(self)
        module = cls.__module__
        qualname = cls.__qualname__

        return f"<{module}.{qualname}(suggested_filename={self.suggested_filename}, size={self.size_fmt} [{self.size} bytes]) file-like object at {self.filename}>"

    def save(self, filename=None) -> int:
        """
        Save the file.
        """
        return self._file.save(filename=filename)

    def __enter__(self) -> BinaryFile:
        return self._file.__enter__()

    def __exit__(self, *args) -> None:
        return self._file.__exit__()
