"""Extended tests for dependencies to cover missing lines."""

import pytest
from src.dependencies import get_wahoo_service, wahoo


class TestDependenciesExtended:
    """Extended tests for dependencies."""

    def test_get_wahoo_service_not_initialized(self):
        """Test get_wahoo_service when service is not initialized."""
        from src import dependencies

        # Save original wahoo service
        original_wahoo = dependencies.wahoo

        try:
            # Set wahoo to None to simulate not initialized
            dependencies.wahoo = None

            with pytest.raises(RuntimeError, match="Wahoo service not initialized"):
                get_wahoo_service()
        finally:
            # Restore original wahoo service
            dependencies.wahoo = original_wahoo

    def test_get_wahoo_service_initialized(self):
        """Test get_wahoo_service when service is properly initialized."""
        result = get_wahoo_service()
        assert result is wahoo
