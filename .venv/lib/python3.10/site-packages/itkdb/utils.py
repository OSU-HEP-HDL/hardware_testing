from __future__ import annotations

import logging
import os
from contextlib import suppress
from pathlib import Path
from typing import ClassVar
from urllib.parse import parse_qs, urlencode, urlparse

with suppress(ImportError):
    import pylibmagic  # noqa: F401  # pylint: disable=unused-import

import requests

import magic  # isort: skip


def _get_color_seq(i):
    """
    The background is set with 40 plus the number of the color, and the foreground with 30
    These are the sequences need to get colored output
    """
    return f"\033[1;{30+i:d}m"


class Colours:
    """
    See: https://stackoverflow.com/questions/287871/print-in-terminal-with-colours
    For additional colours, see: https://stackoverflow.com/questions/15580303/python-output-complex-line-with-floats-coloured-by-value
    """

    RESET_SEQ = "\033[0m"
    BOLD_SEQ = "\033[1m"
    UNDERLINE_SEQ = "\033[4m"
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = list(  # noqa: RUF012
        map(_get_color_seq, range(8))
    )


BASE_FORMAT_STRING = "[$BOLD%(asctime)s$RESET][%(levelname)-18s]  %(message)s ($BOLD%(filename)s$RESET:%(lineno)d)"
FORMAT_STRING = BASE_FORMAT_STRING.replace("$RESET", "").replace("$BOLD", "")
COLOUR_FORMAT_STRING = BASE_FORMAT_STRING.replace("$RESET", Colours.RESET_SEQ).replace(
    "$BOLD", Colours.BOLD_SEQ
)


class ColouredFormatter(logging.Formatter):
    """
    Color logger -- only used for top-level scripts...
    """

    LEVELS: ClassVar[dict[str, str]] = {
        "WARNING": Colours.YELLOW,
        "INFO": Colours.WHITE,
        "DEBUG": Colours.BLUE,
        "CRITICAL": Colours.YELLOW,
        "ERROR": Colours.RED,
    }

    def __init__(self, msg, use_colour=True):
        logging.Formatter.__init__(self, msg)
        self.use_colour = use_colour

    def format(self, record):
        levelname = record.levelname
        if self.use_colour and levelname in self.LEVELS:
            levelname_colour = self.LEVELS[levelname] + levelname + Colours.RESET_SEQ
            record.levelname = levelname_colour
        return logging.Formatter.format(self, record)


# Custom logger class with multiple destinations
class ColouredLogger(logging.Logger):
    """
    Custom logging class for coloured output. Only used for top-level scripts.
    """

    def __init__(self, name, use_colour=True):
        logging.Logger.__init__(self, name, logging.WARNING)
        colour_formatter = ColouredFormatter(
            COLOUR_FORMAT_STRING, use_colour=use_colour
        )
        console = logging.StreamHandler()
        console.setFormatter(colour_formatter)
        self.addHandler(console)


def pretty_print(req):
    """
    Pretty-print requests.Request object.
    """
    request = req.prepare() if isinstance(req, requests.Request) else req
    headers = "\r\n".join(
        f"{k}: {v if k != 'Authorization' else 'Bearer <TOKEN>'}"
        for k, v in request.headers.items()
    )
    try:
        body = (
            ""
            if request.body is None
            else (
                request.body.decode()
                if isinstance(request.body, bytes)
                else request.body
            )
        )
    except UnicodeDecodeError:
        body = "<Decoding error>"

    return f"Host: {urlparse(request.url).netloc}\r\n{request.method} {request.path_url} HTTP/1.1\r\n{headers}\r\n\r\n{body}"


def merge_url_query_params(url: str, additional_params: dict) -> str:
    """
    Merge a url with the specified query parameters.
    """
    url_components = urlparse(url)
    original_params = parse_qs(url_components.query)
    # Before Python 3.5 you could update original_params with
    # additional_params, but here all the variables are immutable.
    merged_params = {**original_params, **additional_params}
    updated_query = urlencode(merged_params, doseq=True)
    # _replace() is how you can create a new NamedTuple with a changed field
    return url_components._replace(query=updated_query).geturl()


