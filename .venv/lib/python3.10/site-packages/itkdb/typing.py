"""
Typing helpers.
"""

from __future__ import annotations

import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from typing import Protocol


class UserLike(Protocol):
    """
    Protocol for expectation of the user used by [itkdb.Client][]

    !!! note "Added in version 0.6.0"
    """

    def authenticate(self) -> bool:
        """
        Authenticate the user if needed.
        """

    @property
    def bearer(self) -> str:
        """
        The bearer token used for requests made by a client.
        """


__all__ = (
    "Self",
    "UserLike",
)
