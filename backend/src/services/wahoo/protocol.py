"""Low-level classes for interacting directly with the Wahoo API webservers.

Inspired by the stravalib library for Strava:
https://github.com/stravalib/stravalib/blob/main/src/stravalib/protocol.py
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, TypedDict
from urllib.parse import urlencode, urljoin, urlunsplit

import requests

if TYPE_CHECKING:
    from _typeshed import SupportsRead

Scope = Literal[
    "email",
    "user_read",
    "user_write",
    "power_zones_read",
    "power_zones_write",
    "workouts_read",
    "workouts_write",
    "plans_read",
    "plans_write",
    "routes_read",
    "routes_write",
    "offline_data",
]

RequestMethod = Literal["GET", "POST", "PUT", "DELETE"]


class AccessInfo(TypedDict):
    """Dictionary containing token exchange response from Wahoo Cloud API."""

    access_token: str
    """A short live token the access Wahoo Cloud API"""

    refresh_token: str
    """The refresh token for this user, to be used to get the next access token
    for this user. Please expect that this value can change anytime you
    retrieve a new access token. Once a new refresh token code has been
    returned, the older code will no longer work.
    """

    expires_at: int
    """The number of seconds since the epoch when the provided access token
    will expire"""


class ApiV1:
    """This class is responsible for performing the HTTP requests, rate
    limiting, and error handling."""

    server = "api.wahooligan.com"
    api_base = "/v1"

    def __init__(
        self,
        access_token: str | None = None,
        requests_session: requests.Session | None = None,
        rate_limiter: Callable[[dict[str, str], RequestMethod], None] | None = None,
        token_expires: int | None = None,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        """Initialize this protocol client, optionally providing a (shared)
        :class:`requests.Session` object.

        Parameters
        ----------
        access_token : str
            The token that provides access to a specific Wahoo account.
        requests_session : :class:`requests.Session`
            An existing :class:`requests.Session` object to use.
        rate_limiter : Callable[[dict[str, str], RequestMethod], None], optional
            A callable used to enforce rate-limiting for API requests.
            The callable accepts a dict of headers and the
            HTTP request method as arguments. Defaults to None.
        token_expires: int
            Epoch time in seconds when the token expires
        refresh_token: str
            Refresh token used to re-authenticate with Wahoo
        client_id: str
            client id for the Wahoo APP pulled from the users envt
        client_secret: str
            client secret for the Wahoo app pulled from the users envt
        """
        self.log = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self.access_token: str | None = access_token
        self.token_expires: int | None = token_expires
        self.refresh_token: str | None = refresh_token
        self.client_id: str | None = None
        self.client_secret: str | None = None
        if requests_session:
            self.rsession: requests.Session = requests_session
        else:
            self.rsession = requests.Session()

        self.rate_limiter = rate_limiter or (lambda _request_params, _method: None)
        # Check for credentials when initializing
        self._check_credentials()

    def _check_credentials(self) -> None:
        """Gets Wahoo client_id and secret credentials from user's environment.

        If the user environment is populated with both values and
        client_id is a proper int, it returns a tuple with both values.
        Otherwise it returns None.

        Returns
        -------
        None
            If the client_id and secret are available it populates self
            with both variables to support automatic token refresh.
        """
        # Default both to None; set if they are available in the correct format
        client_id: str | None = None
        client_secret: str | None = None

        client_id_str = os.environ.get("WAHOO_CLIENT_ID")
        client_secret = os.environ.get("WAHOO_CLIENT_SECRET")
        silence_token_warning = os.environ.get("SILENCE_TOKEN_WARNINGS")

        # Make sure client_id exists
        if client_id_str:
            client_id = client_id_str
        elif silence_token_warning is None:
            logging.warning(
                "Please make sure your WAHOO_CLIENT_ID is set in your environment. "
                "Add SILENCE_TOKEN_WARNINGS=true to your environment to disable "
                "this error."
            )

        if (client_id and client_secret) or silence_token_warning:
            self.client_id = client_id
            self.client_secret = client_secret
        else:
            logging.warning(
                "WAHOO_CLIENT_ID and WAHOO_CLIENT_SECRET not found in your "
                "environment. Please refresh your access_token manually. "
                "Or add WAHOO_CLIENT_ID and WAHOO_CLIENT_SECRET to your environment. "
                "Add SILENCE_TOKEN_WARNINGS=true to your environment to silence "
                "this warning."
            )
        return None

    def _request(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        files: dict[str, SupportsRead[str | bytes]] | None = None,
        headers: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        method: RequestMethod = "GET",
        check_for_errors: bool = True,
    ) -> Any:
        """Perform the underlying request, returning the parsed JSON results.

        Before running, this method will check to make sure that your
        access_token is valid. If it isn't, it will refresh it and then make
        the requested Wahoo Cloud API call.

        Parameters
        ----------
        url : str
            The request URL.
        params : Dict[str,Any]
            Request parameters
        files : Dict[str,file]
            Dictionary of file name to file-like objects.
        headers : Dict[str,Any]
            Request headers
        data : Dict[str,Any]
            Form data to send in request body
        method : str
            The request method (GET/POST/etc.)
        check_for_errors : bool
            Whether to raise an error or not.

        Returns
        -------
        Dict[str, Any]
            The parsed JSON response.
        """

        # Only refresh token if we know the users' environment is setup
        if "/oauth/token" not in url and self.client_id and self.client_secret:
            self.refresh_expired_token()

        url = self.resolve_url(url)
        self.log.info(f"{method} {url!r} with params {params!r}")
        if params is None:
            params = {}

        # If headers are provided, use them (for Authorization header)
        # Otherwise, add access_token to params (default behavior)
        if headers is None:
            headers = {}
            if self.access_token:
                params["access_token"] = self.access_token

        # Log the full request details
        self.log.info(f"Sending {method} request to {url}")
        if params:
            self.log.info(f"  Params: {params}")
        if headers:
            for key, value in headers.items():
                if key.lower() == "authorization":
                    truncated = (
                        value[:30] + "..."
                        if isinstance(value, str) and len(value) > 30
                        else value
                    )
                    self.log.info(f"  {key}: {truncated}")
                else:
                    self.log.info(f"  {key}: {value}")
        if data:
            self.log.info(f"  Data: {list(data.keys())}")

        # Build kwargs for request based on method
        request_kwargs: dict[str, Any] = {"params": params, "headers": headers}
        if data is not None:
            request_kwargs["data"] = data
        if files is not None:
            request_kwargs["files"] = files

        methods = {
            "GET": self.rsession.get,
            "POST": self.rsession.post,
            "PUT": self.rsession.put,
            "DELETE": self.rsession.delete,
        }

        try:
            requester = methods[method.upper()]
        except KeyError:
            raise ValueError(f"Invalid/unsupported request method specified: {method}")

        raw = requester(url, **request_kwargs)  # type: ignore[operator]
        # Rate limits are taken from HTTP response headers
        # https://cloud-api.wahooligan.com/#rate-limiting
        self.rate_limiter(raw.headers, method)

        if check_for_errors:
            self._handle_protocol_error(raw)

        # 204 = No content
        if raw.status_code in [204]:
            resp = {}
        else:
            resp = raw.json()
            if "created_at" in resp and "expires_in" in resp:
                resp["expires_at"] = resp["created_at"] + resp["expires_in"]
            print(resp)

        return resp

    def _token_expired(self) -> bool:
        """Checks if a token has expired or not. Returns True if it's expired.

        Returns
        -------
        bool
            True if token has expired, otherwise returns false
        """
        if self.token_expires:
            if time.time() > self.token_expires:
                logging.info("Your token has expired; Refreshing it now.")
                return True
            else:
                return False
        else:
            logging.warning(
                "Please make sure you've set client.token_expires if you"
                " want automatic token refresh to work"
            )
            return False

    def refresh_expired_token(self) -> None:
        """Checks to see if a token has expired and auto refreshes it
        if the user has setup their environment with the client
        secret information.

        Returns
        -------
        None
            If all is setup properly, updates and resets the access_token
            attribute. Otherwise it logs a warning
        """
        if not self.refresh_token:
            logging.warning(
                "Please set client.refresh_token if you want to use"
                "the auto token-refresh feature"
            )
            return

        # Token is not yet expired, move on
        if not self._token_expired():
            return

        # This should never be false, BUT mypy wants a reminder that these values
        # are populated
        assert self.client_id is not None, "client_id is required but is None."
        assert self.client_secret is not None, "client_secret is required but is None."

        self.refresh_access_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            refresh_token=self.refresh_token,
        )
        return

    def authorization_url(
        self,
        client_id: str,
        redirect_uri: str,
        approval_prompt: Literal["auto", "force"] = "auto",
        scope: list[Scope] | Scope | None = None,
        state: str | None = None,
    ) -> str:
        """Get the URL needed to authorize your application to access a Wahoo
        user's information.

        See https://cloud-api.wahooligan.com/#authentication

        Parameters
        ----------
        client_id : str
            The developer client id.
        redirect_uri : str
            The URL that Wahoo will redirect to after successful (or
            failed) authorization.
        approval_prompt : str
            Whether to prompt for approval even if approval already
            granted to app. Choices are 'auto' or 'force'.  (Default is
            'auto')
        scope : list[Scope]
            The access scope required.  Omit to imply "user_read" and
            "workouts_read" Valid values are 'user_read', 'user_write',
            'power_zones_read', 'power_zones_write', 'workouts_read',
            'workouts_write', 'plans_read', 'plans_write', 'routes_read',
            'routes_write', 'offline_data'.
        state : str
            An arbitrary variable that will be returned to your
            application in the redirect URI.

        Returns
        -------
        str
            The URL to use for authorization link.
        """
        assert approval_prompt in ("auto", "force")
        if scope is None:
            scope = ["user_read"]
        elif isinstance(scope, (str, bytes)):
            scope = [scope]

        # # cf: https://cloud-api.wahooligan.com/#authorization
        # unsupported = set(scope) - {
        #     "email",
        #     "user_read",
        #     "user_write",
        #     "workouts_read",
        #     "workouts_write",
        #     "offline_data",
        # }

        # assert not unsupported, f"Unsupported scope value(s): {unsupported}"

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "approval_prompt": approval_prompt,
            "scope": " ".join(scope),
            "response_type": "code",
        }
        if state is not None:
            params["state"] = state

        return urlunsplit(
            ("https", self.server, "/oauth/authorize", urlencode(params), "")
        )

    def exchange_code_for_token(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        code: str,
    ) -> AccessInfo:
        """Exchange the temporary authorization code (returned with redirect
        from Wahoo authorization URL) for a short-lived access token and a
        refresh token (used to obtain the next access token later on).

        See https://cloud-api.wahooligan.com/#authentication

        Parameters
        ----------
        client_id : str
            The developer client id.
        client_secret : str
            The developer client secret
        redirect_uri : str
            The URL that Wahoo will redirect to after successful (or
            failed) authorization.
        code : str
            The temporary authorization code

        Returns
        -------
        dict
            Dictionary containing the access_token, refresh_token and
            expires_at (number of seconds since Epoch when the provided
            access token will expire)
        """
        # The method returns: No rates present in response headers
        response = self._request(
            f"https://{self.server}/oauth/token",
            params={
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
            },
            method="POST",
        )
        access_info: AccessInfo = {
            "access_token": response["access_token"],
            "refresh_token": response["refresh_token"],
            "expires_at": response["expires_at"],
        }
        self.access_token = response["access_token"]
        return access_info

    def refresh_access_token(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> AccessInfo:
        """Exchanges the previous refresh token for a short-lived access token
        and a new refresh token (used to obtain the next access token later on)

        Parameters
        ----------
        client_id : str
            The developer client id.
        client_secret : str
            The developer client secret
        refresh_token : str
            The refresh token obtain from a previous authorization
            request

        Returns
        -------
        dict
            Dictionary containing the access_token, refresh_token and
            expires_at (number of seconds since Epoch when the provided
            access token will expire)

        Notes
        -----
        This method is user facing. Here, we don't populate client_id and client_secret
        from self; A user can call this method and refresh the token manually with those
        values.
        """
        response = self._request(
            f"https://{self.server}/oauth/token",
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            method="POST",
        )
        access_info: AccessInfo = {
            "access_token": response["access_token"],
            "refresh_token": response["refresh_token"],
            "expires_at": response["expires_at"],
        }
        self.access_token = response["access_token"]
        # Update expires_at and refresh to support automatic refresh
        self.refresh_token = response["refresh_token"]
        self.token_expires = response["expires_at"]

        return access_info

    def resolve_url(self, url: str) -> str:
        """

        Parameters
        ----------
        url : str
            url string to be be accessed / resolved

        Returns
        -------
        str
            A string representing the full properly formatted (https) url.
        """
        if not url.startswith("http"):
            url = urljoin(
                f"https://{self.server}",
                self.api_base + "/" + url.strip("/"),
            )
        return url

    def _handle_protocol_error(self, response: requests.Response) -> requests.Response:
        """Parses the raw response from the server, raising a ValueError
        if the server returned an error.

        Parameters
        ----------
        response
            The response object.

        Raises
        ------
        ValueError
            If the response contains an error.
        """
        error_str = None
        try:
            json_response = response.json()
        except ValueError:
            # Not JSON, log the raw text
            self.log.error(f"Non-JSON error response: {response.text[:500]}")
            pass
        else:
            # Log the full JSON response for debugging
            self.log.error(f"Error response JSON: {json_response}")
            # Check for error field first (common in Wahoo API)
            if "error" in json_response:
                error_str = json_response.get("error")
            elif "message" in json_response or "errors" in json_response:
                error_str = "{}: {}".format(
                    json_response.get("message", "Undefined error"),
                    json_response.get("errors"),
                )

        # Raise ValueError with original information
        if response.status_code >= 400:
            msg = f"{response.status_code} {response.reason}"
            if error_str:
                msg += f" - {error_str}"
            raise ValueError(msg)

        return response

    def _extract_referenced_vars(self, s: str) -> list[str]:
        """Utility method to find the referenced format variables in a string.
        (Assumes string.format() format vars.)

        Parameters
        ----------
        s
            The string that contains format variables. (e.g.
            "{foo}-text")

        Returns
        -------
        list
            The list of referenced variable names. (e.g. ['foo'])
        """
        d: dict[str, int] = {}
        while True:
            try:
                s.format(**d)
            except KeyError as exc:
                # exc.args[0] contains the name of the key that was not found;
                # 0 is used because it appears to work with all types of
                # placeholders.
                d[exc.args[0]] = 0
            else:
                break
        return list(d.keys())

    def get_user(self) -> dict[str, Any]:
        """Get authenticated user information.

        See https://cloud-api.wahooligan.com/#get-authenticated-user

        Returns
        -------
        dict[str, Any]
            Dictionary containing user information

        Raises
        ------
        ValueError
            If no access token is available or if the request fails.
        """
        if not self.access_token:
            raise ValueError("No access token available to get user information")

        # Get user endpoint is GET /v1/user with Authorization header
        url = self.resolve_url("user")
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Use _request method with custom headers
        return self._request(url, headers=headers, method="GET", check_for_errors=True)

    def get_route(
        self,
        route_id: int,
    ) -> dict[str, Any]:
        """Get a route by ID from Wahoo Cloud.

        See https://cloud-api.wahooligan.com/#get-a-route

        Parameters
        ----------
        route_id : int
            ID of the route to retrieve

        Returns
        -------
        dict[str, Any]
            Response from Wahoo API containing the route information

        Raises
        ------
        ValueError
            If no access token is available or if the request fails.
        """
        if not self.access_token:
            raise ValueError("No access token available to get route")

        url = self.resolve_url(f"routes/{route_id}")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        return self._request(url, headers=headers, method="GET", check_for_errors=True)

    def get_routes(self) -> list[dict[str, Any]]:
        """Get all routes from Wahoo Cloud.

        Returns
        -------
        list[dict[str, Any]]
            List of routes from Wahoo API

        Raises
        ------
        ValueError
            If no access token is available or if the request fails.
        """
        if not self.access_token:
            raise ValueError("No access token available to get routes")

        url = self.resolve_url("routes")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        return self._request(url, headers=headers, method="GET", check_for_errors=True)

    def create_route(
        self,
        route_file: str,
        filename: str,
        route_name: str,
        start_lat: float,
        start_lng: float,
        distance: float,
        ascent: float,
        descent: float,
        description: str = "",
        external_id: str | None = None,
        provider_updated_at: str | None = None,
        workout_type_family_id: int = 0,
    ) -> dict[str, Any]:
        """Create a new route in Wahoo Cloud.

        Parameters
        ----------
        route_file : str
            Base64-encoded route file content
            (data URI format: data:application/vnd.fit;base64,...)
        filename : str
            Name of the route file (e.g., 'route.fit')
        route_name : str
            Name of the route
        start_lat : float
            Starting latitude
        start_lng : float
            Starting longitude
        distance : float
            Total distance in meters
        ascent : float
            Ascent in meters
        descent : float
            Descent in meters
        description : str
            Description of the route (optional)
        external_id : str | None
            External identifier for the route (optional)
        provider_updated_at : str | None
            ISO timestamp of when route was updated by provider (optional)
        workout_type_family_id : int
            Workout type family ID (default: 0)

        Returns
        -------
        dict[str, Any]
            Response from Wahoo API containing the created route information
        """
        # Prepare form data - these will be sent as form fields
        data: dict[str, Any] = {
            "route[file]": route_file,
            "route[filename]": filename,
            "route[name]": route_name,
            "route[description]": description,
            "route[workout_type_family_id]": str(workout_type_family_id),
        }

        data["route[external_id]"] = external_id or filename
        data["route[provider_updated_at]"] = provider_updated_at or ""
        data["route[start_lat]"] = str(start_lat)
        data["route[start_lng]"] = str(start_lng)
        data["route[distance]"] = str(distance)
        data["route[ascent]"] = str(ascent)
        data["route[descent]"] = str(descent)

        self.log.info(f"Creating route '{route_name}' in Wahoo Cloud")

        # Use _request method for all the heavy lifting
        params = {}
        if self.access_token:
            params["access_token"] = self.access_token

        return self._request("routes", data=data, params=params, method="POST")

    def update_route(
        self,
        route_id: int,
        route_file: str,
        filename: str,
        route_name: str,
        start_lat: float,
        start_lng: float,
        distance: float,
        ascent: float,
        descent: float,
        description: str = "",
        provider_updated_at: str | None = None,
        workout_type_family_id: int = 0,
    ) -> dict[str, Any]:
        """Update an existing route in Wahoo Cloud.

        Parameters
        ----------
        route_id : int
            ID of the route to update
        route_file : str
            Base64-encoded route file content
            (data URI format: data:application/vnd.fit;base64,...)
        filename : str
            Name of the route file (e.g., 'route.fit')
        route_name : str
            Name of the route
        start_lat : float
            Starting latitude
        start_lng : float
            Starting longitude
        distance : float
            Total distance in meters
        ascent : float
            Ascent in meters
        descent : float
            Descent in meters
        description : str
            Description of the route (optional)
        provider_updated_at : str | None
            ISO timestamp of when route was updated by provider (optional)
        workout_type_family_id : int
            Workout type family ID (default: 0)

        Returns
        -------
        dict[str, Any]
            Response from Wahoo API containing the updated route information

        Raises
        ------
        ValueError
            If no access token is available or if the request fails.
        """
        if not self.access_token:
            raise ValueError("No access token available to update route")

        # Prepare form data - these will be sent as form fields
        data: dict[str, Any] = {
            "route[file]": route_file,
            "route[filename]": filename,
            "route[name]": route_name,
            "route[description]": description,
            "route[workout_type_family_id]": str(workout_type_family_id),
        }

        if provider_updated_at:
            data["route[provider_updated_at]"] = provider_updated_at
        data["route[start_lat]"] = str(start_lat)
        data["route[start_lng]"] = str(start_lng)
        data["route[distance]"] = str(distance)
        data["route[ascent]"] = str(ascent)
        data["route[descent]"] = str(descent)

        self.log.info(f"Updating route {route_id} '{route_name}' in Wahoo Cloud")

        # Use _request method for all the heavy lifting
        headers = {"Authorization": f"Bearer {self.access_token}"}
        return self._request(
            f"routes/{route_id}", data=data, headers=headers, method="PUT"
        )

    def deauthorize(self) -> None:
        """Deauthorize the application by revoking access permissions.

        This causes the application to be removed from the user's
        authorized applications list.

        See https://cloud-api.wahooligan.com/#deauthorize

        Raises
        ------
        ValueError
            If no access token is available or if the request fails.
        """
        if not self.access_token:
            raise ValueError("No access token available for deauthorization")

        # Deauthorize endpoint is DELETE /v1/permissions with Authorization header
        url = self.resolve_url("permissions")
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Use _request method with custom headers
        self._request(url, headers=headers, method="DELETE", check_for_errors=True)

    def delete_route(self, route_id: int) -> None:
        """Delete a route from Wahoo Cloud.

        Parameters
        ----------
        route_id : int
            ID of the route to delete

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If no access token is available or if the request fails.
        """
        if not self.access_token:
            raise ValueError("No access token available to delete route")

        url = self.resolve_url(f"routes/{route_id}")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        return self._request(
            url, headers=headers, method="DELETE", check_for_errors=True
        )

    def get(self, url: str, check_for_errors: bool = True, **kwargs: Any) -> Any:
        """Performs a generic GET request for specified params, returning the
        response.

        Parameters
        ----------
        url : str
            String representing the url to retrieve
        check-for_errors: bool (default = True)
            Flag used to raise an error (or not)

        Returns
        -------
        dict
            Performs the request and returns a JSON object deserialized as dict

        """
        referenced = self._extract_referenced_vars(url)
        url = url.format(**kwargs)
        params = {k: v for k, v in kwargs.items() if k not in referenced}
        return self._request(url, params=params, check_for_errors=check_for_errors)

    def post(
        self,
        url: str,
        files: dict[str, SupportsRead[str | bytes]] | None = None,
        check_for_errors: bool = True,
        **kwargs: Any,
    ) -> Any:
        """Performs a generic POST request for specified params, returning the
        response.

        Parameters
        ----------
        url : str
            Url string to be requested.
        files: dict
            Dictionary of file name to file-like objects. Used by _requests
        check_for_errors: bool
            Whether to raise an error (or not)

        Returns
        -------
            Deserialized request output.

        """
        referenced = self._extract_referenced_vars(url)
        url = url.format(**kwargs)
        params = {k: v for k, v in kwargs.items() if k not in referenced}
        return self._request(
            url,
            params=params,
            files=files,
            method="POST",
            check_for_errors=check_for_errors,
        )

    def put(self, url: str, check_for_errors: bool = True, **kwargs: Any) -> Any:
        """Performs a generic PUT request for specified params, returning the
        response.

        Parameters
        ----------
        url : str
            String representing url to access.
        check_for_errors: bool
            Whether to raise an error (or not)

        Returns
        -------
        Replaces current online content with new content.

        """
        referenced = self._extract_referenced_vars(url)
        url = url.format(**kwargs)
        params = {k: v for k, v in kwargs.items() if k not in referenced}
        return self._request(
            url, params=params, method="PUT", check_for_errors=check_for_errors
        )

    def delete(self, url: str, check_for_errors: bool = True, **kwargs: Any) -> Any:
        """Performs a generic DELETE request for specified params, returning
        the response.

        Parameters
        ----------
        url : str
            String representing url to access.
        check_for_errors: bool
            Whether to raise an error (or not)

        Returns
        -------
        Deletes specified current online content.
        """
        referenced = self._extract_referenced_vars(url)
        url = url.format(**kwargs)
        params = {k: v for k, v in kwargs.items() if k not in referenced}
        return self._request(
            url,
            params=params,
            method="DELETE",
            check_for_errors=check_for_errors,
        )
