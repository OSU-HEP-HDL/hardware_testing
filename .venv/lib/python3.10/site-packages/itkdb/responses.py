from __future__ import annotations

import json
import logging

log = logging.getLogger(__name__)


class PagedResponse:
    """
    A generator that handles paginated responses by requesting the next page as you need it.

    !!! note "Changed in version 0.4.6"
        - added `history` argument
    """

    def __init__(self, session, response, history=False, limit=-1, key="pageItemList"):
        # self._load() relies on self.history
        self.history = history
        self._pages = []
        self._session = session
        self._load(response)
        self.yielded = 0
        self.limit = limit if limit and limit > 0 else self.total
        self.key = key

    @property
    def pages(self) -> list:
        """
        A list of pages fetched.
        """
        return self._pages

    @property
    def last_page(self) -> dict:
        """
        The most recent page retrieved.
        """
        return self.pages[-1]

    @property
    def data(self) -> dict | list[dict]:
        """
        The data contained on the most recent page retrieved.
        """
        return self.last_page.get(self.key)

    @property
    def error(self) -> dict:
        """
        The uuAppErrorMap for the current page.
        """
        return self.last_page.get("uuAppErrorMap", {})

    @property
    def page_info(self) -> dict:
        """
        The pageInfo for the current page.
        """
        return self.last_page.get("pageInfo", {})

    @property
    def page_index(self) -> int:
        """
        The pageIndex for the current page.

        If there is no pageIndex, returns -1.
        """
        return self.page_info.get("pageIndex", -1)

    @property
    def page_size(self) -> int:
        """
        The pageSize for the current page.

        If there is no pageSize, returns -1.
        """
        return self.page_info.get("pageSize", -1)

    @property
    def total(self) -> int:
        """
        The total number of items (reported from the current page).

        If there is no total, returns -1.
        """
        return self.page_info.get("total", -1)

    def _load(self, response):
        self._response = response
        if self.history:
            self._pages.append(response.json())
        else:
            self._pages = [response.json()]

        # nb: list_index is only for the last page
        self._list_index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.limit is not None:
            if self.yielded >= self.limit:
                raise StopIteration()
            if self._list_index >= len(self.data):
                self._next_page()

        self._list_index += 1
        self.yielded += 1
        return self.data[self._list_index - 1]

    def __bool__(self):
        return bool(self.total)

    def _next_page(self):
        body = json.loads(self._response.request.body or "{}")
        body.update(
            {"pageInfo": {"pageIndex": self.page_index + 1, "pageSize": self.page_size}}
        )
        self._response.request.prepare_auth(
            self._session.authorize, self._response.request.url
        )
        self._response.request.prepare_body(data=None, files=None, json=body)
        response = self._session.send(self._response.request)
        self._load(response)
