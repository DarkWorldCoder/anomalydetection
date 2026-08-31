from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ApiRequestInput(BaseModel):
    headers: dict[str, Any] = Field(default_factory=dict)
    method: str
    url: str
    body: str = ""
    Attack_Tag: str | None = None

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        return value.upper()


class ApiResponseInput(BaseModel):
    status: str = ""
    headers: dict[str, Any] = Field(default_factory=dict)
    status_code: int
    body: str = ""


class RequestMetadata(BaseModel):
    timestamp: datetime | None = None
    source_ip: str = ""
    response_time_ms: float = Field(default=0, ge=0)


class TrafficRecord(BaseModel):
    request: ApiRequestInput
    response: ApiResponseInput
    metadata: RequestMetadata = Field(default_factory=RequestMetadata)


class BulkDetectionRequest(BaseModel):
    records: list[TrafficRecord] = Field(min_length=1, max_length=1000)


class PreviewRequest(BaseModel):
    records: TrafficRecord | list[TrafficRecord]

    def items(self) -> list[TrafficRecord]:
        return self.records if isinstance(self.records, list) else [self.records]
