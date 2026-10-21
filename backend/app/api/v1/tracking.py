from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_blockchain_service, get_db_session
from app.core.security import require_api_key
from app.schemas.tracking import TrackingPointCreate, TrackingPointRead
from app.services import deal_service, tracking_service
from app.services.blockchain_service import BlockchainService
from app.models.tracking_point import TrackingPoint

router = APIRouter()


@router.post("/{track_code}/tracking", response_model=dict, status_code=201)
def add_tracking_point(
    track_code: str,
    payload: TrackingPointCreate,
    db: Session = Depends(get_db_session),
    blockchain: BlockchainService = Depends(get_blockchain_service),
    _: None = Depends(require_api_key),
):
    deal = deal_service.get_deal_by_track_code(db, track_code)
    point = tracking_service.add_tracking_point(db, blockchain, deal, payload)
    return {"success": True, "data": TrackingPointRead.model_validate(point).model_dump()}


@router.get("/{track_code}/tracking", response_model=dict)
def list_tracking_points(
    track_code: str,
    db: Session = Depends(get_db_session),
):
    deal = deal_service.get_deal_by_track_code(db, track_code)
    points = tracking_service.list_points(db, str(deal.id))
    return {
        "success": True,
        "data": [TrackingPointRead.model_validate(p).model_dump() for p in points],
    }


@router.delete("/{track_code}/tracking/{point_id}", response_model=dict)
def delete_tracking_point(
    track_code: str,
    point_id: str,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_api_key),
):
    deal = deal_service.get_deal_by_track_code(db, track_code)
    point = db.get(TrackingPoint, point_id)
    if not point or point.deal_id != deal.id:
        raise HTTPException(status_code=404, detail="Tracking point not found")
    db.delete(point)
    db.commit()
    return {"success": True, "data": {"deleted": point_id}}