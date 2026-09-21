from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


class ResourceStatus(Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class Resource:
    name: str
    resource_type: str

    capacity: int = 1

    capabilities: list[str] = field(
        default_factory=list
    )

    equipment: list[str] = field(
        default_factory=list
    )

    location: str = ""

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    status: ResourceStatus = (
        ResourceStatus.AVAILABLE
    )

    current_assignment: Optional[str] = None

    resource_id: str = field(
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

    def __post_init__(self):

        if not self.name.strip():
            raise ValueError(
                "Resource name cannot be empty"
            )

        if not self.resource_type.strip():
            raise ValueError(
                "Resource type cannot be empty"
            )

        if self.capacity < 1:
            raise ValueError(
                "Capacity must be at least 1"
            )