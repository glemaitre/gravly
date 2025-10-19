"""Custom exceptions for Wahoo API service."""


class WahooAccessUnauthorized(Exception):
    """Raised when Wahoo API access is unauthorized."""

    pass


class WahooRateLimitExceeded(Exception):
    """Raised when Wahoo API rate limit is exceeded."""

    pass
