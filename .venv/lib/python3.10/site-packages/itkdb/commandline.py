from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from . import core, eos, settings, utils
from ._version import __version__

logging.basicConfig(format=utils.FORMAT_STRING, level=logging.INFO)
log = logging.getLogger(__name__)

_session = core.Session()


def opt_project(func):
    """
    Click option for project.
    """
    return click.option("--project", default="S", help="Project", show_default=True)(
        func
    )


def opt_component_type(func):
    """
    Click option for component type.
    """
    return click.option(
        "--component-type",
        help="Code for the type of component to query. Run list-component-types to find what types are available.",
        show_default=True,
    )(func)


def opt_component_code(func):
    """
    Click option for component code.
    """
    return click.option(
        "--component", help="Component code or component serial number", required=True
    )(func)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__)
@click.option(
    "--access-code1",
    prompt=not (bool(settings.ITKDB_ACCESS_CODE1)),
    default=settings.ITKDB_ACCESS_CODE1,
    show_default=True,
)
@click.option(
    "--access-code2",
    prompt=not (bool(settings.ITKDB_ACCESS_CODE2)),
    default=settings.ITKDB_ACCESS_CODE2,
    show_default=True,
)
@click.option("--auth-url", default=settings.ITKDB_AUTH_URL, show_default=True)
@click.option("--site-url", default=settings.ITKDB_API_URL, show_default=True)
@click.option(
    "--save-auth",
    help="Filename to save authenticated user to for persistence between requests",
    default=".auth",
    type=click.Path(path_type=Path, exists=False, writable=True, resolve_path=True),
)
def entrypoint(access_code1, access_code2, auth_url, site_url, save_auth):
    """
    Top-level pass-through.
    """
    _session.prefix_url = site_url
    _session.user._prefix_url = auth_url  # pylint: disable=protected-access
    _session.user._access_code1 = access_code1  # pylint: disable=protected-access
    _session.user._access_code2 = access_code2  # pylint: disable=protected-access
    _session.user._save_auth = save_auth  # pylint: disable=protected-access
    _session.user._load()  # pylint: disable=protected-access


@entrypoint.command()
def authenticate():
    """
    Authenticate using the provided access codes (environment variable or command line).
    """
    _session.user.authenticate()
    click.echo(
        f"You have signed in as {_session.user.name}. Your token expires in {_session.user.expires_in}s."
    )


@entrypoint.command()
def stats():
    """
    List overall statistics for ITk Production Database.
    """
    click.echo(
        json.dumps(
            _session.get("getItkpdOverallStatistics").json()["statistics"], indent=2
        )
    )
    sys.exit(0)


@entrypoint.command()
def list_institutes():
    """
    List all institutions.
    """
    click.echo(
        json.dumps(_session.get("listInstitutions").json()["pageItemList"], indent=2)
    )
    sys.exit(0)


# NB: list_component_type_codes is the same as this, but use jq
#  $ itkdb list-component-types --project P | jq '[.[] | {code: .code, name: .name}]'
@entrypoint.command()
@opt_project
def list_component_types(project):
    """
    List component types for a project.
    """
    data = {"project": project}
    click.echo(
        json.dumps(
            _session.get("listComponentTypes", json=data).json()["pageItemList"],
            indent=2,
        )
    )
    sys.exit(0)


@entrypoint.command()
@opt_project
@opt_component_type
def list_components(project, component_type):
    """
    List components registered for a given component type.
    """
    data = {"project": project}
    if component_type:
        data.update({"componentType": component_type})
    click.echo(
        json.dumps(
            _session.get("listComponents", json=data).json()["itemList"], indent=2
        )
    )
    sys.exit(0)


# currently broken FYI
@entrypoint.command()
def list_all_attachments():
    """
    List all attachments physically stored in the ITk Production Database.
    """
    click.echo(
        json.dumps(
            _session.get("uu-app-binarystore/listBinaries").json()["itemList"], indent=2
        )
    )
    sys.exit(0)


@entrypoint.command()
def list_projects():
    """
    List the projects.
    """
    click.echo(json.dumps(_session.get("listProjects").json()["itemList"], indent=2))
    sys.exit(0)


