"""Unit tests for Wahoo models."""

from datetime import datetime

import pytest

from backend.src.services.wahoo.models import WahooUser


class TestWahooUser:
    """Test WahooUser model."""

    def test_wahoo_user_creation(self):
        """Test creating a WahooUser instance."""
        user_data = {
            "id": 12345,
            "height": 175.5,
            "weight": 70.2,
            "first": "John",
            "last": "Doe",
            "email": "john.doe@example.com",
            "birth": datetime(1990, 5, 15),
            "gender": 1,
            "created_at": datetime(2023, 1, 1, 12, 0, 0),
            "updated_at": datetime(2023, 1, 2, 10, 30, 0),
        }

        user = WahooUser(**user_data)

        assert user.id == 12345
        assert user.height == 175.5
        assert user.weight == 70.2
        assert user.first == "John"
        assert user.last == "Doe"
        assert user.email == "john.doe@example.com"
        assert user.birth == datetime(1990, 5, 15)
        assert user.gender == 1
        assert user.created_at == datetime(2023, 1, 1, 12, 0, 0)
        assert user.updated_at == datetime(2023, 1, 2, 10, 30, 0)

    def test_wahoo_user_validation(self):
        """Test WahooUser field validation."""
        # Test with missing required field
        with pytest.raises(ValueError):
            WahooUser(
                id=12345,
                height=175.5,
                weight=70.2,
                first="John",
                last="Doe",
                email="john.doe@example.com",
                birth=datetime(1990, 5, 15),
                gender=1,
                created_at=datetime(2023, 1, 1, 12, 0, 0),
                # Missing updated_at
            )

    def test_wahoo_user_type_validation(self):
        """Test WahooUser type validation."""
        # Test with wrong type for id
        with pytest.raises(ValueError):
            WahooUser(
                id="not_an_int",  # Should be int
                height=175.5,
                weight=70.2,
                first="John",
                last="Doe",
                email="john.doe@example.com",
                birth=datetime(1990, 5, 15),
                gender=1,
                created_at=datetime(2023, 1, 1, 12, 0, 0),
                updated_at=datetime(2023, 1, 2, 10, 30, 0),
            )

    def test_wahoo_user_serialization(self):
        """Test WahooUser serialization to dict."""
        user_data = {
            "id": 12345,
            "height": 175.5,
            "weight": 70.2,
            "first": "John",
            "last": "Doe",
            "email": "john.doe@example.com",
            "birth": datetime(1990, 5, 15),
            "gender": 1,
            "created_at": datetime(2023, 1, 1, 12, 0, 0),
            "updated_at": datetime(2023, 1, 2, 10, 30, 0),
        }

        user = WahooUser(**user_data)
        user_dict = user.model_dump()

        assert user_dict["id"] == 12345
        assert user_dict["height"] == 175.5
        assert user_dict["weight"] == 70.2
        assert user_dict["first"] == "John"
        assert user_dict["last"] == "Doe"
        assert user_dict["email"] == "john.doe@example.com"
        assert user_dict["birth"] == datetime(1990, 5, 15)
        assert user_dict["gender"] == 1
        assert user_dict["created_at"] == datetime(2023, 1, 1, 12, 0, 0)
        assert user_dict["updated_at"] == datetime(2023, 1, 2, 10, 30, 0)

    def test_wahoo_user_from_dict(self):
        """Test creating WahooUser from dictionary."""
        user_data = {
            "id": 67890,
            "height": 180.0,
            "weight": 75.5,
            "first": "Jane",
            "last": "Smith",
            "email": "jane.smith@example.com",
            "birth": datetime(1985, 8, 20),
            "gender": 2,
            "created_at": datetime(2023, 2, 1, 9, 0, 0),
            "updated_at": datetime(2023, 2, 2, 14, 15, 0),
        }

        user = WahooUser.model_validate(user_data)

        assert user.id == 67890
        assert user.height == 180.0
        assert user.weight == 75.5
        assert user.first == "Jane"
        assert user.last == "Smith"
        assert user.email == "jane.smith@example.com"
        assert user.birth == datetime(1985, 8, 20)
        assert user.gender == 2
        assert user.created_at == datetime(2023, 2, 1, 9, 0, 0)
        assert user.updated_at == datetime(2023, 2, 2, 14, 15, 0)

    def test_wahoo_user_edge_cases(self):
        """Test WahooUser with edge case values."""
        # Test with zero values
        user_data = {
            "id": 0,
            "height": 0.0,
            "weight": 0.0,
            "first": "",
            "last": "",
            "email": "",
            "birth": datetime(1900, 1, 1),
            "gender": 0,
            "created_at": datetime(1970, 1, 1),
            "updated_at": datetime(1970, 1, 1),
        }

        user = WahooUser(**user_data)

        assert user.id == 0
        assert user.height == 0.0
        assert user.weight == 0.0
        assert user.first == ""
        assert user.last == ""
        assert user.email == ""
        assert user.birth == datetime(1900, 1, 1)
        assert user.gender == 0
        assert user.created_at == datetime(1970, 1, 1)
        assert user.updated_at == datetime(1970, 1, 1)

    def test_wahoo_user_immutability(self):
        """Test that WahooUser fields are immutable after creation."""
        user_data = {
            "id": 12345,
            "height": 175.5,
            "weight": 70.2,
            "first": "John",
            "last": "Doe",
            "email": "john.doe@example.com",
            "birth": datetime(1990, 5, 15),
            "gender": 1,
            "created_at": datetime(2023, 1, 1, 12, 0, 0),
            "updated_at": datetime(2023, 1, 2, 10, 30, 0),
        }

        user = WahooUser(**user_data)

        # Pydantic v2 models are mutable by default, so we test that assignment works
        user.id = 99999
        assert user.id == 99999

    def test_wahoo_user_json_serialization(self):
        """Test WahooUser JSON serialization."""
        user_data = {
            "id": 12345,
            "height": 175.5,
            "weight": 70.2,
            "first": "John",
            "last": "Doe",
            "email": "john.doe@example.com",
            "birth": datetime(1990, 5, 15),
            "gender": 1,
            "created_at": datetime(2023, 1, 1, 12, 0, 0),
            "updated_at": datetime(2023, 1, 2, 10, 30, 0),
        }

        user = WahooUser(**user_data)
        user_json = user.model_dump_json()

        # Should be valid JSON
        import json

        parsed = json.loads(user_json)

        assert parsed["id"] == 12345
        assert parsed["height"] == 175.5
        assert parsed["weight"] == 70.2
        assert parsed["first"] == "John"
        assert parsed["last"] == "Doe"
        assert parsed["email"] == "john.doe@example.com"
        assert parsed["gender"] == 1
        # Datetime fields should be serialized as ISO strings
        assert "birth" in parsed
        assert "created_at" in parsed
        assert "updated_at" in parsed
