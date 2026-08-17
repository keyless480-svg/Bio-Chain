"""
services/ledger_service.py — Append-only hash-chained audit trail.
Not a real blockchain: single trusted DB, no consensus. What it does provide is
tamper-evidence — editing any past row breaks curr_hash for every row written after it,
which a periodic verify_chain() scan will catch.
"""
import hashlib
import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.models.ledger import TraceLedger


def _hash(prev_hash: Optional[str], payload_json: str) -> str:
    basis = (prev_hash or "") + payload_json
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def append_ledger_entry(
    db: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    payload: Dict[str, Any],
    actor_user_id: Optional[int] = None,
) -> TraceLedger:
    """Append one tamper-evident entry. Call this from the same request/transaction
    that creates or mutates the underlying row, right before db.commit()."""
    last = (
        db.query(TraceLedger)
        .order_by(TraceLedger.id.desc())
        .first()
    )
    prev_hash = last.curr_hash if last else None
    payload_json = json.dumps(payload, default=str, sort_keys=True)
    curr_hash = _hash(prev_hash, payload_json)

    entry = TraceLedger(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_user_id=actor_user_id,
        payload_json=payload_json,
        prev_hash=prev_hash,
        curr_hash=curr_hash,
    )
    db.add(entry)
    return entry


def verify_chain(db: Session) -> Dict[str, Any]:
    """Re-walk the whole ledger and confirm every curr_hash still matches
    sha256(prev_hash + payload_json). Returns the first break found, if any."""
    entries = db.query(TraceLedger).order_by(TraceLedger.id.asc()).all()
    prev_hash = None
    for entry in entries:
        expected = _hash(prev_hash, entry.payload_json)
        if expected != entry.curr_hash:
            return {"valid": False, "broken_at_id": entry.id, "entity": f"{entry.entity_type}:{entry.entity_id}"}
        prev_hash = entry.curr_hash
    return {"valid": True, "entries_checked": len(entries)}
