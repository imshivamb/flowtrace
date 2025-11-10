from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class ProviderBinding(Base):
    __tablename__ = "provider_bindings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    provider = Column(Text, nullable=False)
    model = Column(Text, nullable=False)
    temperature = Column(Text, nullable=True)
