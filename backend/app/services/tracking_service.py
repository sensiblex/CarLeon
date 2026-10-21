from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.models.deal import Deal
from app.models.tracking_point import TrackingPoint
from app.schemas.tracking import TrackingPointCreate
from app.services.blockchain_service import BlockchainService


def add_tracking_point(
    db: Session,
    blockchain: BlockchainService,
    deal: Deal,
    payload: TrackingPointCreate,
) -> TrackingPoint:
    try:
        blockchain.validate_status(payload.status)
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status {payload.status}",
        )

    tx_hash, block_index = blockchain.record(str(deal.id), int(payload.status))

    point = TrackingPoint(
        deal_id=deal.id,
        status=int(payload.status),
        comment=payload.comment,
        tx_hash=tx_hash,
        block_index=block_index,
    )
    db.add(point)

    deal.status = payload.status
    db.commit()
    db.refresh(point)
    return point


def list_points(db: Session, deal_id: str) -> list[TrackingPoint]:
    from sqlalchemy import select

    return list(
        db.scalars(
            select(TrackingPoint)
            .where(TrackingPoint.deal_id == deal_id)
            .order_by(TrackingPoint.created_at)
        )
    )