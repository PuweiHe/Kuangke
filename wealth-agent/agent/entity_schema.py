"""Validate model-extracted entity names before any external lookup."""

from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

EntityName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class EntityNames(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entities: list[EntityName] = Field(max_length=10)

    @field_validator("entities")
    @classmethod
    def unique_names(cls, names: list[str]) -> list[str]:
        return list(dict.fromkeys(names))