@entrypoint.command()
@opt_project
@opt_component_type
def list_test_types(project, component_type):
    """
    List the test types for a component type.
    """
    data = {"project": project, "componentType": component_type}
    click.echo(
        json.dumps(
            _session.get("listTestTypes", json=data).json()["pageItemList"], indent=2
        )
    )
    sys.exit(0)


@entrypoint.command()
@opt_component_code
def get_component_info(component):
    """
    Get information about a component.
    """
    data = {"component": component}
    click.echo(json.dumps(_session.get("getComponent", json=data).json(), indent=2))
    sys.exit(0)


@entrypoint.command()
@opt_project
def summary(project):
    """
    Summarize some information about institutions, component types, and test types per component.
    """
    header_str = "====={0:^100s}====="
    click.echo(header_str.format("Institutes"))
    institutes = _session.get("listInstitutions").json()["pageItemList"]
    for institute in institutes:
        click.echo(f"{institute['name']} ({institute['code']})")

    click.echo(header_str.format("Strip component types"))
    component_types = _session.get(
        "listComponentTypes", json={"project": project}
    ).json()["pageItemList"]

    for component_type in component_types:
        click.echo(
            f"{component_type['name']} ({component_type['code']}) {component_type['state']}"
        )

    click.echo(header_str.format("Test types by component"))
    for component_type in component_types:
        click.echo(f"Test types for {component_type['code']}")
        test_types = _session.get(
            "listTestTypes",
            json={"project": project, "componentType": component_type["code"]},
        ).json()["pageItemList"]
        for test_type in test_types:
            click.echo(
                f"  {test_type['name']} ({test_type['code']}) {test_type['state']}"
            )


@entrypoint.command()
@opt_component_code
@click.option("--title", help="Short description", required=True)
@click.option("-d", "--description", help="Description of attachment", required=True)
@click.option(
    "-f",
    "--file",
    help="File to attach",
    required=True,
    type=click.Path(path_type=Path, exists=True),
)
@click.option("--filename", help="If specified, override filename of attachment")
@click.option(
    "--file-type", help="The type of the file being uploaded", default="text/plain"
)
def add_attachment(component, title, description, file, filename, file_type):
    """
    Add an attachment to a component.
    """
    filename = filename if filename else file.name

    data = {
        "component": component,
        "title": title,
        "description": description,
        "type": "file",
        "url": filename,
    }
    with file.open("rb") as fpointer:
        attachment = {"data": (filename, fpointer, file_type)}
        click.echo(
            json.dumps(
                _session.post(
                    "createComponentAttachment", data=data, files=attachment
                ).json(),
                indent=2,
            )
        )
    sys.exit(0)


@entrypoint.command()
@opt_component_code
@click.option("-m", "--message", help="Comment to add to component", required=True)
def add_comment(component, message):
    """
    Add a comment to a component.
    """
    data = {"component": component, "comments": [message]}
    click.echo(
        json.dumps(_session.post("createComponentComment", json=data).json(), indent=2)
    )
    sys.exit(0)


@entrypoint.group(name="eos", context_settings={"help_option_names": ["-h", "--help"]})
def entrypoint_eos():
    """
    Actions for interacting with EOS.

    \f
    !!! note "Added in version 0.5.0"
    """


@entrypoint_eos.command(name="upload")
@click.option("-t", "--token", help="Token for interacting with EOS", required=True)
@click.option("-p", "--path", help="Path on EOS to upload to", required=True)
@click.option(
    "-f",
    "--file",
    help="File to attach",
    required=True,
    type=click.Path(path_type=Path, exists=True),
)
def eos_upload(token, path, file):
    """
    Upload to a path on EOS.

    \f
    !!! note "Added in version 0.5.0"
    """

    eos_url = f"https://eosatlas.cern.ch{path}"

    with file.open("rb") as fpointer:
        eos_file_details = utils.get_file_components({"data": fpointer})
        response = eos.put(token, eos_url, eos_file_details)
    response.raise_for_status()
    sys.exit(0)


@entrypoint_eos.command(name="delete")
@click.option("-t", "--token", help="Token for interacting with EOS", required=True)
@click.option("-p", "--path", help="Path on EOS to delete", required=True)
def eos_delete(token, path):
    """
    Delete a path from EOS.

    \f
    !!! note "Added in version 0.5.0"
    """

    eos_url = f"https://eosatlas.cern.ch{path}"
    response = eos.delete(token, eos_url)
    response.raise_for_status()
    sys.exit(0)
