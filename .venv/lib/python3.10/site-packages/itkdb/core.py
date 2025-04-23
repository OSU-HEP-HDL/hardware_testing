from __future__ import annotations

import logging
import pickle  # nosec
import time
from pathlib import Path
from typing import Any, Callable, ClassVar, cast

import cachecontrol.caches.file_cache
import requests
from cachecontrol.heuristics import ExpiresAfter
from jose import jwt
from requests.status_codes import codes

from itkdb import exceptions
from itkdb._version import __version__
from itkdb.caching import CacheControlAdapter, CacheController
from itkdb.settings import settings
from itkdb.typing import UserLike

log = logging.getLogger(__name__)


class UserBearer(UserLike):
    """
    Class for managing bearer tokens.

    Args:
        bearer (str): Bearer token
        prefix_url (str): The prefix for all non-absolute URIs

    !!! note "Added in version 0.6.0"
    """

    def __init__(
        self,
        bearer: str = settings.ITKDB_AUDREYTWO_API_KEY,
    ):
        # session handling (for injection in tests)
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": f"itkdb/{__version__}"})
        # store last call to authenticate
        self._response: requests.Response | None = None
        self._status_code: int | None = None
        # initialization configuration
        self._bearer: str = bearer

    def authenticate(self) -> bool:
        return True

    @property
    def bearer(self) -> str:
        """
        The bearer token.
        """
        return self._bearer

    def __repr__(self) -> str:
        return f"{self.__class__.__name__:s}(bearer={self.bearer})"


