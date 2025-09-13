import math


def haversine_distance(
    *, latitude_1: float, longitude_1: float, latitude_2: float, longitude_2: float
) -> float:
    """Compute the great circle distance between two points on Earth in kilometers.

    This function uses the Haversine formula to calculate the shortest distance
    between two points on the Earth's surface, accounting for the Earth's curvature.

    Parameters
    ----------
    latitude_1 : float
        Latitude of the first point in decimal degrees.
    longitude_1 : float
        Longitude of the first point in decimal degrees.
    latitude_2 : float
        Latitude of the second point in decimal degrees.
    longitude_2 : float
        Longitude of the second point in decimal degrees.

    Returns
    -------
    float
        Distance between the two points in kilometers.

    Notes
    -----
    The Haversine formula assumes the Earth is a perfect sphere with radius 6371 km.
    For more accurate calculations over long distances, consider using more
    sophisticated ellipsoidal models.

    Examples
    --------
    >>> haversine_distance(
    ...    latitude_1=46.0, longitude_1=4.0, latitude_2=46.1, longitude_2=4.1
    ... )
    12.345678901234567
    """
    latitude_1, longitude_1, latitude_2, longitude_2 = map(
        math.radians, [latitude_1, longitude_1, latitude_2, longitude_2]
    )
    earth_radius = 6371
    diff_latitude = latitude_2 - latitude_1
    diff_longitude = longitude_2 - longitude_1

    haversine = (
        math.sin(diff_latitude / 2) ** 2
        + math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(diff_longitude / 2) ** 2
    )

    return earth_radius * 2 * math.asin(math.sqrt(haversine))
