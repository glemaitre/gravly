"""Wahoo API service using the custom wahoo client library.

This service provides methods to interact with the Wahoo API for
authenticating users, retrieving activities, getting route data,
and accessing user information.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ...utils.config import WahooConfig
from .client import Client
from .exceptions import WahooAccessUnauthorized

logger = logging.getLogger(__name__)


class WahooService:
    """Wahoo API service using the custom wahoo client library.

    This service provides methods to interact with the Wahoo API for
    authenticating users, retrieving activities, getting route data,
    and accessing user information.

    Attributes
    ----------
    client_id : str
        Wahoo application client ID.
    client_secret : str
        Wahoo application client secret.
    client : wahoo.Client
        The wahoo Client instance for API interactions.
    tokens_file : Path
        Path to the file where authentication tokens are stored.

    Notes
    -----
    This service handles OAuth authentication flow, token management,
    and provides convenient methods for accessing Wahoo data. All
    methods that require authentication will automatically handle
    token refresh if needed.
    """

    def __init__(self, wahoo_config: WahooConfig):
        """Initialize the Wahoo service.

        Parameters
        ----------
        wahoo_config : WahooConfig
            Wahoo configuration containing client credentials and token file
            path.

        Notes
        -----
        This method initializes the Wahoo API client and sets up the token file
        path for storing authentication tokens securely.
        """
        # Use client_id as string as required by wahoo client
        self.client_id = wahoo_config.client_id
        self.client_secret = wahoo_config.client_secret
        self.callback_url = wahoo_config.callback_url
        self.scopes = wahoo_config.scopes

        self.client = Client()
        self.tokens_file = Path(wahoo_config.tokens_file_path)

    def _load_tokens(self) -> dict[str, Any] | None:
        """Load Wahoo authentication tokens from the configured file.

        Returns
        -------
        dict[str, Any] | None
            Dictionary containing access_token, refresh_token, and expires_at,
            or None if the file doesn't exist or cannot be read.

        Notes
        -----
        This method attempts to load tokens from the file specified in the
        configuration. If the file doesn't exist or contains invalid JSON,
        it returns None and logs the error.
        """
        if not self.tokens_file.exists():
            return None

        try:
            with open(self.tokens_file) as f:
                tokens = json.load(f)
            logger.info("Loaded Wahoo tokens from file")
            return tokens
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            return None

    def _save_tokens(self, tokens: dict[str, Any]) -> None:
        """Save Wahoo authentication tokens to the configured file.

        Parameters
        ----------
        tokens : dict[str, Any]
            Dictionary containing access_token, refresh_token, expires_at,
            and any other token-related data.

        Raises
        ------
        Exception
            If the file cannot be written or the directory cannot be created.

        Notes
        -----
        This method creates the parent directory if it doesn't exist and
        converts any datetime objects to ISO format strings for JSON
        serialization. The tokens are saved as JSON format.
        """
        try:
            self.tokens_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert any datetime objects to ISO format strings for JSON serialization
            def convert_datetime(obj):
                if hasattr(obj, "isoformat"):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime(item) for item in obj]
                return obj

            tokens_serializable = convert_datetime(tokens)

            with open(self.tokens_file, "w") as f:
                json.dump(tokens_serializable, f, indent=2)
            logger.info("Saved Wahoo tokens to file")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")

    def get_authorization_url(self, state: str = "wahoo_auth") -> str:
        """Generate Wahoo OAuth authorization URL.

        Parameters
        ----------
        state : str, default="wahoo_auth"
            Optional state parameter for tracking the request and preventing
            CSRF attacks.

        Returns
        -------
        str
            The complete authorization URL that users should visit to authorize
            the application.

        Notes
        -----
        This method generates the URL that users need to visit to authorize
        your application to access their Wahoo data. The URL includes the
        necessary OAuth parameters and scopes. The redirect URI is taken from
        the configuration.
        """
        auth_url = self.client.authorization_url(
            client_id=self.client_id,
            redirect_uri=self.callback_url,
            scope=self.scopes,
            state=state,
        )
        logger.info(f"Generated Wahoo authorization URL with state: {state}")
        return auth_url

    def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access token.

        Parameters
        ----------
        code : str
            The authorization code received from Wahoo after user
            authorization. This code is obtained from the OAuth callback URL.

        Returns
        -------
        dict[str, Any]
            Dictionary containing access_token, refresh_token, expires_at,
            user information, and other token-related data.

        Raises
        ------
        Exception
            If the token exchange fails or the code is invalid.

        Notes
        -----
        This method exchanges the authorization code for an access token and
        refresh token.
        """
        try:
            access_info = self.client.exchange_code_for_token(
                client_id=self.client_id,
                client_secret=self.client_secret,
                code=code,
                redirect_uri=self.callback_url,
            )

            # Convert AccessInfo to dictionary for saving and returning
            token_dict = {
                "access_token": access_info["access_token"],
                "refresh_token": access_info["refresh_token"],
                "expires_at": access_info["expires_at"],
            }

            # Save tokens
            self._save_tokens(token_dict)

            logger.info("Successfully exchanged code for token")
            return token_dict

        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise

    def refresh_access_token(self) -> bool:
        """Refresh the access token using the stored refresh token.

        Returns
        -------
        bool
            True if the refresh was successful, False otherwise.

        Notes
        -----
        This method attempts to refresh the access token using the stored
        refresh token. If successful, it updates the stored tokens with
        the new access token and refresh token. If the refresh fails,
        the user will need to re-authorize the application.
        """
        tokens = self._load_tokens()
        if not tokens or "refresh_token" not in tokens:
            logger.error("No refresh token available")
            return False

        try:
            refresh_response = self.client.refresh_access_token(
                client_id=self.client_id,
                client_secret=self.client_secret,
                refresh_token=tokens["refresh_token"],
            )

            # Save new tokens
            self._save_tokens(refresh_response)

            logger.info("Successfully refreshed access token")
            return True

        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            return False

    def _ensure_authenticated(self) -> None:
        """Ensure the client is authenticated with valid tokens.

        Raises
        ------
        WahooAccessUnauthorized
            If no tokens are available or authentication fails.

        Notes
        -----
        This method checks if valid authentication tokens are available.
        If the access token is expired, it attempts to refresh it using
        the refresh token. If authentication fails, it raises a
        WahooAccessUnauthorized exception.
        """
        tokens = self._load_tokens()
        if not tokens:
            raise WahooAccessUnauthorized(
                "No tokens available. Please authenticate first."
            )

        if "access_token" not in tokens:
            raise WahooAccessUnauthorized(
                "No access token available. Please authenticate first."
            )

        # Check if token is expired and try to refresh
        if "expires_at" in tokens:
            expires_at = datetime.fromtimestamp(tokens["expires_at"])
            if datetime.now() >= expires_at:
                logger.info("Access token expired, attempting refresh")
                if not self.refresh_access_token():
                    raise WahooAccessUnauthorized("Token expired and refresh failed")
                tokens = self._load_tokens()

        # Set the access token on the client
        self.client.access_token = tokens["access_token"]

    def deauthorize(self) -> None:
        """Deauthorize the application.

        This causes the application to be removed from the user's
        authorized applications.

        Raises
        ------
        WahooAccessUnauthorized
            If the user is not authenticated or tokens are invalid.
        Exception
            If there's an error deauthorizing the application.

        Notes
        -----
        This method revokes the current access token and removes the
        application from the user's authorized applications list.
        """
        self._ensure_authenticated()

        try:
            self.client.deauthorize()
            logger.info("Successfully deauthorized application")
        except ValueError as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                logger.error(f"Wahoo API access unauthorized: {e}")
                raise WahooAccessUnauthorized(error_msg)
            else:
                logger.error(f"Failed to deauthorize: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to deauthorize: {e}")
            raise

    def get_user(self) -> dict[str, Any]:
        """Get authenticated user information.

        Returns
        -------
        dict[str, Any]
            Dictionary containing user information

        Raises
        ------
        WahooAccessUnauthorized
            If the user is not authenticated or tokens are invalid.
        Exception
            If there's an error getting user information.
        """
        self._ensure_authenticated()

        try:
            logger.info("Getting user information from Wahoo")
            result = self.client.get_user()
            logger.info("Successfully retrieved user information")
            return result
        except ValueError as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                logger.error(f"Wahoo API access unauthorized: {e}")
                raise WahooAccessUnauthorized(error_msg)
            else:
                logger.error(f"Failed to get user: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            raise

    def get_route(self, route_id: int) -> dict[str, Any]:
        """Get a route by ID from Wahoo Cloud.

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
        WahooAccessUnauthorized
            If the user is not authenticated or tokens are invalid.
        Exception
            If there's an error getting the route.
        """
        self._ensure_authenticated()

        try:
            logger.info(f"Getting route {route_id} from Wahoo Cloud")
            result = self.client.get_route(route_id=route_id)
            logger.info(f"Successfully retrieved route {route_id}")
            return result
        except ValueError as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                logger.error(f"Wahoo API access unauthorized: {e}")
                raise WahooAccessUnauthorized(error_msg)
            else:
                logger.error(f"Failed to get route: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to get route: {e}")
            raise

    def get_routes(self) -> list[dict[str, Any]]:
        """Get all routes from Wahoo Cloud.

        Returns
        -------
        list[dict[str, Any]]
            List of routes from Wahoo API

        Raises
        ------
        WahooAccessUnauthorized
            If the user is not authenticated or tokens are invalid.
        Exception
            If there's an error getting the routes.
        """
        self._ensure_authenticated()

        try:
            logger.info("Getting all routes from Wahoo Cloud")
            result = self.client.get_routes()
            logger.info(f"Successfully retrieved {len(result)} routes")
            return result
        except ValueError as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                logger.error(f"Wahoo API access unauthorized: {e}")
                raise WahooAccessUnauthorized(error_msg)
            else:
                logger.error(f"Failed to get routes: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to get routes: {e}")
            raise

    def create_route(
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
        """Create a new route in Wahoo Cloud.

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
            Response from Wahoo API containing the created route information

        Raises
        ------
        WahooAccessUnauthorized
            If the user is not authenticated or tokens are invalid.
        Exception
            If there's an error creating the route.
        """
        self._ensure_authenticated()

        try:
            logger.info(f"Creating route '{route_name}' in Wahoo Cloud")
            result = self.client.create_route(
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
            logger.info(f"Successfully created route '{route_name}'")
            return result
        except ValueError as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                logger.error(f"Wahoo API access unauthorized: {e}")
                raise WahooAccessUnauthorized(error_msg)
            else:
                logger.error(f"Failed to create route: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to create route: {e}")
            raise

    def update_route(
        self,
        route_id: int,
        route_file: str,
        filename: str,
        route_name: str,
        description: str = "",
        provider_updated_at: str | None = None,
        workout_type_family_id: int = 0,
        start_lat: float | None = None,
        start_lng: float | None = None,
        distance: float | None = None,
        ascent: float | None = None,
        descent: float | None = None,
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
        description : str
            Description of the route (optional)
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
            Response from Wahoo API containing the updated route information

        Raises
        ------
        WahooAccessUnauthorized
            If the user is not authenticated or tokens are invalid.
        Exception
            If there's an error updating the route.
        """
        self._ensure_authenticated()

        try:
            logger.info(f"Updating route {route_id} '{route_name}' in Wahoo Cloud")
            result = self.client.update_route(
                route_id=route_id,
                route_file=route_file,
                filename=filename,
                route_name=route_name,
                description=description,
                provider_updated_at=provider_updated_at,
                workout_type_family_id=workout_type_family_id,
                start_lat=start_lat,
                start_lng=start_lng,
                distance=distance,
                ascent=ascent,
                descent=descent,
            )
            logger.info(f"Successfully updated route {route_id} '{route_name}'")
            return result
        except ValueError as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                logger.error(f"Wahoo API access unauthorized: {e}")
                raise WahooAccessUnauthorized(error_msg)
            else:
                logger.error(f"Failed to update route: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to update route: {e}")
            raise

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
        ascent : float | None
            Ascent in meters (optional)
        descent : float | None
            Descent in meters (optional)

        Returns
        -------
        dict[str, Any]
            Response from Wahoo API containing the uploaded route information

        Raises
        ------
        WahooAccessUnauthorized
            If the user is not authenticated or tokens are invalid.
        Exception
            If there's an error uploading the route.
        """
        self._ensure_authenticated()

        try:
            logger.info(f"Uploading route '{route_name}' to Wahoo Cloud")
            # Try to create the route
            result = self.create_route(
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
            logger.info(f"Successfully uploaded route '{route_name}'")
            return result
        except ValueError as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                logger.error(f"Wahoo API access unauthorized: {e}")
                raise WahooAccessUnauthorized(error_msg)
            elif "already exists" in error_msg:
                # Route already exists - for now just log and re-raise
                # In the future, we could implement update logic here
                logger.warning(
                    f"Route with external_id '{external_id}' already exists: {e}"
                )
                raise ValueError("Route already exists. Update not implemented yet.")
            else:
                logger.error(f"Failed to upload route: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to upload route: {e}")
            raise
