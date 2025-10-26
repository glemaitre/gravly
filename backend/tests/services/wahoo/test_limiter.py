"""Unit tests for Wahoo rate limiter."""

from unittest.mock import Mock, patch

import pytest

from backend.src.services.wahoo.limiter import (
    DefaultRateLimiter,
    RateLimiter,
    RequestRate,
    SleepingRateLimitRule,
    get_rates_from_response_headers,
    get_seconds_until_next_day,
    get_seconds_until_next_quarter,
)


class TestRequestRate:
    """Test RequestRate class."""

    def test_request_rate_creation(self):
        """Test creating a RequestRate instance."""
        rate = RequestRate(
            short_usage=10,
            middle_usage=100,
            long_usage=1000,
            short_limit=15,
            middle_limit=200,
            long_limit=2000,
        )

        assert rate.short_usage == 10
        assert rate.middle_usage == 100
        assert rate.long_usage == 1000
        assert rate.short_limit == 15
        assert rate.middle_limit == 200
        assert rate.long_limit == 2000


class TestGetRatesFromResponseHeaders:
    """Test get_rates_from_response_headers function."""

    def test_get_rates_from_response_headers_read_rate_limit(self):
        """Test extracting rates from read rate limit headers."""
        headers = {
            "X-ReadRateLimit-Usage": "10,100,1000",
            "X-ReadRateLimit-Limit": "15,200,2000",
        }

        result = get_rates_from_response_headers(headers, "GET")

        assert result is not None
        assert result.short_usage == 10
        assert result.middle_usage == 100
        assert result.long_usage == 1000
        assert result.short_limit == 15
        assert result.middle_limit == 200
        assert result.long_limit == 2000

    def test_get_rates_from_response_headers_generic_rate_limit(self):
        """Test extracting rates from generic rate limit headers."""
        headers = {
            "X-RateLimit-Usage": "5,50,500",
            "X-RateLimit-Limit": "10,100,1000",
        }

        result = get_rates_from_response_headers(headers, "POST")

        assert result is not None
        assert result.short_usage == 5
        assert result.middle_usage == 50
        assert result.long_usage == 500
        assert result.short_limit == 10
        assert result.middle_limit == 100
        assert result.long_limit == 1000

    def test_get_rates_from_response_headers_case_insensitive(self):
        """Test that header keys are case insensitive."""
        headers = {
            "x-readratelimit-usage": "1,2,3",
            "x-readratelimit-limit": "4,5,6",
        }

        result = get_rates_from_response_headers(headers, "GET")

        assert result is not None
        assert result.short_usage == 1
        assert result.middle_usage == 2
        assert result.long_usage == 3
        assert result.short_limit == 4
        assert result.middle_limit == 5
        assert result.long_limit == 6

    def test_get_rates_from_response_headers_no_headers(self):
        """Test when no rate limit headers are present."""
        headers = {"Content-Type": "application/json"}

        result = get_rates_from_response_headers(headers, "GET")

        assert result is None

    def test_get_rates_from_response_headers_missing_usage(self):
        """Test when usage header is missing."""
        headers = {"X-ReadRateLimit-Limit": "15,200,2000"}

        result = get_rates_from_response_headers(headers, "GET")

        assert result is None

    def test_get_rates_from_response_headers_missing_limit(self):
        """Test when limit header is missing."""
        headers = {"X-ReadRateLimit-Usage": "10,100,1000"}

        # This will raise a KeyError because the function doesn't handle missing limit
        with pytest.raises(KeyError):
            get_rates_from_response_headers(headers, "GET")

    def test_get_rates_from_response_headers_empty_values(self):
        """Test when rate limit headers have empty values."""
        headers = {
            "X-ReadRateLimit-Usage": "",
            "X-ReadRateLimit-Limit": "",
        }

        # This will raise a ValueError because empty string can't be converted to int
        with pytest.raises(ValueError):
            get_rates_from_response_headers(headers, "GET")


