import math


def haversine_distance(*, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute the great circle distance between two points on Earth in kilometers.

    This function uses the Haversine formula to calculate the shortest distance
    between two points on the Earth's surface, accounting for the Earth's curvature.

    Parameters
    ----------
    lat1 : float
        Latitude of the first point in decimal degrees.
    lon1 : float
        Longitude of the first point in decimal degrees.
    lat2 : float
        Latitude of the second point in decimal degrees.
    lon2 : float
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
    >>> haversine_distance(lat1=46.0, lon1=4.0, lat2=46.1, lon2=4.1)
    12.345678901234567
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    earth_radius, diff_latitude, diff_longitude = 6371, lat2 - lat1, lon2 - lon1

    return (
        earth_radius
        * 2
        * math.asin(
            math.sqrt(
                math.sin(diff_latitude / 2) ** 2
                + math.cos(lat1) * math.cos(lat2) * math.sin(diff_longitude / 2) ** 2
            )
        )
    )
