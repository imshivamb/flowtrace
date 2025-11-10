import asyncio
from celery import Celery
from app.core.config import settings
from app.db.session import async_session
from app.executor.runner import run_workflow
from sqlalchemy import insert
from app.models.workflow_runs import WorkflowRun
from app.models.workflows import Workflow
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.workflow_schema import WorkflowSpec

celery = Celery("flowtrace", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

@celery.task
def execute_workflow(run_id: str):
    asyncio.run(_async_execute(run_id))
    return f"executed {run_id}"

async def _async_execute(run_id: str):
    async with async_session() as db:  # type: AsyncSession
        # load workflow + graph
        run = await db.get(WorkflowRun, run_id)
        wf = await db.get(Workflow, run.workflow_id)
        spec = WorkflowSpec.parse_obj(wf.graph_json)
        await run_workflow(db, str(run_id), spec)
