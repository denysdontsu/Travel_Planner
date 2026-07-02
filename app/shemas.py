from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Place Schemas

class PlaceCreateInput(BaseModel):
    """Used to create a place separately or as part of a project creation request."""
    external_place_id: str = Field(..., description="ID объекта из Art Institute API")
    notes: Optional[str] = Field(None, max_length=1000)


class PlaceUpdate(BaseModel):
    """Schema for updating a project place."""
    notes: Optional[str] = Field(None, max_length=1000)
    is_visited: Optional[bool] = None


class PlaceResponse(BaseModel):
    """Response schema representing a place in a travel project."""
    id: int
    project_id: int
    external_place_id: str
    notes: Optional[str]
    is_visited: bool

    model_config = ConfigDict(
        from_attributes=True
    )

# Travel Project Schemas
class ProjectCreate(BaseModel):
    """Schema for creating a travel project with optional places."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    start_date: date | None = None
    places: list[PlaceCreateInput] = Field(default=[], max_length=10)

    @field_validator("places")
    @classmethod
    def validate_no_duplicates(cls, v):
        ids = [p.external_place_id for p in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate places are not allowed.")
        return v


class ProjectUpdate(BaseModel):
    """Schema for updating travel project information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    start_date: Optional[date] = None


class ProjectResponse(BaseModel):
    """Response schema representing a travel project and its places."""
    id: int
    name: str
    description: Optional[str]
    start_date: Optional[date]
    is_completed: bool
    places: List[PlaceResponse] = []

    model_config = ConfigDict(
        from_attributes=True
    )