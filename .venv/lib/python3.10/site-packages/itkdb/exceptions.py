"""Provide exception classes for the itkdb package."""

from __future__ import annotations

import json
from contextlib import suppress
from urllib.parse import urlparse

import requests

from .utils import pretty_print

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

try:
    from html2text import html2text
except ImportError:

    def html2text(string):
        """
        Pass-through function.
        """
        return string


class ITkDBException(Exception):
    """Base exception class for exceptions that occur within this package."""


class InvalidInvocation(ITkDBException):
    """Indicate that the code to execute cannot be completed."""


class ResponseException(ITkDBException):
    """Indicate that there was an error with the completed HTTP request."""

    def __init__(
        self, response: requests.Response, additional_message: str | None = None
    ):
        """Initialize a ResponseException instance.
        :param response: A requests.response instance.
        """
        self.response: requests.Response = response
        message = f"received {response.status_code} HTTP response for following request\n{pretty_print(response.request)}"

        try:
            if additional_message is None:
                additional_message = json.dumps(response.json(), indent=2)

        except JSONDecodeError:
            additional_message = response.text.strip()

        if additional_message:
            if "text/html" in response.headers.get("content-type", ""):
                additional_message = html2text(additional_message)

            message = (
                f"{message}\n\nThe following details may help:\n{additional_message}"
            )
        super().__init__(message)


class BadJSON(ResponseException):
    """Indicate the response did not contain valid JSON."""


class BadRequest(ResponseException):
    """Indicate invalid parameters for the request."""


class Conflict(ResponseException):
    """Indicate a conflicting change in the target resource."""


class Forbidden(ResponseException):
    """Indicate the authentication is not permitted for the request."""

    def __init__(self, response):
        additional_message = None

        with suppress(JSONDecodeError):
            additional_message = (
                response.json()
                .get("uuAppErrorMap", {})
                .get("uu-app-workspace/authorization/userIsNotAuthorized", {})
                .get("message", None)
            )
        super().__init__(response, additional_message)


class NotFound(ResponseException):
    """Indicate that the requested URL was not found."""


class Redirect(ResponseException):
    """Indicate the request resulted in a redirect.

    This class adds the attribute ``path``, which is the path to which the
    response redirects.

    """

    def __init__(self, response):
        """Initialize a Redirect exception instance.

        :param response: A requests.response instance containing a location
        header.

        """
        path = urlparse(response.headers["location"]).path
        self.path = path[:-5] if path.endswith(".json") else path
        self.response = response
        super().__init__(f"Redirect to {self.path}")


class ServerError(ResponseException):
    """Indicate issues on the server end preventing request fulfillment."""


class SpecialError(ResponseException):
    """Indicate syntax or spam-prevention issues."""

    def __init__(self, response):
        """Initialize a SpecialError exception instance.

        :param response: A requests.response instance containing a message
        and a list of special errors.

        """
        self.response = response

        resp_dict = self.response.json()  # assumes valid JSON
        self.message = resp_dict.get("message", "")
        self.reason = resp_dict.get("reason", "")
        self.special_errors = resp_dict.get("special_errors", [])
        super().__init__(f"Special error {self.message!r}")


class TooLarge(ResponseException):
    """Indicate that the request data exceeds the allowed limit."""


class UnavailableForLegalReasons(ResponseException):
    """Indicate that the requested URL is unavailable due to legal reasons."""


class UnhandledResponse(ResponseException):
    """Indicate a response status code we have not dealt with yet."""


class DuplicateObjectsInDB(ITkDBException):
    """Indicate duplicate checker found a duplicate item when not allowing for duplicates."""


class DuplicateTestRuns(DuplicateObjectsInDB):
    """Indicate that duplicate test runs were found."""
