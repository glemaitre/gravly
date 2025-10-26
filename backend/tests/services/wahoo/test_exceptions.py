"""Unit tests for Wahoo exceptions."""

import pytest

from backend.src.services.wahoo.exceptions import (
    WahooAccessUnauthorized,
    WahooRateLimitExceeded,
)


class TestWahooAccessUnauthorized:
    """Test WahooAccessUnauthorized exception."""

    def test_wahoo_access_unauthorized_inheritance(self):
        """Test that WahooAccessUnauthorized inherits from Exception."""
        assert issubclass(WahooAccessUnauthorized, Exception)

    def test_wahoo_access_unauthorized_creation(self):
        """Test creating WahooAccessUnauthorized exception."""
        exc = WahooAccessUnauthorized("Test message")
        assert str(exc) == "Test message"

    def test_wahoo_access_unauthorized_no_message(self):
        """Test creating WahooAccessUnauthorized without message."""
        exc = WahooAccessUnauthorized()
        assert str(exc) == ""

    def test_wahoo_access_unauthorized_custom_message(self):
        """Test creating WahooAccessUnauthorized with custom message."""
        message = "Custom unauthorized access message"
        exc = WahooAccessUnauthorized(message)
        assert str(exc) == message

    def test_wahoo_access_unauthorized_raise(self):
        """Test raising WahooAccessUnauthorized exception."""
        with pytest.raises(WahooAccessUnauthorized, match="Test unauthorized"):
            raise WahooAccessUnauthorized("Test unauthorized")

    def test_wahoo_access_unauthorized_catch(self):
        """Test catching WahooAccessUnauthorized exception."""
        try:
            raise WahooAccessUnauthorized("Test catch")
        except WahooAccessUnauthorized as e:
            assert str(e) == "Test catch"
        except Exception:
            pytest.fail("Should have caught WahooAccessUnauthorized")

    def test_wahoo_access_unauthorized_catch_generic(self):
        """Test catching WahooAccessUnauthorized as generic Exception."""
        try:
            raise WahooAccessUnauthorized("Test generic catch")
        except Exception as e:
            assert isinstance(e, WahooAccessUnauthorized)
            assert str(e) == "Test generic catch"


class TestWahooRateLimitExceeded:
    """Test WahooRateLimitExceeded exception."""

    def test_wahoo_rate_limit_exceeded_inheritance(self):
        """Test that WahooRateLimitExceeded inherits from Exception."""
        assert issubclass(WahooRateLimitExceeded, Exception)

    def test_wahoo_rate_limit_exceeded_creation(self):
        """Test creating WahooRateLimitExceeded exception."""
        exc = WahooRateLimitExceeded("Test rate limit message")
        assert str(exc) == "Test rate limit message"

    def test_wahoo_rate_limit_exceeded_no_message(self):
        """Test creating WahooRateLimitExceeded without message."""
        exc = WahooRateLimitExceeded()
        assert str(exc) == ""

    def test_wahoo_rate_limit_exceeded_custom_message(self):
        """Test creating WahooRateLimitExceeded with custom message."""
        message = "Custom rate limit exceeded message"
        exc = WahooRateLimitExceeded(message)
        assert str(exc) == message

    def test_wahoo_rate_limit_exceeded_raise(self):
        """Test raising WahooRateLimitExceeded exception."""
        with pytest.raises(WahooRateLimitExceeded, match="Test rate limit"):
            raise WahooRateLimitExceeded("Test rate limit")

    def test_wahoo_rate_limit_exceeded_catch(self):
        """Test catching WahooRateLimitExceeded exception."""
        try:
            raise WahooRateLimitExceeded("Test rate limit catch")
        except WahooRateLimitExceeded as e:
            assert str(e) == "Test rate limit catch"
        except Exception:
            pytest.fail("Should have caught WahooRateLimitExceeded")

    def test_wahoo_rate_limit_exceeded_catch_generic(self):
        """Test catching WahooRateLimitExceeded as generic Exception."""
        try:
            raise WahooRateLimitExceeded("Test rate limit generic catch")
        except Exception as e:
            assert isinstance(e, WahooRateLimitExceeded)
            assert str(e) == "Test rate limit generic catch"


