from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


class IncidentStatus(Enum):
    REPORTED = "reported"
    VERIFIED = "verified"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


@dataclass
class Incident:
    description: str
    location: str
    disaster_type: str
    people_affected: int

    # NEW: GPS coordinates
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    vulnerable_people: int = 0
    injuries: int = 0
    mobility_issue: bool = False

    danger_level: int = 0

    required_resources: list[str] = field(
        default_factory=list
    )

    status: IncidentStatus = (
        IncidentStatus.REPORTED
    )

    assigned_team_id: Optional[str] = None

    incident_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )

    updated_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )

    updates: list[str] = field(
        default_factory=list
    )


    def __post_init__(self):

        if not self.description.strip():
            raise ValueError(
                "Description cannot be empty"
            )

        if not self.location.strip():
            raise ValueError(
                "Location cannot be empty"
            )

        if not self.disaster_type.strip():
            raise ValueError(
                "Disaster type cannot be empty"
            )

        if self.people_affected < 1:
            raise ValueError(
                "People affected must be at least 1"
            )

        if self.vulnerable_people < 0:
            raise ValueError(
                "Vulnerable people cannot be negative"
            )

        if self.injuries < 0:
            raise ValueError(
                "Injuries cannot be negative"
            )

        if not 0 <= self.danger_level <= 100:
            raise ValueError(
                "Danger level must be between 0 and 100"
            )


        # Validate GPS coordinates if supplied
        if self.latitude is not None:

            if not -90 <= self.latitude <= 90:
                raise ValueError(
                    "Latitude must be between -90 and 90"
                )


        if self.longitude is not None:

            if not -180 <= self.longitude <= 180:
                raise ValueError(
                    "Longitude must be between -180 and 180"
                )


    def _touch(self):

        self.updated_at = datetime.now(
            timezone.utc
        )


    def add_update(
        self,
        new_description: str
    ):

        if not new_description.strip():
            raise ValueError(
                "Update cannot be empty"
            )

        self.updates.append(
            self.description
        )

        self.description = (
            new_description
        )

        self._touch()


    def assign_team(
        self,
        team_id: str
    ):

        if (
            self.status
            == IncidentStatus.RESOLVED
        ):

            raise ValueError(
                "Cannot assign a team "
                "to a resolved incident"
            )

        self.assigned_team_id = (
            team_id
        )

        self.status = (
            IncidentStatus.ASSIGNED
        )

        self._touch()


    def mark_in_progress(self):

        if self.assigned_team_id is None:

            raise ValueError(
                "Incident must have an assigned "
                "team before starting"
            )

        self.status = (
            IncidentStatus.IN_PROGRESS
        )

        self._touch()


    def resolve(self):

        self.status = (
            IncidentStatus.RESOLVED
        )

        self._touch()