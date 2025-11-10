from sqlalchemy import Column, Text, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class RunStep(Base):
    __tablename__ = "run_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="CASCADE"))
    node_id = Column(Text, nullable=False)
    node_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    finished_at = Column(TIMESTAMP(timezone=True))
    latency_ms = Column(Integer)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost_cents = Column(Integer, default=0)
    error_summary = Column(Text)