class User(UserLike):
    """
    Class for managing user tokens and authentication flow.

    Args:
        access_code1 (str): ITkPD Access Code 1
        access_code2 (str): ITkPD Access Code 2
        audience (str): ITkPD OIDC Audience
        prefix_url (str): The prefix for all non-absolute URIs
        jwt_options (dict): Additional JWT options to pass through
        save_auth (pathlib.Path | str | None): If set, save authentication information to the file path specified
        auth_expiry_threshold (int): Number of seconds until token expiration to do a reauthentication

    !!! note "Changed in version 0.4.0"
        - renamed `accessCode1` / `accessCode2` to `access_code1` / `access_code2`

    !!! note "Added in version 0.4.7"
        - `auth_expiry_threshold` to force reauthentication sooner

    """

    def __init__(
        self,
        access_code1: str = settings.ITKDB_ACCESS_CODE1,
        access_code2: str = settings.ITKDB_ACCESS_CODE2,
        audience: str = settings.ITKDB_ACCESS_AUDIENCE,
        prefix_url: str = settings.ITKDB_AUTH_URL,
        jwt_options: dict[str, Any] | None = None,
        save_auth: Path | str | None = None,
        auth_expiry_threshold: int = 15,
    ):
        # session handling (for injection in tests)
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": f"itkdb/{__version__}"})
        # store last call to authenticate
        self._response: requests.Response | None = None
        self._status_code: int | None = None
        # store jwks for validation/verification
        self._jwks: dict[str, Any] | None = None
        # store information after authorization occurs
        self._access_token: str | None = None
        self._raw_id_token: str | None = None
        self._id_token: dict[str, Any] | None = None
        # initialization configuration
        self._access_code1: str = access_code1
        self._access_code2: str = access_code2
        self._audience: str = audience
        self._prefix_url: str = prefix_url
        # update jwt_options if provided
        self._jwt_options: dict[str, Any] = {
            "leeway": int(settings.ITKDB_LEEWAY)
        }  # **jwt_options, python3 only
        self._jwt_options.update(jwt_options or {})
        # serialization/persistence
        self._save_auth: Path | None = Path(save_auth) if save_auth else None
        self.auth_expiry_threshold: int = auth_expiry_threshold
        self._load()

    def _load(self) -> bool:
        if self._save_auth and self._save_auth.is_file():
            try:
                with self._save_auth.open("rb") as _pickle_file:
                    saved_user = pickle.load(_pickle_file)  # nosec
                if saved_user.is_expired():
                    log.warning(
                        "Saved user session is expired in %s. Creating a new one.",
                        self._save_auth,
                    )
                    return False
                if saved_user.is_authenticated():
                    self.__dict__.update(saved_user.__dict__)
                    return True
            except pickle.UnpicklingError:
                log.warning(
                    "Unable to load user session from %s. Creating a new one.",
                    self._save_auth,
                )
        return False

    def _dump(self) -> bool:
        if self.is_authenticated() and not self.is_expired() and self._save_auth:
            with self._save_auth.open("wb") as fpointer:
                try:
                    pickle.dump(self, fpointer, pickle.HIGHEST_PROTOCOL)
                    return True
                except (pickle.PicklingError, AttributeError, TypeError):
                    log.warning("Unable to save user session to %s.", self._save_auth)
            return False
        return False

    def _load_jwks(self, force: bool = False) -> None:
        if self._jwks is None or force:
            self._jwks = self._session.get(
                "https://uuidentity.plus4u.net/uu-oidc-maing02/bb977a99f4cc4c37a2afce3fd599d0a7/oidc/listKeys"
            ).json()

    def _parse_id_token(self) -> None:
        if self._raw_id_token:
            self._load_jwks()
            assert self._jwks
            self._id_token = jwt.decode(
                self._raw_id_token,
                self._jwks,
                algorithms="RS256",
                audience=self._audience,
                options=self._jwt_options,
            )

    def authenticate(self) -> bool:
        """
        Authenticate the current user if not already authenticated.

        If the current user session is expired, this will attempt to reauthenticate.
        """
        # if not expired, do nothing
        if self.is_authenticated():
            if not self.is_expired():
                return True
            log.warning("User session is expired. Creating a new one.")

        # session-less request
        response = self._session.post(
            requests.compat.urljoin(self._prefix_url, "grantToken"),
            json={
                "grant_type": "password",
                "accessCode1": self._access_code1,
                "accessCode2": self._access_code2,
                "scope": settings.ITKDB_ACCESS_SCOPE,
            },
        )
        self._response = response
        self._status_code = response.status_code
        self._access_token = response.json().get("access_token")
        self._raw_id_token = response.json().get("id_token")
        self._id_token = None

        # handle parsing the id token
        self._parse_id_token()

        if not self.is_authenticated():
            raise exceptions.ResponseException(self._response)

        self._dump()
        return True

    @property
    def access_code1(self) -> str:
        """
        The first access code.
        """
        return self._access_code1

    @property
    def access_code2(self) -> str:
        """
        The second access code.
        """
        return self._access_code2

    @property
    def access_token(self) -> str | None:
        """
        The opaque access token for the user.
        """
        return self._access_token

    @property
    def id_token(self) -> dict[str, str | list[str] | int]:
        """
        The parsed JWT identity token for the user.
        """
        return self._id_token if self._id_token else {}

    @property
    def name(self) -> str:
        """
        The name for the user.
        """
        return cast(str, self.id_token.get("name", ""))

    @property
    def expires_at(self) -> int:
        """
        The Epoch Unix Timestamp that the user session expires at.
        """
        return cast(int, self.id_token.get("exp", 0))

    @property
    def expires_in(self) -> int:
        """
        The time until expiration in seconds.
        """
        expires_in: float = self.expires_at - time.time()
        return 0 if expires_in < 0 else int(expires_in)

    @property
    def identity(self) -> str:
        """
        The identity for the user in the ITk Production Database.
        """
        return cast(str, self.id_token.get("uuidentity", ""))

    @property
    def bearer(self) -> str:
        """
        The bearer token for the user.
        """
        return self._raw_id_token if self._raw_id_token else ""

    def is_authenticated(self) -> bool:
        """
        Whether current user is authenticated.
        """
        return bool(
            self._status_code == codes["ok"]
            and self._access_token
            and self._raw_id_token
        )

    def is_expired(self) -> bool:
        """
        Whether current user session is expired given the expiration threshold.
        """
        return not self.expires_in > self.auth_expiry_threshold

    def __repr__(self) -> str:
        return f"{self.__class__.__name__:s}(name={self.name:s}, expires_in={self.expires_in:d}s)"


