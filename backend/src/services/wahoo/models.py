"""Models for Wahoo API."""

from datetime import datetime

from pydantic import BaseModel


class WahooUser(BaseModel):
    """Model for a Wahoo user."""

    id: int
    height: float
    weight: float
    first: str
    last: str
    email: str
    birth: datetime
    gender: int
    created_at: datetime
    updated_at: datetime
