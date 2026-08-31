from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_db
from app.models.api_request import ApiRequest, Detection
from app.models.user import User
from app.services.request_service import history_item

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def user_filter(user: User):
    return ApiRequest.user_id == user.id


@router.get("/summary")
async def dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total, suspicious = (await db.execute(
        select(
            func.count(ApiRequest.id),
            func.count(case((Detection.prediction == "Suspicious", 1))),
        ).join(ApiRequest.detection).where(user_filter(current_user))
    )).one()
    benign = total - suspicious
    rate = round(suspicious * 100 / total, 2) if total else 0
    data = {
        "total_requests": total,
        "suspicious_requests": suspicious,
        "benigin_requests": benign,
        "anomaly_rate": rate,
        "changes": {"total_requests": 0, "suspicious_requests": 0, "benigin_requests": 0, "anomaly_rate": 0},
    }
    response = success_response("Dashboard summary fetched", data)
    response["last_updated_at"] = datetime.now(UTC)
    return response


@router.get("/request-distribution")
async def request_distribution(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Detection.attack_type, func.count(ApiRequest.id))
        .join(ApiRequest.detection)
        .where(user_filter(current_user), Detection.prediction == "Suspicious")
        .group_by(Detection.attack_type)
    )).all()
    total = sum(count for _, count in rows)
    data = [{"label": label, "count": count, "percentage": round(count * 100 / total, 2)} for label, count in rows] if total else []
    return success_response("Attack distribution fetched", data)


@router.get("/request-trend")
async def request_trend(
    range: str = "7d",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    days = {"7d": 7, "30d": 30, "90d": 90}.get(range, 7)
    start = datetime.now(UTC) - timedelta(days=days)
    date = func.date(ApiRequest.created_at)
    rows = (await db.execute(
        select(
            date,
            func.count(ApiRequest.id),
            func.count(case((Detection.prediction == "Suspicious", 1))),
        )
        .join(ApiRequest.detection)
        .where(user_filter(current_user), ApiRequest.created_at >= start)
        .group_by(date)
        .order_by(date)
    )).all()
    data = [{"date": day, "total_requests": total, "suspicious_requests": suspicious, "benign_requests": total - suspicious} for day, total, suspicious in rows]
    return success_response("Request trend fetched", data)


@router.get("/recent-suspicious")
async def recent_suspicious(
    limit: int = Query(5, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    requests = await db.scalars(
        select(ApiRequest)
        .join(ApiRequest.detection)
        .options(selectinload(ApiRequest.detection))
        .where(user_filter(current_user), Detection.prediction == "Suspicious")
        .order_by(ApiRequest.created_at.desc())
        .limit(limit)
    )
    return success_response("Recent suspicious requests fetched", [history_item(item) for item in requests.all()])


@router.get("/top-risky-endpoints")
async def top_risky_endpoints(
    limit: int = Query(5, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(ApiRequest.method, ApiRequest.endpoint, func.max(Detection.anomaly_score))
        .join(ApiRequest.detection)
        .where(user_filter(current_user))
        .group_by(ApiRequest.method, ApiRequest.endpoint)
        .order_by(func.max(Detection.anomaly_score).desc())
        .limit(limit)
    )).all()
    data = [{"method": method, "endpoint": endpoint, "anomaly_score": score, "risk_level": "high" if score >= 0.7 else "medium" if score >= 0.5752 else "low"} for method, endpoint, score in rows]
    return success_response("Top risky endpoints fetched", data)
