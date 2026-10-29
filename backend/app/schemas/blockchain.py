from pydantic import BaseModel, ConfigDict, Field


class StatusChangeIn(BaseModel):
    deal_id: str = Field(min_length=1)
    status: int = Field(ge=0, le=9)
    # Необязательный внешний файл (договор, ПТС и т.п.): хэш считает сервер
    file_path: str | None = None


class StatusChangeRead(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    deal_id: str = Field(min_length=1, max_length=200)
    status: int = Field(ge=0, le=9)
    timestamp: float
    file_path: str | None = Field(default=None, max_length=2048)
    file_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class BlockRead(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    index: int = Field(ge=0)
    timestamp: float
    previous_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    transactions: list[StatusChangeRead] = Field(min_length=1, max_length=500)


class BlockSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block: BlockRead