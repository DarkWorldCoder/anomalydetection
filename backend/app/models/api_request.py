from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class DetectionBatch(Base):
    __tablename__ = "detection_batches"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str | None] = mapped_column(String(255))
    input_type: Mapped[str] = mapped_column(String(20))
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    suspicious_count: Mapped[int] = mapped_column(Integer, default=0)
    benign_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    requests: Mapped[list["ApiRequest"]] = relationship(back_populates="batch")


class ApiRequest(Base):
    __tablename__ = "api_requests"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    batch_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("detection_batches.id", ondelete="SET NULL"), index=True)
    method: Mapped[str] = mapped_column(String(10))
    url: Mapped[str] = mapped_column(Text)
    endpoint: Mapped[str] = mapped_column(String(2048), index=True)
    query_string: Mapped[str] = mapped_column(Text, default="")
    source_ip: Mapped[str] = mapped_column(String(64), default="")
    headers: Mapped[dict] = mapped_column(JSON, default=dict)
    attack_tag: Mapped[str | None] = mapped_column(String(80))
    body: Mapped[str] = mapped_column(Text, default="")
    response_status: Mapped[str] = mapped_column(String(100), default="")
    response_headers: Mapped[dict] = mapped_column(JSON, default=dict)
    response_body: Mapped[str] = mapped_column(Text, default="")
    status_code: Mapped[int] = mapped_column(Integer, default=0)
    response_time_ms: Mapped[float] = mapped_column(Float, default=0)
    raw_request: Mapped[dict] = mapped_column(JSON)
    request_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    batch: Mapped[DetectionBatch | None] = relationship(back_populates="requests")
    features: Mapped["ExtractedFeature"] = relationship(back_populates="request", cascade="all, delete-orphan", uselist=False)
    detection: Mapped["Detection"] = relationship(back_populates="request", cascade="all, delete-orphan", uselist=False)


class ExtractedFeature(Base):
    __tablename__ = "extracted_features"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("api_requests.id", ondelete="CASCADE"), unique=True)
    url_length: Mapped[int] = mapped_column(Integer)
    endpoint_depth: Mapped[int] = mapped_column(Integer)
    query_param_count: Mapped[int] = mapped_column(Integer)
    body_length: Mapped[int] = mapped_column(Integer)
    header_count: Mapped[int] = mapped_column(Integer)
    cookie_length: Mapped[int] = mapped_column(Integer)
    user_agent_length: Mapped[int] = mapped_column(Integer)
    special_char_count: Mapped[int] = mapped_column(Integer)
    special_char_density: Mapped[float] = mapped_column(Float)
    sql_pattern_score: Mapped[float] = mapped_column(Float)
    xss_pattern_score: Mapped[float] = mapped_column(Float)
    traversal_pattern_score: Mapped[float] = mapped_column(Float)
    command_pattern_score: Mapped[float] = mapped_column(Float)
    log_injection_pattern_score: Mapped[float] = mapped_column(Float)
    log4j_pattern_score: Mapped[float] = mapped_column(Float)
    cookie_injection_pattern_score: Mapped[float] = mapped_column(Float)
    composite_anomaly_score: Mapped[float] = mapped_column(Float)
    response_body_length: Mapped[int] = mapped_column(Integer)
    response_header_count: Mapped[int] = mapped_column(Integer)
    status_code: Mapped[int] = mapped_column(Integer)
    is_error_status: Mapped[int] = mapped_column(Integer)

    request: Mapped[ApiRequest] = relationship(back_populates="features")

    def as_dict(self) -> dict:
        excluded = {"id", "request_id"}
        return {column.name: getattr(self, column.name) for column in self.__table__.columns if column.name not in excluded}


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("api_requests.id", ondelete="CASCADE"), unique=True)
    anomaly_score: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    prediction: Mapped[str] = mapped_column(String(20), index=True)
    risk_level: Mapped[str] = mapped_column(String(20), index=True)
    attack_type: Mapped[str] = mapped_column(String(80), default="Unknown")
    explanation: Mapped[str] = mapped_column(Text, default="")
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    request: Mapped[ApiRequest] = relationship(back_populates="detection")
