from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.get("/{run_id}")
async def stream_run_events(run_id: str):
    async def event_stream():
        yield "event: trace\ndata: {\"info\":\"stream not yet wired\"}\n\n"
    return StreamingResponse(event+_stream(), media_type="text/event-stream")

