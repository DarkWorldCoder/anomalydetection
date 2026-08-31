from __future__ import annotations

from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.api_request import ApiRequest, Detection, DetectionBatch, ExtractedFeature
from app.models.user import User
from app.schemas.detection import TrafficRecord
from app.services.detection_service import detect


def create_batch(user: User, input_type: str, filename: str | None = None) -> DetectionBatch:
    return DetectionBatch(user_id=user.id, input_type=input_type, filename=filename)


async def analyze_record(
    db: AsyncSession,
    user: User,
    record: TrafficRecord,
    batch: DetectionBatch | None = None,
) -> ApiRequest:
    result = detect(record)
    parsed = urlparse(record.request.url)
    request = ApiRequest(
        user_id=user.id,
        batch=batch,
        method=record.request.method,
        url=record.request.url,
        endpoint=parsed.path or "/",
        query_string=parsed.query,
        source_ip=record.metadata.source_ip,
        headers=record.request.headers,
        attack_tag=record.request.Attack_Tag,
        body=record.request.body,
        response_status=record.response.status,
        response_headers=record.response.headers,
        response_body=record.response.body,
        status_code=record.response.status_code,
        response_time_ms=record.metadata.response_time_ms,
        raw_request=record.model_dump(mode="json"),
        request_time=record.metadata.timestamp,
        features=ExtractedFeature(**result["features"]),
        detection=Detection(
            anomaly_score=result["anomaly_score"],
            threshold=result["threshold"],
            prediction=result["prediction"],
            risk_level=result["risk_level"],
            attack_type=result["attack_type"],
            explanation=result["explanation"],
            reasons=result["reasons"],
        ),
    )
    db.add(request)
    await db.flush()
    return request


def finish_batch(batch: DetectionBatch, requests: list[ApiRequest]) -> None:
    batch.total_requests = len(requests)
    batch.suspicious_count = sum(item.detection.prediction == "Suspicious" for item in requests)
    batch.benign_count = batch.total_requests - batch.suspicious_count


def detection_result(request: ApiRequest) -> dict:
    detection = request.detection
    return {
        "request_id": request.id,
        "method": request.method,
        "url": request.url,
        "endpoint": request.endpoint,
        "status_code": request.status_code,
        "prediction": detection.prediction,
        "risk_level": detection.risk_level,
        "anomaly_score": detection.anomaly_score,
        "threshold": detection.threshold,
        "attack_type": detection.attack_type,
        "features": request.features.as_dict(),
        "reasons": detection.reasons,
        "explanation": detection.explanation,
        "created_at": request.created_at,
    }


def history_item(request: ApiRequest) -> dict:
    return {
        "id": request.id,
        "method": request.method,
        "endpoint": request.endpoint,
        "status_code": request.status_code,
        "prediction": request.detection.prediction,
        "risk_level": request.detection.risk_level,
        "anomaly_score": request.detection.anomaly_score,
        "attack_type": request.detection.attack_type,
        "created_at": request.created_at,
    }
