import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_db
from backend.app.models.api_request import ApiRequest, Detection
from app.models.user import User
from app.services.request_service import detection_result

router = APIRouter(prefix="/requests", tags=["Requests"])


@router.get("")
async def list_requests(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    prediction: str | None = None,
    risk_level: str | None = None,
    method: str | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [ApiRequest.user_id == current_user.id]
    if prediction:
        filters.append(Detection.prediction.ilike(prediction))
    if risk_level:
        filters.append(Detection.risk_level.ilike(risk_level))
    if method:
        filters.append(ApiRequest.method.ilike(method))
    if search:
        filters.append(or_(ApiRequest.url.ilike(f"%{search}%"), ApiRequest.endpoint.ilike(f"%{search}%")))

    total = await db.scalar(select(func.count(ApiRequest.id)).join(ApiRequest.detection).where(*filters)) or 0
    sortable = {
        "created_at": ApiRequest.created_at,
        "anomaly_score": Detection.anomaly_score,
        "status_code": ApiRequest.status_code,
        "method": ApiRequest.method,
    }
    column = sortable.get(sort_by, ApiRequest.created_at)
    ordering = asc(column) if sort_order.lower() == "asc" else desc(column)
    result = await db.scalars(
        select(ApiRequest)
        .join(ApiRequest.detection)
        .options(selectinload(ApiRequest.features), selectinload(ApiRequest.detection))
        .where(*filters)
        .order_by(ordering)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return success_response("Request logs fetched", {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": math.ceil(total / limit),
        "items": [detection_result(item) for item in result.all()],
    })


async def owned_request(db: AsyncSession, user: User, request_id: UUID) -> ApiRequest:
    request = await db.scalar(
        select(ApiRequest)
        .options(selectinload(ApiRequest.features), selectinload(ApiRequest.detection))
        .where(ApiRequest.id == request_id, ApiRequest.user_id == user.id)
    )
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return request


@router.get("/{request_id}")
async def get_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    request = await owned_request(db, current_user, request_id)
    data = {
        "id": request.id,
        "time": request.created_at,
        "method": request.method,
        "url": request.url,
        "endpoint": request.endpoint,
        "query_string": request.query_string,
        "source_ip": request.source_ip,
        "request": {"headers": request.headers, "body": request.body},
        "response": {
            "status": request.response_status,
            "headers": request.response_headers,
            "status_code": request.status_code,
            "body": request.response_body,
        },
        "features": request.features.as_dict(),
        "detection": detection_result(request),
    }
    return success_response("Request details fetched", data)


@router.delete("/{request_id}")
async def delete_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    request = await owned_request(db, current_user, request_id)
    await db.delete(request)
    await db.commit()
    return success_response("Request deleted successfully")
