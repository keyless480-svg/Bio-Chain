"""
models/ledger.py — Append-only, hash-chained audit trail (tamper-evident, not blockchain).
Every write to Harvest/HubBatch/Shipment appends one row here via services/ledger_service.py.
Rows are never UPDATEd or DELETEd; corrections are new rows with action="corrected".
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from src.database import Base


class TraceLedger(Base):
    __tablename__ = "trace_ledger"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(30), nullable=False)   # harvest|hub_batch|shipment
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(30), nullable=False)        # created|status_changed|corrected
    actor_user_id = Column(Integer, nullable=True)
    payload_json = Column(Text, nullable=False)         # snapshot data saat entri ditulis
    prev_hash = Column(String(64), nullable=True)
    curr_hash = Column(String(64), nullable=False)      # sha256(prev_hash + payload_json)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