class TestGetSecondsUntilNextQuarter:
    """Test get_seconds_until_next_quarter function."""

    def test_get_seconds_until_next_quarter_with_now(self):
        """Test calculating seconds until next quarter with provided time."""
        with patch("backend.src.services.wahoo.limiter.arrow"):
            mock_now = Mock()
            mock_now.minute = 10  # 10 minutes past the hour
            mock_now.replace.return_value = Mock()
            mock_now.replace.return_value.seconds = 0
            mock_now.__sub__ = Mock(return_value=Mock(seconds=300))  # 5 minutes

            result = get_seconds_until_next_quarter(now=mock_now)

            assert result == 599  # 899 - 300

    def test_get_seconds_until_next_quarter_without_now(self):
        """Test calculating seconds until next quarter without provided time."""
        with patch("backend.src.services.wahoo.limiter.arrow") as mock_arrow:
            mock_utcnow = Mock()
            mock_utcnow.minute = 5
            mock_utcnow.replace.return_value = Mock()
            mock_utcnow.replace.return_value.seconds = 0
            mock_utcnow.__sub__ = Mock(return_value=Mock(seconds=300))
            mock_arrow.utcnow.return_value = mock_utcnow

            result = get_seconds_until_next_quarter()

            assert result == 599
            mock_arrow.utcnow.assert_called_once()


class TestGetSecondsUntilNextDay:
    """Test get_seconds_until_next_day function."""

    def test_get_seconds_until_next_day_with_now(self):
        """Test calculating seconds until next day with provided time."""
        with patch("backend.src.services.wahoo.limiter.arrow"):
            mock_now = Mock()
            mock_ceil = Mock()
            mock_ceil.__sub__ = Mock(return_value=Mock(seconds=3600))  # 1 hour
            mock_now.ceil.return_value = mock_ceil

            result = get_seconds_until_next_day(now=mock_now)

            assert result == 3600
            mock_now.ceil.assert_called_once_with("day")

    def test_get_seconds_until_next_day_without_now(self):
        """Test calculating seconds until next day without provided time."""
        with patch("backend.src.services.wahoo.limiter.arrow") as mock_arrow:
            mock_utcnow = Mock()
            mock_ceil = Mock()
            mock_ceil.__sub__ = Mock(return_value=Mock(seconds=7200))  # 2 hours
            mock_utcnow.ceil.return_value = mock_ceil
            mock_arrow.utcnow.return_value = mock_utcnow

            result = get_seconds_until_next_day()

            assert result == 7200
            mock_arrow.utcnow.assert_called_once()


