"""Client for interacting with the Wahoo API."""

import logging
from typing import Any, Literal

from requests import Session

from .limiter import DefaultRateLimiter, RateLimiter
from .protocol import AccessInfo, ApiV1, Scope


class Client:
    """Main client class for interacting with the exposed Wahoo Cloud API methods.

    This class can be instantiated without an access_token when performing
    authentication; however, most methods will require a valid access token.

    """

    def __init__(
        self,
        access_token: str | None = None,
        rate_limit_requests: bool = True,
        rate_limiter: RateLimiter | None = None,
        requests_session: Session | None = None,
        token_expires: int | None = None,
        refresh_token: str | None = None,
    ) -> None:
        """
        Initialize a new client object.

        Parameters
        ----------
        access_token : str
            The token that provides access to a specific Wahoo account. If
            empty, assume that this account is not yet authenticated.
        rate_limit_requests : bool
            Whether to apply a rate limiter to the requests. (default True)
        rate_limiter : callable
            A :class:`.limiter.RateLimiter` object to use.
            If not specified (and rate_limit_requests is True), then
            :class:`limiter.DefaultRateLimiter` will be used.
        requests_session : requests.Session() object
            (Optional) pass request session object.
        token_expires : int
            epoch timestamp -- seconds since jan 1 1970 (Epoch timestamp)
            This represents the date and time that the token will expire. It is
            used to automatically check and refresh the token in the client
            method on all API requests.
        refresh_token : str

        """
        self.log = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

        if rate_limit_requests:
            if not rate_limiter:
                rate_limiter = DefaultRateLimiter()
        elif rate_limiter:
            raise ValueError(
                "Cannot specify rate_limiter object when rate_limit_requests is False"
            )

        self.protocol = ApiV1(
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires=token_expires,
            requests_session=requests_session,
            rate_limiter=rate_limiter,
        )

    @property
    def access_token(self) -> str | None:
        """The currently configured authorization token."""
        return self.protocol.access_token

    @access_token.setter
    def access_token(self, token_value: str | None) -> None:
        """Set the currently configured authorization token.

        Parameters
        ----------
        access_token : str
             User's access token

        Returns
        -------

        """
        self.protocol.access_token = token_value

    @property
    def token_expires(self) -> int | None:
        """The currently configured authorization token."""
        return self.protocol.token_expires

    @token_expires.setter
    def token_expires(self, expires_value: int) -> None:
        """Used to set and update the refresh token.

        Parameters
        ----------
        expires_value : int
             Current token expiration time (epoch seconds)

        Returns
        -------

        """
        self.protocol.token_expires = expires_value

    @property
    def refresh_token(self) -> str | None:
        """The currently configured authorization token."""
        return self.protocol.refresh_token

    @refresh_token.setter
    def refresh_token(self, refresh_value: str) -> None:
        """Used to set and update the refresh token.

        Parameters
        ----------
        refresh_value : str
             Current token refresh value.

        Returns
        -------
        None
            Updates the `refresh_token` attribute in the Client class.

        """
        self.protocol.refresh_token = refresh_value

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
            The URL that Wahoo will redirect to after successful (or failed)
            authorization.
        approval_prompt : str, default='auto'
            Whether to prompt for approval even if approval already granted to
            app.
            Choices are 'auto' or 'force'.
        scope : list[str], default = None
            The access scope required.  Omit to imply "read" and "activity:read"
            Valid values are 'email', 'user_read', 'user_write', 'power_zones_read',
            'power_zones_write', 'workouts_read', 'workouts_write', 'plans_read',
            'plans_write', 'routes_read', 'routes_write', 'offline_data'.
        state : str, default=None
            An arbitrary variable that will be returned to your application in
            the redirect URI.

        Returns
        -------
        str:
            A string containing the url required to authorize with the Wahoo
            API.

        """
        return self.protocol.authorization_url(
            client_id=client_id,
            redirect_uri=redirect_uri,
            approval_prompt=approval_prompt,
            scope=scope,
            state=state,
        )

    def exchange_code_for_token(
        self,
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
    ) -> AccessInfo:
        """Exchange the temporary authorization code (returned with redirect
        from Wahoo authorization URL) for a short-lived access token and a
        refresh token (used to obtain the next access token later on).

        Parameters
        ----------
        client_id : str
            The developer client id.
        client_secret : str
            The developer client secret
        code : str
            The temporary authorization code
        redirect_uri : str
            The URL that Wahoo will redirect to after successful (or
            failed) authorization.

        Returns
        -------
        AccessInfo
            TypedDictionary containing the access_token, refresh_token and
            expires_at (number of seconds since Epoch when the provided access
            token will expire)

        Notes
        -----
        Wahoo does not return any information during this exchange.
        """
        return self.protocol.exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            code=code,
            redirect_uri=redirect_uri,
        )

    def refresh_access_token(
        self, client_id: int, client_secret: str, refresh_token: str
    ) -> AccessInfo:
        """Exchanges the previous refresh token for a short-lived access token
        and a new refresh token (used to obtain the next access token later on).

        Parameters
        ----------
        client_id : str
            The developer client id.
        client_secret : str
            The developer client secret
        refresh_token : str
            The refresh token obtained from a previous authorization request

        Returns
        -------
        dict:
            Dictionary containing the access_token, refresh_token and expires_at
            (number of seconds since Epoch when the provided access
            token will expire)

        """
        return self.protocol.refresh_access_token(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )

    def deauthorize(self) -> None:
        """Deauthorize the application. This causes the application to be
        removed from the athlete's "My Apps" settings page.

        https://cloud-api.wahooligan.com/#deauthorize

        """
        self.protocol.deauthorize()

    def get_user(self) -> dict[str, Any]:
        """Get authenticated user information.

        https://cloud-api.wahooligan.com/#get-authenticated-user

        Returns
        -------
        dict[str, Any]
            Dictionary containing user information

        """
        return self.protocol.get_user()

    def get_route(self, route_id: int) -> dict[str, Any]:
        """Get a route by ID from Wahoo Cloud.

        https://cloud-api.wahooligan.com/#get-a-route

        Parameters
        ----------
        route_id : int
            ID of the route to retrieve

        Returns
        -------
        dict[str, Any]
            Dictionary containing the route information

        """
        return self.protocol.get_route(route_id=route_id)

    def get_routes(self) -> list[dict[str, Any]]:
        """Get all routes from Wahoo Cloud.

        Returns
        -------
        list[dict[str, Any]]
            List of routes from Wahoo API

        """
        return self.protocol.get_routes()

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
            Base64-encoded route file content (data URI format)
        filename : str
            Name of the route file
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
        return self.protocol.create_route(
            route_file=route_file,
            filename=filename,
            route_name=route_name,
            start_lat=start_lat,
            start_lng=start_lng,
            distance=distance,
            ascent=ascent,
            descent=descent,
            description=description,
            external_id=external_id,
            provider_updated_at=provider_updated_at,
            workout_type_family_id=workout_type_family_id,
        )

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
            Base64-encoded route file content (data URI format)
        filename : str
            Name of the route file
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
        """
        return self.protocol.update_route(
            route_id=route_id,
            route_file=route_file,
            filename=filename,
            route_name=route_name,
            start_lat=start_lat,
            start_lng=start_lng,
            distance=distance,
            ascent=ascent,
            descent=descent,
            description=description,
            provider_updated_at=provider_updated_at,
            workout_type_family_id=workout_type_family_id,
        )

    def upload_route(
        self,
        route_file: str,
        filename: str,
        route_name: str,
        description: str = "",
        external_id: str | None = None,
        provider_updated_at: str | None = None,
        workout_type_family_id: int = 0,
        start_lat: float | None = None,
        start_lng: float | None = None,
        distance: float | None = None,
        ascent: float | None = None,
        descent: float | None = None,
    ) -> dict[str, Any]:
        """Upload a route to Wahoo Cloud.

        Checks if route exists and updates if found, otherwise creates new.

        This method first tries to get the route by external_id.
        If the route exists, it updates it. Otherwise, it creates a new route.
        This ensures the upload never fails due to duplicate routes.

        Parameters
        ----------
        route_file : str
            Base64-encoded route file content (data URI format)
        filename : str
            Name of the route file
        route_name : str
            Name of the route
        description : str
            Description of the route (optional)
        external_id : str | None
            External identifier for the route (optional)
        provider_updated_at : str | None
            ISO timestamp of when route was updated by provider (optional)
        workout_type_family_id : int
            Workout type family ID (default: 0)
        start_lat : float | None
            Starting latitude (optional)
        start_lng : float | None
            Starting longitude (optional)
        distance : float | None
            Total distance in meters (optional)
        ascent : float | None
            Ascent in meters (optional)
        descent : float | None
            Descent in meters (optional)

        Returns
        -------
        dict[str, Any]
            Response from Wahoo API containing the uploaded route information
        """
        # Try to create the route first
        try:
            return self.create_route(
                route_file=route_file,
                filename=filename,
                route_name=route_name,
                description=description,
                external_id=external_id,
                provider_updated_at=provider_updated_at,
                workout_type_family_id=workout_type_family_id,
                start_lat=start_lat,
                start_lng=start_lng,
                distance=distance,
                ascent=ascent,
                descent=descent,
            )
        except ValueError as e:
            error_msg = str(e)
            # If route already exists, we need to find it and update it
            if "already exists" in error_msg:
                # Extract route ID from error message if possible
                # Error format: "A route with an external_id of "
                # "gravly_route_7 already exists"
                # We need to find the route by external_id and get its ID
                # For now, we'll catch the exception and handle it in the
                # service layer
                raise ValueError(
                    f"Route with external_id {external_id} already exists. "
                    f"Update not implemented yet."
                )
            else:
                raise e
