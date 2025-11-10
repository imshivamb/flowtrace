from sqlalchemy import Column, Text, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    status = Column(Text, nullable=False)
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    finished_at = Column(TIMESTAMP(timezone=True))
    total_tokens = Column(Integer, default=0)
    total_cost_cents = Column(Integer, default=0)
    total_latency_ms = Column(Integer, default=0)
    error_summary = Column(Text)