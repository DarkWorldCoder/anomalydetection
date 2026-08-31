import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.schemas.detection import BulkDetectionRequest, PreviewRequest, TrafficRecord
from app.services.request_service import analyze_record, create_batch, detection_result, finish_batch

router = APIRouter(prefix="/detect", tags=["Detection"])


def preview_data(records: list[TrafficRecord], file_name: str | None = None) -> dict:
    preview = [
        {
            "index": index,
            "timestamp": record.metadata.timestamp,
            "url": record.request.url,
            "method": record.request.method,
            "status": record.response.status,
            "status_code": record.response.status_code,
            "request_size_bytes": len(record.request.body.encode()),
            "response_size_bytes": len(record.response.body.encode()),
            "response_time_ms": record.metadata.response_time_ms,
            "source_ip": record.metadata.source_ip,
            "attack_tag": record.request.Attack_Tag,
            "request_headers": record.request.headers,
            "request_body": record.request.body,
            "response_headers": record.response.headers,
            "response_body": record.response.body,
        }
        for index, record in enumerate(records, 1)
    ]
    data = {"total_requests": len(records), "preview": preview}
    if file_name is not None:
        data["file_name"] = file_name
    return data


def validate_record_count(records: list[TrafficRecord]) -> None:
    if not records or len(records) > 1000:
        raise HTTPException(status_code=422, detail="File must contain between 1 and 1000 records")


@router.post("/preview")
async def preview_records(
    payload: PreviewRequest,
    _: User = Depends(get_current_user),
):
    records = payload.items()
    return success_response("Request preview generated", preview_data(records))


@router.post("/bulk")
async def bulk_detect(
    payload: BulkDetectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    batch = create_batch(current_user, "json")
    db.add(batch)
    requests = [await analyze_record(db, current_user, record, batch) for record in payload.records]
    finish_batch(batch, requests)
    await db.commit()
    for request in requests:
        await db.refresh(request, attribute_names=["created_at"])
    results = [detection_result(request) for request in requests]
    suspicious = [request for request in requests if request.detection.prediction == "Suspicious"]
    data = {
        "total_requests": len(requests),
        "benign_count": len(requests) - len(suspicious),
        "suspicious_count": len(suspicious),
        "high_risk_count": sum(request.detection.risk_level == "high" for request in requests),
        "medium_risk_count": sum(request.detection.risk_level == "medium" for request in requests),
        "low_risk_count": sum(request.detection.risk_level == "low" for request in requests),
        "results": results,
    }
    return success_response("Detection completed", data)


def parse_upload(content: bytes, filename: str) -> list[TrafficRecord]:
    try:
        if filename.lower().endswith(".json"):
            payload = json.loads(content)
            rows = payload.get("records", payload) if isinstance(payload, dict) else payload
        elif filename.lower().endswith(".csv"):
            rows = []
            for row in csv.DictReader(io.StringIO(content.decode())):
                rows.append({
                    "request": {
                        "method": row.get("method", "GET"),
                        "url": row.get("url", row.get("endpoint", "/")),
                        "headers": json.loads(row.get("request_headers", "{}")),
                        "body": row.get("request_body", ""),
                        "Attack_Tag": row.get("attack_type") or None,
                    },
                    "response": {
                        "status": row.get("response_status", ""),
                        "headers": json.loads(row.get("response_headers", "{}")),
                        "status_code": int(row.get("status_code", 0)),
                        "body": row.get("response_body", ""),
                    },
                    "metadata": {
                        "timestamp": row.get("timestamp") or None,
                        "source_ip": row.get("source_ip", ""),
                        "response_time_ms": float(row.get("response_time_ms", 0)),
                    },
                })
        else:
            raise ValueError("Only JSON and CSV files are supported")
        return [TrafficRecord.model_validate(row) for row in rows]
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


async def read_upload(file: UploadFile) -> list[TrafficRecord]:
    content = await file.read(5_000_001)
    if len(content) > 5_000_000:
        raise HTTPException(status_code=413, detail="File must be 5 MB or smaller")
    records = parse_upload(content, file.filename or "")
    validate_record_count(records)
    return records


@router.post("/preview-upload")
async def preview_upload(
    file: UploadFile,
    _: User = Depends(get_current_user),
):
    records = await read_upload(file)
    return success_response(
        "File preview generated",
        preview_data(records, file.filename),
    )


@router.post("/upload")
async def upload_and_detect(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    records = await read_upload(file)

    input_type = "csv" if (file.filename or "").lower().endswith(".csv") else "json"
    batch = create_batch(current_user, input_type, file.filename)
    db.add(batch)
    requests = [await analyze_record(db, current_user, record, batch) for record in records]
    finish_batch(batch, requests)
    await db.commit()
    for request in requests:
        await db.refresh(request, attribute_names=["created_at"])
    results = [detection_result(request) for request in requests]
    suspicious_count = batch.suspicious_count
    return success_response("File detection completed", {
        "file_name": file.filename,
        "batch_id": batch.id,
        "total_requests": len(requests),
        "benign_count": len(requests) - suspicious_count,
        "suspicious_count": suspicious_count,
        "results": results,
    })
