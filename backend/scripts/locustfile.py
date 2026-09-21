"""Locust workload for authenticated detection of real dataset records."""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from locust import HttpUser, between, task


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path(
    os.getenv(
        "REAL_DATASET_PATH",
        str(ROOT / "datasets" / "dataset_4_sample_100_mixed.json"),
    )
)
BATCH_SIZE = int(os.getenv("REAL_DATA_BATCH_SIZE", "10"))

payload = json.loads(DATASET.read_text(encoding="utf-8"))
rows = payload.get("records", payload) if isinstance(payload, dict) else payload
if not isinstance(rows, list) or not rows:
    raise RuntimeError("REAL_DATASET_PATH must contain a non-empty JSON record array")
REAL_RECORDS = rows[:BATCH_SIZE]


class DetectionApiUser(HttpUser):
    wait_time = between(0.5, 1.5)

    def on_start(self) -> None:
        unique = uuid4().hex
        self.email = f"locust-{unique}@example.com"
        credentials = {
            "full_name": "Locust Performance User",
            "email": self.email,
            "password": "strongpass123",
        }
        register = self.client.post("/auth/register", json=credentials, name="POST /auth/register")
        if register.status_code not in (200, 201):
            raise RuntimeError(f"registration failed: {register.status_code} {register.text}")

        login = self.client.post(
            "/auth/login",
            json={"email": self.email, "password": credentials["password"]},
            name="POST /auth/login",
        )
        if login.status_code != 200:
            raise RuntimeError(f"login failed: {login.status_code} {login.text}")
        token = login.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {token}"}

    @task(4)
    def detect_real_batch(self) -> None:
        with self.client.post(
            "/detect/bulk",
            headers=self.headers,
            json={"records": REAL_RECORDS},
            name=f"POST /detect/bulk [{len(REAL_RECORDS)} real records]",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"HTTP {response.status_code}: {response.text[:200]}")
                return
            data = response.json().get("data", {})
            if data.get("total_requests") != len(REAL_RECORDS):
                response.failure("response record count did not match the submitted batch")

    @task(1)
    def read_model_info(self) -> None:
        self.client.get("/model/info", headers=self.headers, name="GET /model/info")
