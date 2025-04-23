from __future__ import annotations

import contextlib
import logging
from functools import partial
from typing import Any
from urllib.parse import urlparse

from requests.exceptions import HTTPError

from itkdb import eos, exceptions, models, utils
from itkdb.core import Session
from itkdb.data import path as itkdb_data
from itkdb.responses import PagedResponse

log = logging.getLogger(__name__)


class Client(Session):
    """
    The top-level user-facing client for interacting with the ITk Production Database API.

    !!! note "Changed in version 0.4.0"
        - added `use_eos` argument

    !!! note "Changed in version 0.4.6"
        - added `pagination_history` argument
    """

    limit = -1

    def __init__(self, use_eos=False, pagination_history=False, **session_kwargs):
        self._use_eos = use_eos
        self._pagination_history = pagination_history
        super().__init__(**session_kwargs)

    def request(self, method, url, *args, **kwargs):
        self.limit = kwargs.pop("limit", -1)

        response = super(Session, self).request(method, url, *args, **kwargs)
        return self._response_handler(response)

    def get(self, url, **kwargs):
        is_cern_url = ".cern.ch" in urlparse(url).netloc
        # is_binary_data = "uu-app-binarystore/getBinaryData" in url
        if is_cern_url and "verify" not in kwargs:
            log.info(
                "Identified a cern.ch request, will attach CERN SSL chain to request by overriding `verify`."
            )
            kwargs["verify"] = itkdb_data / "CERN_chain.pem"

        # getBinaryData does not handle chunked requests
        # if is_cern_url or is_binary_data:
        if is_cern_url:
            log.info(
                "Identified a request that potentially downloads larger amounts of data, will execute chunked requests (stream=True)."
            )
            kwargs["stream"] = True
            headers = kwargs.get("headers", {})
            headers["transfer-encoding"] = "chunked"
            kwargs["headers"] = headers
        return super().get(url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        """
        Make a POST request.

        Args:
            url (str): URI to POST to
            allow_duplicate (bool): Indicate if this request should allow creation of duplicate item (see below)
            kwargs: (any): All other keyword arguments supposed by [itkdb.core.Session.post][]

        !!! note "Changed in version 0.6.1"
            `allow_duplicate` keyword argument supported

        The following routes have duplicate check support:
            - `uploadTestRunResults` (added in `v0.6.1`)

        """
        allow_duplicate = kwargs.pop("allow_duplicate", True)
        if not allow_duplicate:
            duplicates = []
            if not json:
                msg = "You asked for me to check for duplicates, but you didn't provide any data? If this message was in error, please get in touch with the itkdb developers: https://itkdb.docs.cern.ch/ ."
                raise ValueError(msg)

            if url.endswith("uploadTestRunResults"):
                duplicates = self._get_duplicate_test_runs(json)
                if duplicates:
                    msg = f"Duplicate test runs: {duplicates}"
                    raise exceptions.DuplicateTestRuns(msg)
            else:
                msg = f"No logic exists to check for duplicates for url: {url}. Either submit an MR or remove 'allow_duplicate=False'."
                raise ValueError(msg)
        return super().post(url, data=data, json=json, **kwargs)

    def _handle_warnings(self, data):
        warnings = data.pop("uuAppErrorMap", {})
        try:
            for key, message in warnings.items():
                log.warning("%s: %s", key, message)
        except AttributeError:
            # it's a string like:
            #   'uuAppErrorMap': '#<UuApp::Oidc::Session:0x00561d53890118>'
            log.warning(warnings)

    def upload_to_eos(self, response, eos_file_details=None, **_) -> None:
        """
        requests response hook function to upload a file to eos.
        """
        log.info("I was able to get a token to upload to EOS. Let me upload.")
        try:
            response.raise_for_status()
        except HTTPError:
            log.warning("Something went wrong with uploading to EOS.")
            return response

        # do nothing if betamax is being used (no need to run the cURL for EOS)
        if response.connection.__class__.__name__ == "BetamaxAdapter":
            return None

        token_request = response.json()

        log.info(token_request)

        response.eos_response = eos.put(
            token_request["token"], token_request["url"], eos_file_details
        )
        return None

    def delete_from_eos(self, response, **_) -> None:
        """
        requests response hook function to delete a file from eos.
        """
        try:
            response.raise_for_status()
        except HTTPError:
            log.warning("Something went wrong with deleting the attachment.")
            return response

        data = response.json()

        # do nothing if it's not an EOS-type attachment
        # or if betamax is being used (no need to run the cURL for EOS)
        if (
            data["attachment"]["type"] != "eos"
            or response.connection.__class__.__name__ == "BetamaxAdapter"
        ):
            return None

        if "token" not in data:
            log.warning(
                "It seems there is no token, so we are not deleting this from EOS."
            )
            return None

        log.info(
            "It looks like you're deleting an attachment from ITk PD that is stored on EOS, I will try to delete it from EOS for you."
        )

        response.eos_response = eos.delete(data["token"], data["attachment"]["url"])
        return None

    def retry_with_old_binary(
        self, response, request_url, request_params, **kwargs
    ) -> None:
        """
        requests response hook function to retry with old binary API.
        """
        try:
            self._check_response(response)
            return response
        except exceptions.BadRequest as he:
            redirect_error = he

        redirected_url = "uu-app-binarystore/getBinaryData"
        log.warning("Error from '%s' retrying as '%s'", request_url, redirected_url)

        bin_code = request_params["code"]
        json = {"code": bin_code}

        try:
            retry_response = self.get(redirected_url, json=json, **kwargs)
            retry_response.raise_for_status()
            return retry_response
        except exceptions.BadRequest as re_error:
            # Raise original error
            raise redirect_error from re_error

    def _request_handler(self, request):
        if request.url == self._normalize_url("/itkdbPoisonPillTest"):
            request.url = self._normalize_url("/poison")
        elif request.url == self._normalize_url("/createComponentAttachment"):
            if not self.use_eos:
                return

            if not eos.HAS_PYCURL:
                msg = "You are trying to upload to EOS, but you did not install itkdb[eos] or pycurl is not installed correctly."
                raise RuntimeError(msg)

            fname, fpointer, ftype, fheaders = utils.get_file_components(request.files)

            if not utils.is_eos_uploadable(fname, fpointer):
                return

            log.info(
                "It looks like you're attaching an image, root, or large file, I will try to put it on EOS for you."
            )

            # update headers
            fheaders = fheaders or {}
            request.headers.update(fheaders)

            ftype = ftype or utils.get_mimetype(fname, fpointer)

            details = {
                "type": "component",
                "id": request.data["component"],
                "title": request.data["title"],
                "description": request.data["description"],
                "filesize": utils.get_filesize(fname, fpointer),
            }

            leftover = {
                k: v
                for k, v in request.data.items()
                if k not in ["component", "title", "description"]
            }

            if leftover:
                log.warning("Ignoring user-specified data=%s", leftover)

            request.json = details
            request.data = None
            request.files = None
            request.hooks["response"] = [
                partial(
                    self.upload_to_eos,
                    eos_file_details=(fname, fpointer, ftype, fheaders),
                )
            ]
            request.url = self._normalize_url("requestUploadEosFile")
        elif request.url == self._normalize_url("/createTestRunAttachment"):
            if not self.use_eos:
                return

            if not eos.HAS_PYCURL:
                msg = "You are trying to upload to EOS, but you did not install itkdb[eos] or pycurl is not installed correctly."
                raise RuntimeError(msg)

            fname, fpointer, ftype, fheaders = utils.get_file_components(request.files)

            if not utils.is_eos_uploadable(fname, fpointer):
                return

            log.info(
                "It looks like you're attaching an image, root, or large file, I will try to put it on EOS for you."
            )

            # update headers
            fheaders = fheaders or {}
            request.headers.update(fheaders)

            ftype = ftype or utils.get_mimetype(fname, fpointer)

            details = {
                "type": "testRun",
                "id": request.data["testRun"],
                "title": request.data["title"],
                "description": request.data["description"],
                "filesize": utils.get_filesize(fname, fpointer),
            }

            leftover = {
                k: v
                for k, v in request.data.items()
                if k not in ["component", "title", "description"]
            }

            if leftover:
                log.warning("Ignoring user-specified data=%s", leftover)

            request.json = details
            request.data = None
            request.files = None
            request.hooks["response"] = [
                partial(
                    self.upload_to_eos,
                    eos_file_details=(fname, fpointer, ftype, fheaders),
                )
            ]
            request.url = self._normalize_url("requestUploadEosFile")
        elif request.url == self._normalize_url("/createShipmentAttachment"):
            if not self.use_eos:
                return

            if not eos.HAS_PYCURL:
                msg = "You are trying to upload to EOS, but you did not install itkdb[eos] or pycurl is not installed correctly."
                raise RuntimeError(msg)

            fname, fpointer, ftype, fheaders = utils.get_file_components(request.files)

            if not utils.is_eos_uploadable(fname, fpointer):
                return

            log.info(
                "It looks like you're attaching an image, root, or large file, I will try to put it on EOS for you."
            )

            # update headers
            request.headers.update(fheaders)

            details = {
                "type": "shipment",
                "id": request.data["shipment"],
                "title": request.data["title"],
                "description": request.data["description"],
                "filesize": utils.get_filesize(fname, fpointer),
            }

            leftover = {
                k: v
                for k, v in request.data.items()
                if k not in ["component", "title", "description"]
            }

            if leftover:
                log.warning("Ignoring user-specified data=%s", leftover)

            request.json = details
            request.data = None
            request.files = None
            request.hooks["response"] = [
                partial(
                    self.upload_to_eos,
                    eos_file_details=(fname, fpointer, ftype, fheaders),
                )
            ]
            request.url = self._normalize_url("requestUploadEosFile")
        elif request.url in [
            self._normalize_url("/getBatchAttachment"),
            self._normalize_url("/getComponentAttachment"),
            self._normalize_url("/getShipmentAttachment"),
            self._normalize_url("/getTestRunAttachment"),
        ]:
            request.hooks["response"] = [
                partial(
                    self.retry_with_old_binary,
                    request_url=request.url,
                    request_params=request.json,
                )
            ]
        elif request.url in [
            self._normalize_url("/deleteComponentAttachment"),
            self._normalize_url("/deleteTestRunAttachment"),
            self._normalize_url("/deleteShipmentAttachment"),
        ]:
            if not self.use_eos or not eos.HAS_PYCURL:
                msg = "You are trying to delete an attachment that might be on EOS, but you did not install itkdb[eos] or pycurl is not installed correctly."
                raise RuntimeError(msg)

            request.hooks["response"] = [self.delete_from_eos]

    def _response_handler(self, response):
        # sometimes we don't get content-type, so make sure it's a string at least
        content_type = response.headers.get("content-type", "")
        if content_type is None and not response.url.startswith(
            "https://eosatlas.cern.ch"
        ):
            return response

        if (
            content_type.startswith("application/json")
            and not response.url.endswith("uu-app-binarystore/getBinaryData")
            and not response.url.startswith("https://eosatlas.cern.ch")
            and not response.url.endswith("/getBatchAttachment")
            and not response.url.endswith("/getComponentAttachment")
            and not response.url.endswith("/getShipmentAttachment")
            and not response.url.endswith("/getTestRunAttachment")
        ):
            if response.headers.get("content-length") == "0":
                return {}

            try:
                data = response.json()
                self._handle_warnings(data)
            except ValueError as err:
                raise exceptions.BadJSON(response) from err

            limit = self.limit
            self.limit = -1  # reset the limit again
            if "pageItemList" in data:
                return PagedResponse(
                    super(),
                    response,
                    history=self._pagination_history,
                    limit=limit,
                    key="pageItemList",
                )

            if "itemList" in data:
                page_info = data.get("pageInfo", None)
                if page_info and (
                    page_info["pageIndex"] * page_info["pageSize"] < page_info["total"]
                ):
                    return PagedResponse(
                        super(),
                        response,
                        history=self._pagination_history,
                        limit=limit,
                        key="itemList",
                    )
                return data["itemList"]

            if "testRunList" in data:
                return data["testRunList"]

            if "dtoSample" in data:
                return data["dtoSample"]

            return data

        # we've got a file or attachment we're downloading of some kind, so
        # dump to tempfile and seek from there to determine behavior
        binary_file = models.BinaryFile.from_response(response)
        is_cern_url = ".cern.ch" in urlparse(response.url).netloc

        if (
            is_cern_url
            and binary_file.mimetype == "application/octet-stream"
            and binary_file.content_type != "application/octet-stream"
        ):
            log.warning(
                "Changing the mimetype for the response from EOS from 'application/octet-stream' to '%s'.",
                binary_file.content_type,
            )
            binary_file._mimetype = (  # pylint: disable=protected-access
                binary_file.content_type
            )
            response.headers["content-type"] = binary_file.mimetype

        mimetype = binary_file.mimetype or ""
        if mimetype.startswith("image/"):
            binary_file.__class__ = models.ImageFile
        elif mimetype.startswith(("text/", "text")) or mimetype == "application/json":
            binary_file.__class__ = models.TextFile
        elif mimetype == "application/zip":
            binary_file = models.ZipFile(binary_file)
        elif binary_file.mimetype is None:
            log.warning(
                "No mimetype available. This is likely an empty file. Defaulting to BinaryFile."
            )
        else:
            log.warning(
                "No model available for Content-Type: '%s'. Defaulting to BinaryFile.",
                mimetype,
            )

        return binary_file

    def prepare_request(self, request):
        request.url = self._normalize_url(request.url)
        self._request_handler(request)
        return super().prepare_request(request)

    @property
    def use_eos(self):
        """
        Flag indicating whether to use eos for uploading attachments.
        """
        return self._use_eos

    def _get_duplicate_test_runs(self, new_test_run: dict[str, Any]) -> list[str]:
        """
        Returns a list of test run ids for test runs that were identified as duplicates
        """
        log.info("You asked for me to check for duplicates, I will do my best.")
        component_identifier = new_test_run["component"]
        filter_map = {}
        if len(component_identifier) == 32:
            filter_map["code"] = component_identifier
        else:
            filter_map["serialNumber"] = component_identifier

        if "stage" in new_test_run:
            filter_map["stage"] = [new_test_run["stage"]]

        filter_map["testType"] = [new_test_run["testType"]]
        filter_map["state"] = ["ready"]
        test_runs = self.get("listTestRunsByComponent", json={"filterMap": filter_map})

        test_run_ids = [test_run["id"] for test_run in test_runs]

        # have no duplicates
        if len(test_run_ids) == 0:
            return test_run_ids

        log.info(
            "Found %d that may be duplicates, checking below...", len(test_run_ids)
        )

        # have at least one potential duplicate, need to check properties / parameters
        test_runs_info = self.get("getTestRunBulk", json={"testRun": test_run_ids})
        # here, we have multiple duplicates, so need to filter
        # check first for test pass/fail - might be old test re-analysed, analysis version would be in properties
        for test_run in test_runs_info:
            # check some common keys at top-level first
            for key in ["passed", "problems"]:
                if test_run[key] != new_test_run.get(key, False):
                    log.info(
                        "  - %s does not have the same %s value", test_run["id"], key
                    )
                    test_run_ids.remove(test_run["id"])
                    continue
            # if the test run has been removed by the previous check then move to the next test run
            if test_run["id"] not in test_run_ids:
                continue

            # then check properties, defects, comments, parameters
            properties = {
                prop["code"]: prop["value"]
                for prop in (test_run.get("properties", []) or [])
            }

            with contextlib.suppress(ValueError):
                new_test_run["properties"] = {
                    key: type(properties[key])(new_test_run["properties"][key])
                    for key in new_test_run["properties"]
                }  ## in case new_test_run are missing some keys
                if new_test_run["properties"] != properties:
                    log.info("  - %s does not have the same properties", test_run["id"])
                    test_run_ids.remove(test_run["id"])
                    continue

            ## TODO? check if type coercion is needed here as well
            defects = [
                {key: value for key, value in defect.items() if key != "code"}
                for defect in (test_run.get("defects", []) or [])
            ]
            if defects != new_test_run.get("defects", []):
                log.info("  - %s does not have the same set of defects", test_run["id"])
                test_run_ids.remove(test_run["id"])
                continue

            comments = [
                comment["comment"] for comment in (test_run.get("comments", []) or [])
            ]
            if comments != new_test_run.get("comments", []):
                log.info(
                    "  - %s does not have the same set of comments", test_run["id"]
                )
                test_run_ids.remove(test_run["id"])
                continue

            # check results - if variables above were identical AND the results are identical, then the test run is identical
            parameters = {}
            image_params = {}
            for param in test_run.get("results", []) or []:
                if param["dataType"] != "image":
                    parameters[param["code"]] = param["value"]
                else:
                    parameters[param["code"]] = None
                    image_params[param["code"]] = None

            if parameters != {**new_test_run["results"], **image_params}:
                log.info("  - %s does not have the same results", test_run["id"])
                test_run_ids.remove(test_run["id"])
                continue

        return test_run_ids
