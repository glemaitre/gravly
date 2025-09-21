"""Strava API service using the official stravalib library."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from stravalib import Client
from stravalib.exc import AccessUnauthorized, RateLimitExceeded

from ..utils.config import StravaConfig

logger = logging.getLogger(__name__)


class StravaService:
    """Strava API service using the official stravalib library.

    This service provides methods to interact with the Strava API for
    authenticating users, retrieving activities, getting GPX data,
    and accessing athlete information.

    Attributes
    ----------
    client_id : int
        Strava application client ID.
    client_secret : str
        Strava application client secret.
    client : stravalib.Client
        The stravalib Client instance for API interactions.
    tokens_file : Path
        Path to the file where authentication tokens are stored.

    Notes
    -----
    This service handles OAuth authentication flow, token management,
    and provides convenient methods for accessing Strava data. All
    methods that require authentication will automatically handle
    token refresh if needed.
    """

    def __init__(self, strava_config: StravaConfig):
        """Initialize the Strava service.

        Parameters
        ----------
        strava_config : StravaConfig
            Strava configuration containing client credentials and token file
            path.

        Notes
        -----
        This method initializes the Strava API client and sets up the token file
        path for storing authentication tokens securely.
        """
        # Convert client_id to int as required by stravalib
        self.client_id = int(strava_config.client_id)
        self.client_secret = strava_config.client_secret

        self.client = Client()
        self.tokens_file = Path(strava_config.tokens_file_path)

    def _load_tokens(self) -> dict[str, Any] | None:
        """Load Strava authentication tokens from the configured file.

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
            logger.info("Loaded Strava tokens from file")
            return tokens
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            return None

    def _save_tokens(self, tokens: dict[str, Any]) -> None:
        """Save Strava authentication tokens to the configured file.

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
            logger.info("Saved Strava tokens to file")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")

    def get_authorization_url(
        self, redirect_uri: str, state: str = "strava_auth"
    ) -> str:
        """Generate Strava OAuth authorization URL.

        Parameters
        ----------
        redirect_uri : str
            The redirect URI for OAuth callback. This should match the URI
            configured in your Strava application settings.
        state : str, default="strava_auth"
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
        your application to access their Strava data. The URL includes the
        necessary OAuth parameters and scopes.
        """
        # Convert client_id to int as required by stravalib

        auth_url = self.client.authorization_url(
            client_id=self.client_id,
            redirect_uri=redirect_uri,
            scope=["activity:read_all"],
            state=state,
        )
        logger.info(f"Generated Strava authorization URL with state: {state}")
        return auth_url

    def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access token.

        Parameters
        ----------
        code : str
            The authorization code received from Strava after user
            authorization. This code is obtained from the OAuth callback URL.

        Returns
        -------
        dict[str, Any]
            Dictionary containing access_token, refresh_token, expires_at,
            athlete information, and other token-related data.

        Raises
        ------
        Exception
            If the token exchange fails or the code is invalid.

        Notes
        -----
        This method exchanges the authorization code for an access token and
        refresh token. It also fetches the athlete information and saves
        all tokens to the configured file for future use.
        """
        try:
            token_response = self.client.exchange_code_for_token(
                client_id=self.client_id,
                client_secret=self.client_secret,
                code=code,
                return_athlete=True,  # Get athlete info too
            )

            # Extract AccessInfo and athlete from response
            if isinstance(token_response, tuple):
                access_info, athlete = token_response
            else:
                access_info = token_response
                athlete = None

            # Convert AccessInfo to dictionary for saving and returning
            token_dict = {
                "access_token": access_info["access_token"],
                "refresh_token": access_info["refresh_token"],
                "expires_at": access_info["expires_at"],
                "athlete": athlete.model_dump() if athlete else None,
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
        AccessUnauthorized
            If no tokens are available or authentication fails.

        Notes
        -----
        This method checks if valid authentication tokens are available.
        If the access token is expired, it attempts to refresh it using
        the refresh token. If authentication fails, it raises an
        AccessUnauthorized exception.
        """
        tokens = self._load_tokens()
        if not tokens:
            raise AccessUnauthorized("No tokens available. Please authenticate first.")

        if "access_token" not in tokens:
            raise AccessUnauthorized(
                "No access token available. Please authenticate first."
            )

        # Check if token is expired and try to refresh
        if "expires_at" in tokens:
            expires_at = datetime.fromtimestamp(tokens["expires_at"])
            if datetime.now() >= expires_at:
                logger.info("Access token expired, attempting refresh")
                if not self.refresh_access_token():
                    raise AccessUnauthorized("Token expired and refresh failed")
                tokens = self._load_tokens()

        # Set the access token on the client
        self.client.access_token = tokens["access_token"]

    def get_activities(self, page: int = 1, per_page: int = 30) -> list[dict[str, Any]]:
        """Get athlete activities from Strava with proper pagination.

        Parameters
        ----------
        page : int, default=1
            Page number for pagination (1-based).
        per_page : int, default=30
            Number of activities to retrieve per request.

        Returns
        -------
        list[dict[str, Any]]
            List of activity dictionaries containing activity data such as
            name, type, distance, duration, start_date, etc.

        Raises
        ------
        AccessUnauthorized
            If authentication fails or tokens are invalid.
        Exception
            If the API request fails for any other reason.

        Notes
        -----
        This method retrieves the athlete's activities from Strava using cursor-based
        pagination. For page > 1, it calculates the appropriate offset by fetching
        all previous pages and using the last activity's date as the 'before' parameter.
        """
        try:
            self._ensure_authenticated()

            activities = []
            limit = per_page

            if page == 1:
                # First page: get the most recent activities
                for activity in self.client.get_activities(limit=limit):
                    activity_dict = self._convert_activity_to_dict(activity)
                    activities.append(activity_dict)
            else:
                # For subsequent pages, we need to calculate the offset
                # by fetching all previous pages to get the 'before' date
                offset = (page - 1) * per_page

                # Get all activities up to the current page to find the 'before' date
                all_activities = []
                for activity in self.client.get_activities(limit=offset + per_page):
                    activity_dict = self._convert_activity_to_dict(activity)
                    all_activities.append(activity_dict)

                # Return only the activities for the current page
                activities = all_activities[offset : offset + per_page]

            logger.info(
                f"Retrieved {len(activities)} activities from Strava (page {page})"
            )
            return activities

        except RateLimitExceeded as e:
            logger.error(f"Strava API rate limit exceeded: {e}")
            raise
        except AccessUnauthorized as e:
            logger.error(f"Strava API access unauthorized: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get activities: {e}")
            raise

    def _convert_activity_to_dict(self, activity) -> dict[str, Any]:
        """Convert stravalib activity object to dictionary.

        Parameters
        ----------
        activity : stravalib.Activity
            The stravalib Activity object to convert.

        Returns
        -------
        dict[str, Any]
            Dictionary containing activity data with keys like id, name,
            distance, moving_time, elapsed_time, total_elevation_gain,
            type, start_date, and other activity properties.

        Notes
        -----
        This method converts the stravalib Activity object to a plain
        dictionary format that can be easily serialized to JSON or
        used in other parts of the application.
        """
        return {
            "id": str(activity.id),
            "name": activity.name,
            "distance": float(activity.distance) if activity.distance else 0.0,
            "moving_time": (
                activity.moving_time.timedelta().total_seconds()
                if activity.moving_time
                else 0
            ),
            "elapsed_time": (
                activity.elapsed_time.timedelta().total_seconds()
                if activity.elapsed_time
                else 0
            ),
            "total_elevation_gain": (
                float(activity.total_elevation_gain)
                if activity.total_elevation_gain
                else 0.0
            ),
            "type": activity.type,
            "start_date": (
                activity.start_date.isoformat() if activity.start_date else None
            ),
            "start_date_local": (
                activity.start_date_local.isoformat()
                if activity.start_date_local
                else None
            ),
            "timezone": activity.timezone,
            "start_latlng": (
                list(activity.start_latlng.root) if activity.start_latlng else None
            ),
            "end_latlng": (
                list(activity.end_latlng.root) if activity.end_latlng else None
            ),
            "map": (
                {
                    "id": activity.map.id if activity.map else None,
                    "summary_polyline": (
                        activity.map.summary_polyline
                        if activity.map and activity.map.summary_polyline
                        else None
                    ),
                    "resource_state": 2,  # Default resource state for summary maps
                }
                if activity.map
                else None
            ),
            "has_heartrate": activity.has_heartrate,
            "average_heartrate": (
                float(activity.average_heartrate)
                if activity.average_heartrate
                else None
            ),
            "max_heartrate": (
                float(activity.max_heartrate) if activity.max_heartrate else None
            ),
            "has_kudoed": activity.has_kudoed,
            "kudos_count": activity.kudos_count,
            "comment_count": activity.comment_count,
            "athlete_count": activity.athlete_count,
            "trainer": activity.trainer,
            "commute": activity.commute,
            "manual": activity.manual,
            "private": activity.private,
            "visibility": activity.visibility,
            "flagged": activity.flagged,
            "gear_id": activity.gear_id,
            "external_id": activity.external_id,
            "upload_id": activity.upload_id,
            "average_speed": (
                float(activity.average_speed) if activity.average_speed else None
            ),
            "max_speed": float(activity.max_speed) if activity.max_speed else None,
            "hide_from_home": activity.hide_from_home,
            "from_accepted_tag": activity.from_accepted_tag,
            "average_watts": (
                float(activity.average_watts) if activity.average_watts else None
            ),
            "weighted_average_watts": (
                float(activity.weighted_average_watts)
                if activity.weighted_average_watts
                else None
            ),
            "kilojoules": (float(activity.kilojoules) if activity.kilojoules else None),
            "device_watts": activity.device_watts,
            "elev_high": float(activity.elev_high) if activity.elev_high else None,
            "elev_low": float(activity.elev_low) if activity.elev_low else None,
            "pr_count": activity.pr_count,
            "total_photo_count": activity.total_photo_count,
            "suffer_score": activity.suffer_score,
        }

    def get_activity_gpx(self, activity_id: str) -> str | None:
        """Get GPX data for a specific activity.

        Parameters
        ----------
        activity_id : str
            The Strava activity ID as a string.

        Returns
        -------
        str | None
            GPX data as XML string, or None if the activity doesn't have
            GPS data or if the request fails.

        Raises
        ------
        AccessUnauthorized
            If authentication fails or tokens are invalid.
        Exception
            If the API request fails for any other reason.

        Notes
        -----
        This method retrieves the GPS track data for a specific activity
        and constructs GPX format data from the Strava streams API.
        The GPX data includes time, position, distance, and altitude information.
        """
        try:
            self._ensure_authenticated()

            # Get activity details
            activity = self.client.get_activity(int(activity_id))

            # Get streams data
            streams = self.client.get_activity_streams(
                int(activity_id), types=["time", "latlng", "distance", "altitude"]
            )

            # Construct GPX from streams
            gpx_string = self._construct_gpx_from_streams(activity, streams)

            if gpx_string:
                logger.info(f"Retrieved GPX data for activity {activity_id}")
                return gpx_string
            else:
                logger.warning(f"No GPX data available for activity {activity_id}")
                return None

        except RateLimitExceeded as e:
            logger.error(f"Strava API rate limit exceeded: {e}")
            raise
        except AccessUnauthorized as e:
            logger.error(f"Strava API access unauthorized: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get GPX for activity {activity_id}: {e}")
            raise

    def _construct_gpx_from_streams(self, activity, streams) -> str | None:
        """Construct GPX XML from activity streams.

        Parameters
        ----------
        activity : stravalib.Activity
            The Strava activity object containing activity metadata.
        streams : dict
            Dictionary containing stream data from Strava API with keys
            like 'latlng', 'altitude', 'time', etc.

        Returns
        -------
        str | None
            GPX XML string, or None if no valid GPS data is available.

        Notes
        -----
        This method constructs a valid GPX 1.1 XML format from Strava
        stream data. It requires latlng stream data to be present.
        The resulting GPX includes track points with latitude, longitude,
        elevation, and time information.
        """
        try:
            # Extract stream data
            latlng_stream = streams.get("latlng")
            altitude_stream = streams.get("altitude")
            time_stream = streams.get("time")
            # distance_stream = streams.get('distance')

            if not latlng_stream:
                logger.warning("No latlng stream available")
                return None

            # Get activity details
            activity_name = activity.name or "Strava Activity"
            start_date = activity.start_date

            # Construct GPX
            gpx_header = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Strava" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd
                         http://www.garmin.com/xmlschemas/GpxExtensions/v3
                         http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd
                         http://www.garmin.com/xmlschemas/TrackPointExtension/v1
                         http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd"
     xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
     xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3">
  <metadata>
    <name>{name}</name>
    <time>{start_time}</time>
  </metadata>
  <trk>
    <name>{name}</name>
    <trkseg>"""

            gpx_footer = """
    </trkseg>
  </trk>
</gpx>"""

            # Format start time
            start_time_str = start_date.isoformat() if start_date else ""

            # Build track points
            track_points = []
            latlng_data = latlng_stream.data
            altitude_data = altitude_stream.data if altitude_stream else None
            time_data = time_stream.data if time_stream else None

            for i, (lat, lon) in enumerate(latlng_data):
                # Calculate timestamp
                if time_data and i < len(time_data):
                    point_time = start_date.timestamp() + time_data[i]
                    time_str = datetime.fromtimestamp(point_time).isoformat()
                else:
                    time_str = ""

                # Get elevation
                elevation = ""
                if altitude_data and i < len(altitude_data):
                    elevation = f"<ele>{altitude_data[i]}</ele>"

                # Build track point
                trkpt = f'      <trkpt lat="{lat}" lon="{lon}">{elevation}'
                if time_str:
                    trkpt += f"<time>{time_str}</time>"
                trkpt += "</trkpt>"

                track_points.append(trkpt)

            # Combine all parts
            gpx_content = gpx_header.format(
                name=activity_name, start_time=start_time_str
            )
            gpx_content += "\n".join(track_points)
            gpx_content += gpx_footer

            return gpx_content

        except Exception as e:
            logger.error(f"Failed to construct GPX from streams: {e}")
            return None

    def get_athlete(self) -> dict[str, Any]:
        """Get current athlete information from Strava.

        Returns
        -------
        dict[str, Any]
            Dictionary containing athlete information including id, username,
            firstname, lastname, bio, city, state, country, sex, premium
            status, and other athlete profile data.

        Raises
        ------
        AccessUnauthorized
            If authentication fails or tokens are invalid.
        Exception
            If the API request fails for any other reason.

        Notes
        -----
        This method retrieves the current authenticated athlete's profile
        information from Strava. The returned data includes personal
        information and account status.
        """
        try:
            self._ensure_authenticated()

            athlete = self.client.get_athlete()

            athlete_dict = {
                "id": str(athlete.id),
                "username": athlete.username,
                "resource_state": athlete.resource_state,
                "firstname": athlete.firstname,
                "lastname": athlete.lastname,
                "bio": athlete.bio,
                "city": athlete.city,
                "state": athlete.state,
                "country": athlete.country,
                "sex": athlete.sex,
                "premium": athlete.premium,
                "summit": athlete.summit,
                "created_at": (
                    athlete.created_at.isoformat() if athlete.created_at else None
                ),
                "updated_at": (
                    athlete.updated_at.isoformat() if athlete.updated_at else None
                ),
                "badge_type_id": athlete.badge_type_id,
                "weight": float(athlete.weight) if athlete.weight else None,
                "profile_medium": athlete.profile_medium,
                "profile": athlete.profile,
                "friend": athlete.friend,
                "follower": athlete.follower,
                "blocked": athlete.blocked,
                "can_follow": athlete.can_follow,
                "follower_count": athlete.follower_count,
                "friend_count": athlete.friend_count,
                "mutual_friend_count": athlete.mutual_friend_count,
                "athlete_type": athlete.athlete_type,
                "date_preference": athlete.date_preference,
                "measurement_preference": athlete.measurement_preference,
                "clubs": (
                    [{"id": str(club.id), "name": club.name} for club in athlete.clubs]
                    if athlete.clubs
                    else []
                ),
                "ftp": athlete.ftp,
                "max_heartrate": (
                    float(athlete.max_heartrate) if athlete.max_heartrate else None
                ),
                "max_watts": float(athlete.max_watts) if athlete.max_watts else None,
                "max_speed": float(athlete.max_speed) if athlete.max_speed else None,
                "default_bikes": athlete.default_bikes,
                "default_shoes": athlete.default_shoes,
                "default_gear": athlete.default_gear,
                "offline_token": athlete.offline_token,
                "email": athlete.email,
            }

            firstname = athlete_dict.get("firstname", "Unknown")
            logger.info(f"Retrieved athlete information for {firstname}")
            return athlete_dict

        except RateLimitExceeded as e:
            logger.error(f"Strava API rate limit exceeded: {e}")
            raise
        except AccessUnauthorized as e:
            logger.error(f"Strava API access unauthorized: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get athlete: {e}")
            raise
