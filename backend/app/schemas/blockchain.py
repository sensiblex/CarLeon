from pydantic import BaseModel, Field


class StatusChangeIn(BaseModel):
    deal_id: str = Field(min_length=1)
    status: int = Field(ge=0, le=9)


class BlockRead(BaseModel):
    index: int
    timestamp: float
    previous_hash: str
    hash: str
    transactions: list[dict]