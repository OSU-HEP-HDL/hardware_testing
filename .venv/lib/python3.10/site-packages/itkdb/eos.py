from __future__ import annotations

import logging
from io import BytesIO
from string import capwords

from requests import Request, Response

from itkdb import exceptions, utils
from itkdb._version import __version__
from itkdb.data import path as itkdb_data

try:
    import pycurl
except ModuleNotFoundError:
    HAS_PYCURL = False
except ImportError as imp_err:
    imp_err_msg = "There is an error importing pycurl. Please see the documentation for some hints.\n\n  https://itkdb.docs.cern.ch/0.6/meta/faq/"  # pylint: disable=invalid-name
    raise ImportError(imp_err_msg) from imp_err
else:
    HAS_PYCURL = True

log = logging.getLogger(__name__)


def put(eos_token, eos_url, eos_file_details=None) -> Response:
    """
    Function for uploading to EOS, by wrapping pyCURL appropriately.

    Args:
        eos_token (str): EOS token
        eos_url (str): Path on EOS to upload file to
        eos_file_details (tuple or None): Details on the file being uploaded: (fname, fpointer, ftype, fheaders)

    !!! note "Added in version 0.5.0"
    """

    # see _request_handler for this information
    fname, fpointer, ftype, fheaders = eos_file_details

    headers = {
        "Authorization": f"Bearer {eos_token}",
        "User-Agent": f"itkdb/{__version__}",
        "Content-Type": ftype,
        **fheaders,
    }

    buffer_header = BytesIO()
    buffer_body = BytesIO()

    curl = pycurl.Curl()
    curl.setopt(curl.URL, eos_url)
    curl.setopt(curl.FOLLOWLOCATION, True)
    curl.setopt(curl.UPLOAD, True)
    curl.setopt(
        curl.HTTPHEADER, [f'{capwords(k, "-")}: {v}' for k, v in headers.items()]
    )
    curl.setopt(curl.CAINFO, str((itkdb_data / "CERN_chain.pem").resolve()))
    curl.setopt(curl.READDATA, fpointer)
    curl.setopt(curl.INFILESIZE_LARGE, utils.get_filesize(fname, fpointer))
    curl.setopt(curl.HEADERFUNCTION, buffer_header.write)
    curl.setopt(curl.WRITEFUNCTION, buffer_body.write)
    curl.setopt(curl.SEEKFUNCTION, fpointer.seek)
    curl.perform()
    curl.close()

    resp_header = buffer_header.getvalue().decode()
    resp_body = buffer_body.getvalue().decode()

    header_blocks = []
    for item in resp_header.strip().split("\r\n"):
        if item.startswith("HTTP"):
            header_blocks.append([item])
        elif item:
            header_blocks[-1].append(item)

    eos_response = Response()
    eos_response.status_code = int(header_blocks[-1][0].split()[1])
    eos_response.request = Request(
        method="PUT",
        url=eos_url,
        headers=headers,
        files={"file": (fname, fpointer, ftype)},
    )

    additional_message = f"  - I was not able to upload file to EOS. Please report the above information to developers.\r\n\r\n{resp_body}\r\n\r\n"
    if eos_response.status_code != 201:
        for header_block in header_blocks:
            additional_message += "\r\n".join(header_block)
            additional_message += "\r\n" + "-" * 10 + "\r\n"
        raise exceptions.ResponseException(
            eos_response, additional_message=additional_message
        )

    return eos_response


def delete(eos_token, eos_url) -> Response:
    """
    Function for deleting from EOS, by wrapping pyCURL appropriately.

    Args:
        eos_token (str): EOS token
        eos_url (str): Path on EOS to upload file to

    !!! note "Added in version 0.5.0"
    """

    headers = {
        "Authorization": f"Bearer {eos_token}",
        "User-Agent": f"itkdb/{__version__}",
    }

    buffer_header = BytesIO()
    buffer_body = BytesIO()

    curl = pycurl.Curl()
    curl.setopt(curl.URL, eos_url)
    curl.setopt(curl.FOLLOWLOCATION, True)
    curl.setopt(curl.CUSTOMREQUEST, "DELETE")
    curl.setopt(
        curl.HTTPHEADER, [f'{capwords(k, "-")}: {v}' for k, v in headers.items()]
    )
    curl.setopt(curl.CAINFO, str((itkdb_data / "CERN_chain.pem").resolve()))
    curl.setopt(curl.HEADERFUNCTION, buffer_header.write)
    curl.setopt(curl.WRITEFUNCTION, buffer_body.write)
    curl.perform()
    curl.close()

    resp_header = buffer_header.getvalue().decode()
    resp_body = buffer_body.getvalue().decode()

    header_blocks = []
    for item in resp_header.strip().split("\r\n"):
        if item.startswith("HTTP"):
            header_blocks.append([item])
        elif item:
            header_blocks[-1].append(item)

    eos_response = Response()
    eos_response.status_code = int(header_blocks[-1][0].split()[1])
    eos_response.request = Request(
        method="DELETE",
        url=eos_url,
        headers=headers,
    )

    additional_message = f"  - I was not able to delete the file from EOS. Please report the above information to developers.\r\n\r\n{resp_body}\r\n\r\n"
    if eos_response.status_code != 204:
        for header_block in header_blocks:
            additional_message += "\r\n".join(header_block)
            additional_message += "\r\n" + "-" * 10 + "\r\n"
        raise exceptions.ResponseException(
            eos_response, additional_message=additional_message
        )

    return eos_response
