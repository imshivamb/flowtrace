from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, BIGINT
from sqlalchemy.sql import func
from .base import Base

class TraceEvent(Base):
    __tablename__ = "trace_events"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="CASCADE"))
    step_id = Column(UUID(as_uuid=True), ForeignKey("run_steps.id", ondelete="SET NULL"))
    ts = Column(TIMESTAMP(timezone=True), server_default=func.now())
    kind = Column(Text, nullable=False)
    payload = Column(JSON, nullable=False)
