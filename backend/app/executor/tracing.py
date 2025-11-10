import asyncio
from typing import Any, Dict, DefaultDict, List, Optional
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from app.models.trace_events import TraceEvent

# Per-run async subscribers for SSE (in-memory for V1)
_subscribers: DefaultDict[str, List[asyncio.Queue]] = defaultdict(list)

async def subscribe(run_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers[run_id].append(q)
    return q

def _cleanup(run_id: str, q: asyncio.Queue):
    try:
        _subscribers[run_id].remove(q)
    except ValueError:
        pass

async def emit_event(db: AsyncSession, run_id: str, step_id: Optional[str], kind: str, payload: Dict[str, Any]):
    # Persist
    await db.execute(insert(TraceEvent).values(
        run_id=run_id, step_id=step_id, kind=kind, payload=payload
    ))
    await db.commit()
    # Fan-out
    for q in _subscribers.get(run_id, []):
        await q.put({"kind": kind, "step_id": step_id, "payload": payload})
