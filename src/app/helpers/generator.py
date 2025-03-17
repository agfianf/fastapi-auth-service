from sqlalchemy import URL
from uuid_utils.compat import UUID, uuid7


def generate_connection_url(
    driver_name: str,
    username: str,
    password: str,
    host: str,
    port: str | int,
    database: str,
) -> URL:
    """Generate a SQLAlchemy connection URL.

    Parameters
    ----------
    driver_name : str
        Name of the database driver.
    username : str
        Database username.
    password : str
        Database password.
    host : str
        Database host.
    port : str or int
        Database port.
    database : str
        Database name.

    Returns
    -------
    URL
        SQLAlchemy URL object for database connection.

    """
    return URL.create(
        drivername=driver_name,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def generate_uuid() -> UUID:
    """Generate a UUID using the uuid7 specification.

    Returns
    -------
    UUID
        A new UUID (v7) instance.

    """
    return uuid7()
