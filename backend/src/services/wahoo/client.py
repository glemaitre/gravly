"""Client for interacting with the Wahoo API."""

import logging
from datetime import datetime
from typing import Literal

from requests import Session

from .protocol import ApiV1, AccessInfo, Scope
from .limiter import RateLimiter, DefaultRateLimiter

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
            The token that provides access to a specific Strava account. If
            empty, assume that this account is not yet authenticated.
        rate_limit_requests : bool
            Whether to apply a rate limiter to the requests. (default True)
        rate_limiter : callable
            A :class:`stravalib.util.limiter.RateLimiter` object to use.
            If not specified (and rate_limit_requests is True), then
            :class:`stravalib.util.limiter.DefaultRateLimiter` will be used.
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
                "Cannot specify rate_limiter object when rate_limit_requests is"
                " False"
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
        client_id: int,
        redirect_uri: str,
        approval_prompt: Literal["auto", "force"] = "auto",
        scope: list[Scope] | Scope | None = None,
        state: str | None = None,
    ) -> str:
        """Get the URL needed to authorize your application to access a Strava
        user's information.

        See https://developers.strava.com/docs/authentication/

        Parameters
        ----------
        client_id : int
            The numeric developer client id.
        redirect_uri : str
            The URL that Strava will redirect to after successful (or failed)
            authorization.
        approval_prompt : str, default='auto'
            Whether to prompt for approval even if approval already granted to
            app.
            Choices are 'auto' or 'force'.
        scope : list[str], default = None
            The access scope required.  Omit to imply "read" and "activity:read"
            Valid values are 'read', 'read_all', 'profile:read_all',
            'profile:write', 'activity:read', 'activity:read_all',
            'activity:write'.
        state : str, default=None
            An arbitrary variable that will be returned to your application in
            the redirect URI.

        Returns
        -------
        str:
            A string containing the url required to authorize with the Strava
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
        client_id: int,
        client_secret: str,
        code: str,
    ) -> AccessInfo:
        """Exchange the temporary authorization code (returned with redirect
        from Strava authorization URL) for a short-lived access token and a
        refresh token (used to obtain the next access token later on).

        Parameters
        ----------
        client_id : int
            The numeric developer client id.
        client_secret : str
            The developer client secret
        code : str
            The temporary authorization code
        return_athlete : bool (default = False)
            Whether to return a SummaryAthlete object (or not)
            This parameter is currently undocumented and could change
            at any time.

        Returns
        -------
        AccessInfo
            TypedDictionary containing the access_token, refresh_token and
            expires_at (number of seconds since Epoch when the provided access
            token will expire)

        Notes
        -----
        Strava by default returns `SummaryAthlete` information during
        this exchange. However this return is currently undocumented
        and could change at any time.
        """
        access_info, athlete_data = self.protocol.exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            code=code,
        )

        return access_info

    def refresh_access_token(
        self, client_id: int, client_secret: str, refresh_token: str
    ) -> AccessInfo:
        """Exchanges the previous refresh token for a short-lived access token
        and a new refresh token (used to obtain the next access token later on).

        Parameters
        ----------
        client_id : int
            The numeric developer client id.
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
        self.protocol.post("oauth/deauthorize")
