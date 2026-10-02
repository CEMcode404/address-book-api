"""Pydantic schemas for validating address requests and shaping responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddressBase(BaseModel):
    """Fields shared by address creation and responses."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100, examples=["Home"])
    street: str = Field(min_length=1, max_length=255, examples=["123 Rizal Street"])
    city: str = Field(min_length=1, max_length=100, examples=["Manila"])
    state: str | None = Field(default=None, max_length=100, examples=["Metro Manila"])
    postal_code: str | None = Field(default=None, max_length=20, examples=["1000"])
    country: str = Field(min_length=1, max_length=100, examples=["Philippines"])
    latitude: float = Field(ge=-90, le=90, examples=[14.5995])
    longitude: float = Field(ge=-180, le=180, examples=[120.9842])


class AddressCreate(AddressBase):
    """Request body for creating an address."""


class AddressUpdate(BaseModel):
    """Request body for partially updating an address.

    Only the fields provided in the request are updated.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    street: str | None = Field(default=None, min_length=1, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("name", "street", "city", "country", "latitude", "longitude")
    @classmethod
    def reject_explicit_null(cls, value: object) -> object:
        """Allow omitting required fields, but not setting them to null."""
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class AddressResponse(AddressBase):
    """Address data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime