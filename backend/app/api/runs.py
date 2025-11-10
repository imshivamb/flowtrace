from fastapi import APIRouter

router = APIRouter()

@router.post("/{workflow_id}/runs")
async def trigger_run(workflow_id: str):
    return {"run_id": "fake-run-id"}

@router.get("/{run_id}")
async def get_run(run_id: str):
    return {"run_id": run_id, "status": "queued"}

