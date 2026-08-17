"""
routers/stream.py — Server-Sent Events untuk visibilitas real-time tanpa polling manual
dari frontend. Komputasi tetap batched (lihat optimize.py) — endpoint ini hanya mendorong
status yang sudah ada di DB begitu berubah, bukan memicu solve baru per koneksi.
"""
import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models.task import OptimizationTask
from src.routers.auth import get_current_user
from src.models.spatial import User

router = APIRouter(prefix="/api/v1/stream", tags=["stream"])

POLL_INTERVAL_SECONDS = 2
MAX_STREAM_SECONDS = 280  # tetap di bawah batas eksekusi function (300s)


@router.get("/optimize/{task_id}")
async def stream_optimize_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """text/event-stream — kirim ulang status task setiap kali berubah, tutup saat terminal."""

    async def event_generator():
        elapsed = 0
        last_status = None
        while elapsed < MAX_STREAM_SECONDS:
            db: Session = SessionLocal()
            try:
                task = db.query(OptimizationTask).filter(OptimizationTask.task_id == task_id).first()
            finally:
                db.close()

            if task is None:
                yield f"data: {json.dumps({'error': 'task not found'})}\n\n"
                return

            if task.status != last_status:
                payload = {
                    "task_id": task.task_id,
                    "status": task.status,
                    "total_annual_cost": task.total_annual_cost,
                    "solve_time_seconds": task.solve_time_seconds,
                }
                yield f"data: {json.dumps(payload)}\n\n"
                last_status = task.status

            if task.status in ("completed", "failed", "timeout"):
                return

            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            elapsed += POLL_INTERVAL_SECONDS

        yield f"data: {json.dumps({'status': 'stream_timeout'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
