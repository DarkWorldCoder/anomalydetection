import json
from copy import deepcopy

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_bulk_detection_and_request_history(client: AsyncClient, auth_headers, traffic_record):
    detection = await client.post("/detect/bulk", headers=auth_headers, json={"records": [traffic_record]})

    assert detection.status_code == 200
    result = detection.json()["data"]["results"][0]
    assert result["request_id"]
    assert result["features"]["url_length"] > 0

    history = await client.get("/requests", headers=auth_headers)
    detail = await client.get(f'/requests/{result["request_id"]}', headers=auth_headers)

    assert history.status_code == 200
    assert history.json()["data"]["total"] == 1
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == result["request_id"]


@pytest.mark.asyncio
async def test_dashboard_uses_saved_detection(client: AsyncClient, auth_headers, traffic_record):
    await client.post("/detect/bulk", headers=auth_headers, json={"records": [traffic_record]})

    summary = await client.get("/dashboard/summary", headers=auth_headers)
    risky = await client.get("/dashboard/top-risky-endpoints", headers=auth_headers)

    assert summary.status_code == 200
    assert summary.json()["data"]["total_requests"] == 1
    assert risky.status_code == 200
    assert len(risky.json()["data"]) == 1


@pytest.mark.asyncio
async def test_json_upload(client: AsyncClient, auth_headers, traffic_record):
    response = await client.post(
        "/detect/upload",
        headers=auth_headers,
        files={"file": ("traffic.json", json.dumps([traffic_record]), "application/json")},
    )

    assert response.status_code == 200
    assert response.json()["data"]["total_requests"] == 1


@pytest.mark.asyncio
async def test_json_upload_preview_includes_full_url_and_details(
    client: AsyncClient, auth_headers, traffic_record
):
    response = await client.post(
        "/detect/preview-upload",
        headers=auth_headers,
        files={"file": ("traffic.json", json.dumps([traffic_record]), "application/json")},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["file_name"] == "traffic.json"
    assert data["total_requests"] == 1
    assert data["preview"][0]["url"] == "https://example.com/api/users?page=1"
    assert data["preview"][0]["request_headers"] == {"User-Agent": "pytest"}
    assert data["preview"][0]["response_headers"] == {"Content-Type": "application/json"}


@pytest.mark.asyncio
async def test_protected_api_rejects_missing_token(client: AsyncClient, traffic_record):
    response = await client.post("/detect/bulk", json={"records": [traffic_record]})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_preview_dashboard_filters_and_delete(client: AsyncClient, auth_headers, traffic_record):
    suspicious = deepcopy(traffic_record)
    suspicious["request"]["url"] = "https://example.com/search?q=<script>alert(1)</script>"

    preview = await client.post(
        "/detect/preview",
        headers=auth_headers,
        json={"records": [traffic_record, suspicious]},
    )
    bulk = await client.post(
        "/detect/bulk",
        headers=auth_headers,
        json={"records": [traffic_record, suspicious]},
    )

    assert preview.status_code == 200
    assert preview.json()["data"]["total_requests"] == 2
    request_id = bulk.json()["data"]["results"][1]["request_id"]

    for endpoint in [
        "/dashboard/request-distribution",
        "/dashboard/request-trend?range=30d",
        "/dashboard/recent-suspicious?limit=10",
    ]:
        response = await client.get(endpoint, headers=auth_headers)
        assert response.status_code == 200

    filtered = await client.get(
        "/requests?prediction=Suspicious&risk_level=medium&method=GET&search=search",
        headers=auth_headers,
    )
    assert filtered.status_code == 200
    assert filtered.json()["data"]["total"] == 1

    deleted = await client.delete(f"/requests/{request_id}", headers=auth_headers)
    missing = await client.get(f"/requests/{request_id}", headers=auth_headers)
    assert deleted.status_code == 200
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_csv_upload(client: AsyncClient, auth_headers):
    csv_content = "\n".join([
        "method,url,request_headers,request_body,response_status,response_headers,status_code,response_body,timestamp,source_ip,response_time_ms",
        'GET,https://example.com/health,{},,OK,{},200,,2026-08-28T10:00:00Z,127.0.0.1,4.2',
    ])
    response = await client.post(
        "/detect/upload",
        headers=auth_headers,
        files={"file": ("traffic.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["data"]["total_requests"] == 1
