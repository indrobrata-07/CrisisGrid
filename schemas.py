from pydantic import BaseModel, Field


# ===================================================
# INCIDENT SCHEMAS
# ===================================================


class EmergencyReport(BaseModel):

    description: str = Field(
        min_length=5
    )

    location: str = Field(
        min_length=1
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180
    )


# ---------------------------------------------------
# AI EXTRACTED INCIDENT DATA
# ---------------------------------------------------

class ExtractedIncident(BaseModel):

    disaster_type: str

    people_affected: int = Field(
        ge=1
    )

    vulnerable_people: int = Field(
        ge=0
    )

    injuries: int = Field(
        ge=0
    )

    mobility_issue: bool

    required_resources: list[str]

    uncertainty_notes: list[str]


# ---------------------------------------------------
# INCIDENT DESCRIPTION UPDATE
# ---------------------------------------------------

class IncidentDescriptionUpdate(BaseModel):

    description: str = Field(
        min_length=1
    )


# ===================================================
# RESOURCE SCHEMAS
# ===================================================


# ---------------------------------------------------
# CREATE RESOURCE
# ---------------------------------------------------

class ResourceCreate(BaseModel):

    name: str = Field(
        min_length=1
    )

    resource_type: str = Field(
        min_length=1
    )

    capacity: int = Field(
        default=1,
        ge=1
    )

    capabilities: list[str] = Field(
        default_factory=list
    )

    equipment: list[str] = Field(
        default_factory=list
    )

    location: str = Field(
        min_length=1
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180
    )


# ---------------------------------------------------
# RESOURCE STATUS UPDATE
# ---------------------------------------------------

class ResourceStatusUpdate(BaseModel):

    status: str = Field(
        min_length=1
    )


# ---------------------------------------------------
# RESOURCE LIVE GPS UPDATE
# ---------------------------------------------------

class ResourceLocationUpdate(BaseModel):

    latitude: float = Field(
        ge=-90,
        le=90
    )

    longitude: float = Field(
        ge=-180,
        le=180
    )


# ===================================================
# DISPATCH / ASSIGNMENT SCHEMAS
# ===================================================


# ---------------------------------------------------
# HUMAN ACCEPTS DISPATCH RECOMMENDATION
# ---------------------------------------------------

class DispatchAssignmentRequest(BaseModel):

    resource_ids: list[str] = Field(
        min_length=1
    )