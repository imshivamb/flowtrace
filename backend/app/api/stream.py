from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.executor.tracing import subscribe

router = APIRouter()

@router.get("/{run_id}")
async def stream_run_events(run_id: str):
    async def event_stream():
        q = await subscribe(run_id)
        try:
            while True:
                evt = await q.get()
                yield f"event: trace\ndata: {evt}\n\n"
        except Exception:
            return
    return StreamingResponse(event_stream(), media_type="text/event-stream")
