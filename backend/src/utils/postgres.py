"""PostgreSQL database configuration utilities."""


def get_database_url(
    *,
    host: str,
    port: str,
    database: str,
    username: str,
    password: str,
) -> str:
    """Construct PostgreSQL database URL from provided parameters.

    Parameters
    ----------
    host : str
        Database host.
    port : str
        Database port.
    database : str
        Database name.
    username : str
        Database username.
    password : str
        Database password.

    Returns
    -------
    str
        PostgreSQL connection string in the format:
        postgresql+asyncpg://username:password@host:port/database_name

    Examples
    --------
    >>> get_database_url("localhost", "5432", "cycling", "postgres", "mypassword")
    'postgresql+asyncpg://postgres:mypassword@localhost:5432/cycling'

    >>> get_database_url("remote-host", "5432", "my_db", "user", "pass")
    'postgresql+asyncpg://user:pass@remote-host:5432/my_db'
    """
    return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
