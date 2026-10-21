from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.deal import DealStatus


class DealCreate(BaseModel):
    track_code: str = Field(min_length=4, max_length=32)
    title: str = Field(min_length=1, max_length=255)
    supplier: str
    buyer: str


class DealRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    track_code: str
    title: str
    supplier: str
    buyer: str
    status: DealStatus
    created_at: datetime