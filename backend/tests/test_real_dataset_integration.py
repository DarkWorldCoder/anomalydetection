import json

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal
from app.models.api_request import ApiRequest, Detection, DetectionBatch, ExtractedFeature


def read_first_dataset_records(count: int = 3) -> list[dict]:
    with open("datasets/dataset_3_train.json", encoding="utf-8") as file:
        content = file.read(1_000_000)

    decoder = json.JSONDecoder()
    position = 1
    records = []
    while len(records) < count:
        while content[position] in " \n\r\t,":
            position += 1
        record, position = decoder.raw_decode(content, position)
        records.append(record)
    return records


@pytest.mark.asyncio
async def test_real_dataset_records_complete_full_pipeline(client: AsyncClient, auth_headers):
    records = read_first_dataset_records()
    response = await client.post("/detect/bulk", headers=auth_headers, json={"records": records})

    assert response.status_code == 200
    results = response.json()["data"]["results"]
    assert [item["anomaly_score"] for item in results] == [0.5176, 0.6188, 0.3627]
    assert [item["prediction"] for item in results] == ["Benign", "Suspicious", "Benign"]
    assert results[1]["attack_type"] == "Cross Site Scripting"
    assert "Executable HTML or script syntax was detected" in results[1]["explanation"]

    async with AsyncSessionLocal() as session:
        counts = {
            "requests": await session.scalar(select(func.count(ApiRequest.id))),
            "features": await session.scalar(select(func.count(ExtractedFeature.id))),
            "detections": await session.scalar(select(func.count(Detection.id))),
            "batches": await session.scalar(select(func.count(DetectionBatch.id))),
        }
        batch = await session.scalar(select(DetectionBatch))
        request = await session.scalar(select(ApiRequest).where(ApiRequest.id == results[0]["request_id"]))
        feature = await session.scalar(select(ExtractedFeature).where(ExtractedFeature.request_id == request.id))

    assert counts == {"requests": 3, "features": 3, "detections": 3, "batches": 1}
    assert batch.total_requests == 3
    assert batch.suspicious_count == 1
    assert request.raw_request["request"]["url"] == records[0]["request"]["url"]
    assert feature.url_length == len(records[0]["request"]["url"])
    assert feature.special_char_density > 0


@pytest.mark.asyncio
async def test_model_info_reports_loaded_artifact(client: AsyncClient, auth_headers):
    response = await client.get("/model/info", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "loaded"
    assert data["trees"] == 300
    assert data["feature_count"] == 21
    assert data["threshold"] == 0.5752