class TestSleepingRateLimitRule:
    """Test SleepingRateLimitRule class."""

    def test_sleeping_rate_limit_rule_invalid_priority(self):
        """Test that invalid priority raises ValueError."""
        with pytest.raises(ValueError, match='Invalid priority "invalid"'):
            SleepingRateLimitRule(priority="invalid")

    def test_sleeping_rate_limit_rule_valid_priorities(self):
        """Test that valid priorities work."""
        for priority in ["low", "medium", "high"]:
            rule = SleepingRateLimitRule(priority=priority)
            assert rule.priority == priority

    def test_get_wait_time_long_limit_exceeded(self):
        """Test wait time when long limit is exceeded."""
        rule = SleepingRateLimitRule(priority="low")
        rates = RequestRate(
            short_usage=5,
            middle_usage=50,
            long_usage=1000,
            short_limit=10,
            middle_limit=100,
            long_limit=1000,  # At limit
        )

        with patch.object(rule, "log") as mock_log:
            result = rule._get_wait_time(rates, 300, 3600)

            assert result == 3600  # seconds_until_long_limit
            mock_log.warning.assert_called_once_with(
                "Long term API rate limit exceeded"
            )

    def test_get_wait_time_short_limit_exceeded(self):
        """Test wait time when short limit is exceeded."""
        rule = SleepingRateLimitRule(priority="medium")
        rates = RequestRate(
            short_usage=10,  # At limit
            middle_usage=50,
            long_usage=500,
            short_limit=10,
            middle_limit=100,
            long_limit=1000,
        )

        with patch.object(rule, "log") as mock_log:
            result = rule._get_wait_time(rates, 300, 3600)

            assert result == 300  # seconds_until_short_limit
            mock_log.warning.assert_called_once_with(
                "Short term API rate limit exceeded"
            )

    def test_get_wait_time_high_priority(self):
        """Test wait time with high priority (no wait)."""
        rule = SleepingRateLimitRule(priority="high")
        rates = RequestRate(
            short_usage=5,
            middle_usage=50,
            long_usage=500,
            short_limit=10,
            middle_limit=100,
            long_limit=1000,
        )

        result = rule._get_wait_time(rates, 300, 3600)

        assert result == 0

    def test_get_wait_time_medium_priority(self):
        """Test wait time with medium priority."""
        rule = SleepingRateLimitRule(priority="medium")
        rates = RequestRate(
            short_usage=5,
            middle_usage=50,
            long_usage=500,
            short_limit=10,
            middle_limit=100,
            long_limit=1000,
        )

        result = rule._get_wait_time(rates, 300, 3600)

        # Should be seconds_until_short_limit / (short_limit - short_usage)
        # 300 / (10 - 5) = 60
        assert result == 60.0

    def test_get_wait_time_low_priority(self):
        """Test wait time with low priority."""
        rule = SleepingRateLimitRule(priority="low")
        rates = RequestRate(
            short_usage=5,
            middle_usage=50,
            long_usage=500,
            short_limit=10,
            middle_limit=100,
            long_limit=1000,
        )

        result = rule._get_wait_time(rates, 300, 3600)

        # Should be seconds_until_long_limit / (long_limit - long_usage)
        # 3600 / (1000 - 500) = 7.2
        assert result == 7.2

    def test_call_with_rates(self):
        """Test calling the rule with valid rates."""
        rule = SleepingRateLimitRule(priority="high")
        headers = {
            "X-ReadRateLimit-Usage": "5,50,500",
            "X-ReadRateLimit-Limit": "10,100,1000",
        }

        with patch("backend.src.services.wahoo.limiter.time.sleep") as mock_sleep:
            with patch(
                "backend.src.services.wahoo.limiter.get_seconds_until_next_quarter"
            ) as mock_quarter:
                with patch(
                    "backend.src.services.wahoo.limiter.get_seconds_until_next_day"
                ) as mock_day:
                    mock_quarter.return_value = 300
                    mock_day.return_value = 3600

                    rule(headers, "GET")

                    mock_sleep.assert_called_once_with(0)  # High priority = no wait

    def test_call_without_rates(self):
        """Test calling the rule without valid rates."""
        rule = SleepingRateLimitRule(priority="low")
        headers = {"Content-Type": "application/json"}

        with patch.object(rule, "log") as mock_log:
            rule(headers, "GET")

            mock_log.warning.assert_called_once_with(
                "No rates present in response headers"
            )


class TestRateLimiter:
    """Test RateLimiter class."""

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter()

        assert limiter.rules == []

    def test_rate_limiter_call_with_rules(self):
        """Test calling rate limiter with rules."""
        limiter = RateLimiter()
        mock_rule1 = Mock()
        mock_rule2 = Mock()
        limiter.rules = [mock_rule1, mock_rule2]

        headers = {"X-RateLimit-Usage": "1,2,3"}
        method = "GET"

        limiter(headers, method)

        mock_rule1.assert_called_once_with(headers, method)
        mock_rule2.assert_called_once_with(headers, method)

    def test_rate_limiter_call_without_rules(self):
        """Test calling rate limiter without rules."""
        limiter = RateLimiter()

        headers = {"X-RateLimit-Usage": "1,2,3"}
        method = "GET"

        # Should not raise any exceptions
        limiter(headers, method)


class TestDefaultRateLimiter:
    """Test DefaultRateLimiter class."""

    def test_default_rate_limiter_initialization(self):
        """Test DefaultRateLimiter initialization."""
        limiter = DefaultRateLimiter()

        assert len(limiter.rules) == 1
        assert isinstance(limiter.rules[0], SleepingRateLimitRule)
        assert limiter.rules[0].priority == "high"

    def test_default_rate_limiter_call(self):
        """Test calling DefaultRateLimiter."""
        limiter = DefaultRateLimiter()
        headers = {
            "X-ReadRateLimit-Usage": "5,50,500",
            "X-ReadRateLimit-Limit": "10,100,1000",
        }

        with patch("backend.src.services.wahoo.limiter.time.sleep") as mock_sleep:
            with patch(
                "backend.src.services.wahoo.limiter.get_seconds_until_next_quarter"
            ) as mock_quarter:
                with patch(
                    "backend.src.services.wahoo.limiter.get_seconds_until_next_day"
                ) as mock_day:
                    mock_quarter.return_value = 300
                    mock_day.return_value = 3600

                    limiter(headers, "GET")

                    # Should call sleep with calculated wait time
                    mock_sleep.assert_called_once()
