from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from sqlalchemy import insert, select
from app.models.workflow_runs import WorkflowRun
from app.models.workflows import Workflow
from uuid import uuid4
from worker.worker import execute_workflow

router = APIRouter()

@router.post("/{workflow_id}/runs")
async def trigger_run(workflow_id: str):
    async with async_session() as db:  # type: AsyncSession
        wf = await db.get(Workflow, workflow_id)
        if not wf:
            raise HTTPException(404, "workflow not found")
        run_id = uuid4()
        await db.execute(insert(WorkflowRun).values(
            id=run_id, workflow_id=workflow_id, status="queued"
        ))
        await db.commit()
    execute_workflow.delay(str(run_id))
    return {"run_id": str(run_id)}

@router.get("/{run_id}")
async def get_run(run_id: str):
    async with async_session() as db:
        run = await db.get(WorkflowRun, run_id)
        if not run:
            raise HTTPException(404, "run not found")
        return {
            "run_id": run_id,
            "workflow_id": str(run.workflow_id),
            "status": run.status,
            "total_tokens": run.total_tokens,
            "total_cost_cents": run.total_cost_cents,
            "total_latency_ms": run.total_latency_ms,
            "error_summary": run.error_summary,
        }
