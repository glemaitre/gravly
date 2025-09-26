"""Tests for Base model."""

from src.models.base import Base


def test_base_inheritance():
    """Test that Base properly integrates with SQLAlchemy DeclarativeBase."""
    # Test that Base can be used to create declarative models
    assert hasattr(Base, "metadata")
    assert hasattr(Base, "registry")


def test_base_metadata_exists():
    """Test Base metadata object is accessible."""
    assert Base.metadata is not None
    assert hasattr(Base.metadata, "create_all")
    assert hasattr(Base.metadata, "drop_all")


def test_base_registry_exists():
    """Test Base registry object is accessible."""
    assert Base.registry is not None


def test_base_declarative_base_integration():
    """Test Base provides proper DeclarativeBase integration."""
    from sqlalchemy.orm import DeclarativeBase

    # Test that Base is correctly derived from DeclarativeBase
    assert issubclass(Base, DeclarativeBase)
    assert hasattr(Base, "registry")
    assert hasattr(Base, "metadata")


def test_base_compatibility():
    """Test Base provides compatibility for declarative models."""
    # Test that Base provides expected properties for subclasses
    assert hasattr(Base, "metadata")
    assert hasattr(Base, "registry")
    assert callable(Base.metadata.create_all)
    assert callable(Base.metadata.drop_all)


def test_base_class_type():
    """Test Base class type and inheritance hierarchy."""
    # Verify it's derived from DeclarativeBase
    base_mro = Base.__mro__
    from sqlalchemy.orm import DeclarativeBase

    # Should find DeclarativeBase in method resolution order
    assert DeclarativeBase in base_mro

    # Should be directly inherited from DeclarativeBase
    assert Base.__bases__ == (DeclarativeBase,)