def get_file_components(files):
    """
    Parse the files keyword argument from a requests object which can be one of the following:

        - {key: filepointer}
        - {key: (filename, filepointer)}
        - {key: (filename, filepointer, mimetype)}
        - {key: (filename, filepointer, mimetype, additional headers)}

    Only a single key is supported, so check if there's exactly one key or raise ValueError.
    """
    files_list = requests.utils.to_key_val_list(files)

    if len(files_list) != 1:
        msg = f"You're creating a single attachment but you specified {len(files_list)} files."
        raise ValueError(msg)
    # now need to handle the user scenarios
    key, value = files_list[0]

    # identify:
    #   filename, filepointer, mimetype, additional headers
    fname, fpointer, ftype, fheaders = (None,) * 4
    if isinstance(value, (tuple, list)):
        if len(value) == 2:
            fname, fpointer = value
        elif len(value) == 3:
            fname, fpointer, ftype = value
        else:
            fname, fpointer, ftype, fheaders = value
    else:
        fname = requests.utils.guess_filename(value) or key
        fpointer = value

    # handle cases where we didn't get ftype/fheaders specified by user
    ftype = ftype or get_mimetype(fname, fpointer)
    fheaders = fheaders or {}

    return fname, fpointer, ftype, fheaders


def is_image(fname, fpointer) -> bool:
    """
    Whether file is an image or not.

    Examples:

        >>> fname = itkdb.data / "1x1.sh"
        >>> with fname.open("rb") as fpointer:
        ...     is_image(fname, fpointer)
        ...
        False

        >>> fname = itkdb.data / "1x1.jpg"
        >>> with fname.open("rb") as fpointer:
        ...     is_image(fname, fpointer)
        ...
        True

    """
    return get_mimetype(fname, fpointer).startswith("image/")


def is_largefile(fname, fpointer, limit=64 * 1000) -> bool:
    """
    Whether file is a large file or not.

    Examples:

        >>> fname = itkdb.data / "1x1.jpg"
        >>> with fname.open("rb") as fpointer:
        ...     is_largefile(fname, fpointer)
        ...
        False

        >>> fname = itkdb.data / "1x1.jpg"
        >>> with fname.open("rb") as fpointer:
        ...     is_largefile(fname, fpointer, limit=100) # (1)!
        ...
        True

    1. :material-file: Set the lower `limit` for filesize to 100 bytes.

    """
    return get_filesize(fname, fpointer) > limit


def is_root(_, fpointer) -> bool:
    """
    Whether file is a ROOT file or not.

    Examples:

        >>> fname = itkdb.data / "1x1.jpg"
        >>> with fname.open("rb") as fpointer:
        ...     is_root(fname, fpointer)
        ...
        False

        >>> fname = itkdb.data / "tiny.root"
        >>> with fname.open("rb") as fpointer:
        ...     is_root(fname, fpointer)
        ...
        True

    !!! note "Added in version 0.4.0"

    """
    data = fpointer.read(4)
    fpointer.seek(0)
    return data == b"root"


def get_mimetype(fname, fpointer) -> str:
    """
    Mimetype of file.

    Examples:

        >>> fname = itkdb.data / "1x1.jpg"
        >>> with fname.open("rb") as fpointer:
        ...     get_mimetype(fname, fpointer)
        ...
        'image/jpeg'

    """
    try:
        ftype = magic.from_file(str(fname), mime=True)
    except FileNotFoundError:
        ftype = magic.from_buffer(fpointer.read(2048), mime=True)
        fpointer.seek(0)
    return ftype


def get_filesize(fname, fpointer) -> int:
    """
    Size of file in bytes.

    Examples:

        >>> fname = itkdb.data / "1x1.jpg"
        >>> with fname.open("rb") as fpointer:
        ...     get_filesize(fname, fpointer)
        ...
        125
    """
    try:
        size = Path(fname).stat().st_size
    except FileNotFoundError:
        fpointer.seek(0, os.SEEK_END)
        size = fpointer.tell()
        fpointer.seek(0)

    return size


def is_eos_uploadable(fname, fpointer) -> bool:
    """
    Decision on whether a file should be uploaded to EOS or not.

    Examples:

        >>> fname = itkdb.data / "1x1.sh"
        >>> with fname.open("rb") as fpointer:
        ...     is_eos_uploadable(fname, fpointer)
        ...
        False

        >>> fname = itkdb.data / "1x1.jpg"
        >>> with fname.open("rb") as fpointer:
        ...     is_eos_uploadable(fname, fpointer)
        ...
        True

    !!! note "Added in version 0.4.0"

    """
    return (
        is_image(fname, fpointer)
        or is_root(fname, fpointer)
        or is_largefile(fname, fpointer)
    )


def sizeof_fmt(num, suffix="B") -> str:
    """
    Return human-readable of bytes.

    Examples:

        >>> sizeof_fmt(2**8)
        '256.0B'
        >>> sizeof_fmt(2**16) # (1)!
        '64.0KiB'
        >>> sizeof_fmt(2**32)
        '4.0GiB'

    1. :material-alert: Don't forget that the `KiB` suffix indicates 1024 bytes, rather than the metric 1000 bytes.

    !!! note "Added in version 0.4.0"

    """
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"
