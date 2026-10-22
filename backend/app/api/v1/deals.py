from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.core.security import require_api_key
from app.schemas.deal import DealCreate, DealRead
from app.services import deal_service

router = APIRouter()


@router.post("", response_model=dict, status_code=201)
def create_deal(
    payload: DealCreate,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_api_key),
):
    deal = deal_service.create_deal(db, payload)
    return {"success": True, "data": DealRead.model_validate(deal).model_dump()}


@router.get("", response_model=dict)
def list_deals(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
):
    deals = deal_service.list_deals(db, limit=limit, offset=offset)
    return {
        "success": True,
        "data": [DealRead.model_validate(d).model_dump() for d in deals],
    }


@router.get("/{track_code}", response_model=dict)
def get_deal_by_track_code(
    track_code: str,
    db: Session = Depends(get_db_session),
):
    deal = deal_service.get_deal_by_track_code(db, track_code)
    return {"success": True, "data": DealRead.model_validate(deal).model_dump()}


@router.delete("/{track_code}", response_model=dict)
def delete_deal(
    track_code: str,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_api_key),
):
    deal = deal_service.get_deal_by_track_code(db, track_code)
    db.delete(deal)          # cascade удалит tracking_points (ondelete="CASCADE")
    db.commit()
    return {"success": True, "data": {"deleted": track_code}}