class Session(requests.Session):
    """
    Lightweight wrapper around `requests.Session` with basic error-handling, auto-(re)authentication, and URI prefixing.

    For more information, see python requests.

    Attributes:
        STATUS_EXCEPTIONS (dict): Mapping from status code to [itkdb.exceptions][]
        SUCCESS_STATUSES (dict): List of status codes that are OK
        auth (callable): Call [itkdb.core.Session.authorize][]
        prefix_url (str): The prefix for all non-absolute URIs
        user (itkdb.core.User): The user object for authentication

    Args:
        user (itkdb.core.User): A user object. Create one if not specified.
        prefix_url (str): The prefix url to use for all requests.
        save_auth (pathlib.Path | str | None): A file path to where to save authentication information.
        cache (str): A CacheControl.caches object for cache (default: cachecontrol.caches.file_cache.FileCache). Set to False to disable cache.
        expires_after (dict): The arguments are the same as the datetime.timedelta object. This will override or add the Expires header and override or set the Cache-Control header to public.
        auth_expiry_threshold (int): Number of seconds until token expiration to do a reauthentication (see itkdb.core.User)

    !!! note "Added in version 0.4.7"
        - `auth_expiry_threshold` to force reauthentication sooner

    """

    STATUS_EXCEPTIONS: ClassVar[dict[int, type[exceptions.ITkDBException]]] = {
        codes["bad_gateway"]: exceptions.ServerError,
        codes["bad_request"]: exceptions.BadRequest,
        codes["conflict"]: exceptions.Conflict,
        codes["found"]: exceptions.Redirect,
        codes["forbidden"]: exceptions.Forbidden,
        codes["gateway_timeout"]: exceptions.ServerError,
        codes["internal_server_error"]: exceptions.ServerError,
        codes["media_type"]: exceptions.SpecialError,
        codes["not_found"]: exceptions.NotFound,
        codes["request_entity_too_large"]: exceptions.TooLarge,
        codes["service_unavailable"]: exceptions.ServerError,
        codes["unauthorized"]: exceptions.Forbidden,
        codes["unavailable_for_legal_reasons"]: exceptions.UnavailableForLegalReasons,
    }
    SUCCESS_STATUSES: ClassVar[set[int]] = {codes["created"], codes["ok"]}

    def __init__(
        self,
        user: User | None = None,
        prefix_url: str = settings.ITKDB_API_URL,
        save_auth: Path | str | None = None,
        cache: bool | object = True,
        expires_after: dict[str, int] | None = None,
        auth_expiry_threshold: int = 15,
    ):
        super().__init__()
        self.headers.update({"User-Agent": f"itkdb/{__version__}"})
        self.user: UserLike = (
            user
            if user
            else User(save_auth=save_auth, auth_expiry_threshold=auth_expiry_threshold)
        )
        self.auth: Callable[[requests.PreparedRequest], requests.PreparedRequest] = (
            self.authorize
        )
        self.prefix_url: str = prefix_url
        # store last call
        self._response: requests.Response | None = None

        cache_options = {}
        if cache:
            cache = (
                cachecontrol.caches.file_cache.FileCache(".webcache")
                if cache is True
                else cache
            )
            cache_options.update({"cache": cache})

        # handle expirations for cache
        if expires_after and isinstance(expires_after, dict):
            cache_options.update({"heuristic": ExpiresAfter(**expires_after)})

        if cache_options:
            # add caching
            super().mount(
                self.prefix_url,
                CacheControlAdapter(controller_class=CacheController, **cache_options),
            )

    def authorize(self, req: requests.PreparedRequest) -> requests.PreparedRequest:
        """
        Add authentication information to the request by updating the headers.
        """
        if req.url.startswith(self.prefix_url):  # type: ignore[union-attr]
            self.user.authenticate()
            req.headers.update({"Authorization": f"Bearer {self.user.bearer:s}"})
        return req

    def _normalize_url(self, url: str | bytes) -> str:
        url_str = url.decode("utf-8") if isinstance(url, bytes) else url
        return requests.compat.urljoin(self.prefix_url, url_str)

    def _check_response(self, response: requests.Response) -> None:
        if response.status_code in self.STATUS_EXCEPTIONS:
            raise self.STATUS_EXCEPTIONS[response.status_code](response)

        try:
            response.raise_for_status()
        except BaseException as err:
            raise exceptions.UnhandledResponse(response) from err

    def prepare_request(self, request: requests.Request) -> requests.PreparedRequest:
        request.url = self._normalize_url(request.url)
        return super().prepare_request(request)

    def send(
        self, request: requests.PreparedRequest, **kwargs: Any
    ) -> requests.Response:
        response = super().send(request, **kwargs)
        self._response = response
        log.debug(
            "Response: %s (%s bytes)",
            response.status_code,
            response.headers.get("content-length"),
        )
        self._check_response(response)
        return response

    def request(
        self, method: str | bytes, url: str | bytes, *args: Any, **kwargs: Any
    ) -> requests.Response:
        url = self._normalize_url(url)
        return super().request(method, url, *args, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> requests.Response:
        if len(args) == 1:
            return self.send(self.prepare_request(*args), **kwargs)

        return self.request(*args, **kwargs)
