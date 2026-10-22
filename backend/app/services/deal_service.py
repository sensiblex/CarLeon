from fastapi import HTTPException, status as http_status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.deal import Deal
from app.schemas.deal import DealCreate


def create_deal(db: Session, payload: DealCreate) -> Deal:
    exists = db.scalar(select(Deal).where(Deal.track_code == payload.track_code))
    if exists:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Track code {payload.track_code} already used",
        )
    deal = Deal(**payload.model_dump())
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


def get_deal_by_track_code(db: Session, track_code: str) -> Deal:
    deal = db.scalar(select(Deal).where(Deal.track_code == track_code))
    if not deal:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Deal with track code {track_code} not found",
        )
    return deal


def list_deals(db: Session, limit: int = 100, offset: int = 0) -> list[Deal]:
    return list(db.scalars(select(Deal).limit(limit).offset(offset)))