class TestWahooExceptionsIntegration:
    """Test Wahoo exceptions in integration scenarios."""

    def test_exceptions_are_different_types(self):
        """Test that Wahoo exceptions are different types."""
        exc1 = WahooAccessUnauthorized("Test 1")
        exc2 = WahooRateLimitExceeded("Test 2")

        assert type(exc1) is not type(exc2)
        assert not isinstance(exc1, WahooRateLimitExceeded)
        assert not isinstance(exc2, WahooAccessUnauthorized)

    def test_exceptions_can_be_caught_separately(self):
        """Test that Wahoo exceptions can be caught separately."""
        # Test catching WahooAccessUnauthorized
        try:
            raise WahooAccessUnauthorized("Unauthorized test")
        except WahooAccessUnauthorized:
            pass  # Should be caught
        except WahooRateLimitExceeded:
            pytest.fail("Should not catch WahooRateLimitExceeded")
        except Exception:
            pytest.fail("Should not catch generic Exception")

        # Test catching WahooRateLimitExceeded
        try:
            raise WahooRateLimitExceeded("Rate limit test")
        except WahooAccessUnauthorized:
            pytest.fail("Should not catch WahooAccessUnauthorized")
        except WahooRateLimitExceeded:
            pass  # Should be caught
        except Exception:
            pytest.fail("Should not catch generic Exception")

    def test_exceptions_can_be_caught_together(self):
        """Test that Wahoo exceptions can be caught together."""
        exceptions_to_test = [
            WahooAccessUnauthorized("Unauthorized"),
            WahooRateLimitExceeded("Rate limit"),
        ]

        for exc in exceptions_to_test:
            try:
                raise exc
            except (WahooAccessUnauthorized, WahooRateLimitExceeded) as e:
                assert isinstance(e, (WahooAccessUnauthorized, WahooRateLimitExceeded))
            except Exception:
                pytest.fail(f"Should have caught {type(exc).__name__}")

    def test_exceptions_inherit_from_exception(self):
        """Test that both Wahoo exceptions inherit from Exception."""
        exc1 = WahooAccessUnauthorized("Test")
        exc2 = WahooRateLimitExceeded("Test")

        assert isinstance(exc1, Exception)
        assert isinstance(exc2, Exception)

    def test_exceptions_can_be_raised_in_functions(self):
        """Test that Wahoo exceptions can be raised in functions."""

        def raise_unauthorized():
            raise WahooAccessUnauthorized("Function unauthorized")

        def raise_rate_limit():
            raise WahooRateLimitExceeded("Function rate limit")

        with pytest.raises(WahooAccessUnauthorized):
            raise_unauthorized()

        with pytest.raises(WahooRateLimitExceeded):
            raise_rate_limit()

    def test_exceptions_with_multiple_arguments(self):
        """Test Wahoo exceptions with multiple arguments."""
        # Test with multiple string arguments
        exc1 = WahooAccessUnauthorized("arg1", "arg2", "arg3")
        assert str(exc1) == "('arg1', 'arg2', 'arg3')"

        exc2 = WahooRateLimitExceeded("arg1", "arg2", "arg3")
        assert str(exc2) == "('arg1', 'arg2', 'arg3')"

    def test_exceptions_with_non_string_arguments(self):
        """Test Wahoo exceptions with non-string arguments."""
        exc1 = WahooAccessUnauthorized(123, {"key": "value"})
        assert str(exc1) == "(123, {'key': 'value'})"

        exc2 = WahooRateLimitExceeded([1, 2, 3], None)
        assert str(exc2) == "([1, 2, 3], None)"

    def test_exceptions_are_pickleable(self):
        """Test that Wahoo exceptions can be pickled (for multiprocessing)."""
        import pickle

        exc1 = WahooAccessUnauthorized("Pickle test")
        exc2 = WahooRateLimitExceeded("Pickle test")

        # Test pickling
        pickled1 = pickle.dumps(exc1)
        pickled2 = pickle.dumps(exc2)

        # Test unpickling
        unpickled1 = pickle.loads(pickled1)
        unpickled2 = pickle.loads(pickled2)

        assert isinstance(unpickled1, WahooAccessUnauthorized)
        assert isinstance(unpickled2, WahooRateLimitExceeded)
        assert str(unpickled1) == "Pickle test"
        assert str(unpickled2) == "Pickle test"
