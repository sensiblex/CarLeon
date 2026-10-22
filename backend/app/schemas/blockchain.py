from pydantic import BaseModel, Field


class StatusChangeIn(BaseModel):
    deal_id: str = Field(min_length=1)
    status: int = Field(ge=0, le=9)
    # Необязательный внешний файл (договор, ПТС и т.п.): хэш считает сервер
    file_path: str | None = None


class BlockRead(BaseModel):
    index: int
    timestamp: float
    previous_hash: str
    hash: str
    transactions: list[dict]