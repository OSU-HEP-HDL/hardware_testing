from __future__ import annotations

from contextlib import suppress
from typing import Any

from itkdb import Client
from itkdb.exceptions import BadRequest


class Component:
    """Component model"""

    def __init__(self, client: Client, data: dict[str, Any]):
        self._client = client
        self._data = data
        self._children: list[Any] = []

    @property
    def serial_number(self) -> str:
        """serial number of component"""
        return self._data.get("serialNumber", "") or ""

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        """unique identifier of component"""
        return str(self._data["id"])

    @property
    def children(self) -> list[Any]:
        """children of component"""
        return self._children or self._data.get("children", []) or []

    @children.setter
    def children(self, children: list[Any]) -> None:
        self._data["children"] = children

    def walk(self, recurse: bool = True) -> None:
        """recursively walk through children and load information from database"""
        for child in self.children:
            # BadRequest: component doesn't exist
            # KeyError: no component in slot
            data = child
            with suppress(BadRequest, KeyError):
                data = self._client.get(  # type: ignore[no-untyped-call]
                    "getComponent", json={"component": child["component"]["id"]}
                )

            child_component = Component(self._client, data)
            if recurse:
                child_component.walk(recurse)
            self._children.append(child_component)

    def __repr__(self) -> str:
        module = type(self).__module__
        qualname = type(self).__qualname__
        return f"<{module}.{qualname} object '{self.serial_number}' at {hex(id(self))}>"
