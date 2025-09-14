"""Tests for PostgreSQL database configuration utilities."""

import pytest

from backend.src.utils.postgres import get_database_url


def test_basic_url_construction():
    """Test basic URL construction with all parameters."""
    result = get_database_url(
        host="localhost",
        port="5432",
        database="cycling",
        username="postgres",
        password="postgres",
    )
    expected = "postgresql+asyncpg://postgres:postgres@localhost:5432/cycling"
    assert result == expected


def test_custom_parameters():
    """Test URL construction with custom parameters."""
    result = get_database_url(
        host="remote-host",
        port="3306",
        database="test_db",
        username="test_user",
        password="test_password",
    )
    expected = "postgresql+asyncpg://test_user:test_password@remote-host:3306/test_db"
    assert result == expected


def test_special_characters_in_password():
    """Test that special characters in password are handled correctly."""
    result = get_database_url(
        host="localhost",
        port="5432",
        database="cycling",
        username="postgres",
        password="pass@word#123$",
    )
    expected = "postgresql+asyncpg://postgres:pass@word#123$@localhost:5432/cycling"
    assert result == expected


def test_special_characters_in_host_and_username():
    """Test that special characters in host and username are handled correctly."""
    result = get_database_url(
        host="host with spaces",
        port="5432",
        database="cycling",
        username="user@domain",
        password="password",
    )
    expected = "postgresql+asyncpg://user@domain:password@host with spaces:5432/cycling"
    assert result == expected


@pytest.mark.parametrize(
    "port,expected_port",
    [
        ("5432", "5432"),
        ("5433", "5433"),
        ("3306", "3306"),
        ("8080", "8080"),
    ],
)
def test_different_ports(port, expected_port):
    """Test different port configurations."""
    result = get_database_url(
        host="localhost",
        port=port,
        database="cycling",
        username="postgres",
        password="postgres",
    )
    expected = (
        f"postgresql+asyncpg://postgres:postgres@localhost:{expected_port}/cycling"
    )
    assert result == expected


@pytest.mark.parametrize(
    "db_name",
    [
        "cycling_dev",
        "cycling-staging",
        "cycling_prod_v2",
        "cycling",
        "my_database_name",
    ],
)
def test_different_database_names(db_name):
    """Test different database naming conventions."""
    result = get_database_url(
        host="localhost",
        port="5432",
        database=db_name,
        username="postgres",
        password="postgres",
    )
    expected = f"postgresql+asyncpg://postgres:postgres@localhost:5432/{db_name}"
    assert result == expected


def test_empty_strings():
    """Test that empty strings are handled correctly."""
    result = get_database_url(host="", port="", database="", username="", password="")
    expected = "postgresql+asyncpg://:@:/"
    assert result == expected


@pytest.mark.parametrize(
    "host,port,database,username,password,expected",
    [
        # Local development
        (
            "localhost",
            "5432",
            "cycling",
            "postgres",
            "my_secure_password",
            "postgresql+asyncpg://postgres:my_secure_password@localhost:5432/cycling",
        ),
        # Remote production
        (
            "production-db.company.com",
            "5432",
            "cycling_production",
            "cycling_app",
            "super_secure_password_123",
            "postgresql+asyncpg://cycling_app:super_secure_password_123@production-db.company.com:5432/cycling_production",
        ),
        # Staging with different port
        (
            "staging-db.company.com",
            "5433",
            "cycling_staging",
            "staging_user",
            "staging_pass",
            "postgresql+asyncpg://staging_user:staging_pass@staging-db.company.com:5433/cycling_staging",
        ),
    ],
)
def test_real_world_scenarios(host, port, database, username, password, expected):
    """Test realistic database connection scenarios."""
    result = get_database_url(
        host=host, port=port, database=database, username=username, password=password
    )
    assert result == expected


@pytest.mark.parametrize(
    "args",
    [
        (),  # No arguments
        ("localhost",),  # 1 argument
        ("localhost", "5432"),  # 2 arguments
        ("localhost", "5432", "cycling"),  # 3 arguments
        ("localhost", "5432", "cycling", "postgres"),  # 4 arguments
    ],
)
def test_function_signature_missing_parameters(args):
    """Test that function requires all parameters."""
    # This test ensures that all parameters are required by checking that
    # calling the function with insufficient parameters raises a TypeError
    with pytest.raises(TypeError):
        get_database_url(*args)
