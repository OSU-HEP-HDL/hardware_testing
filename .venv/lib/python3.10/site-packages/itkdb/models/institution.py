from __future__ import annotations

import attr


def make_item(data):
    """
    make Item.
    """
    return Item(code=data["code"], id=data["id"], name=data["name"])


def make_component_type(data):
    """
    make ComponentType.
    """
    return ComponentType(
        name=data["name"],
        code=data["code"],
        item_list=list(map(make_item, data["itemList"])),
    )


def make_contacts(data):
    """
    make Contact.
    """
    return Contact(
        email=data.get("email"), phone=data.get("phone"), web=data.get("web")
    )


def make_address(data):
    """
    make Address.
    """
    return Address(
        building=data.get("building"),
        city=data.get("city"),
        state=data.get("state"),
        street=data.get("street"),
        zip_code=data.get("zipCode"),
    )


def make_institution(data):
    """
    make Institution.
    """
    return Institution(
        address=make_address(data["address"]),
        code=data["code"],
        component_type=list(map(make_component_type, data["componentType"])),
        contacts=make_contacts(data["contacts"]),
        id=data["id"],
        latitude=data["latitude"],
        longitude=data["longitude"],
        name=data["name"],
        supervisor=data["supervisor"],
    )


def make_institution_list(data):
    """
    make InstitutionList.
    """
    return InstitutionList(institutions=list(map(make_institution, data)))


@attr.s
class Item:
    """
    institution item.
    """

    code = attr.ib()
    id = attr.ib()  # pylint: disable=invalid-name
    name = attr.ib()


@attr.s
class ComponentType:
    """
    component type.
    """

    code = attr.ib()
    item_list = attr.ib()
    name = attr.ib()


@attr.s
class Contact:
    """
    institution contact.
    """

    email = attr.ib()
    phone = attr.ib()
    web = attr.ib()


@attr.s
class Address:
    """
    institution address.
    """

    building = attr.ib()
    city = attr.ib()
    state = attr.ib()
    street = attr.ib()
    zip_code = attr.ib()


@attr.s
class Institution:
    """
    institution.
    """

    address = attr.ib()
    code = attr.ib()
    component_type = attr.ib()
    contacts = attr.ib()
    id = attr.ib()  # pylint: disable=invalid-name
    latitude = attr.ib()
    longitude = attr.ib()
    name = attr.ib()
    supervisor = attr.ib()


@attr.s
class InstitutionList:
    """
    list of institutions.
    """

    institutions = attr.ib(type=list)
