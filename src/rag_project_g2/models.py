from datetime import datetime

from pydantic import BaseModel, Field


class JobAd(BaseModel):
    """Source-agnostic job ad. Every ingestion client maps its payload to this."""

    id: str
    source: str
    source_id: str
    title: str
    employer: str | None = None
    description: str = ""
    municipality: str | None = None
    region: str | None = None
    region_id: str | None = None
    occupation: str | None = None
    occupation_id: str | None = None
    occupation_group_id: str | None = None
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    url: str  # "Apply" link
    published_at: datetime | None = None
    deadline: datetime | None = None
    remote: bool | None = None
