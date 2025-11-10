from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from sqlalchemy import insert, select, update, delete
from app.models.workflows import Workflow
from app.schemas.workflow_schema import WorkflowSpec
from uuid import uuid4

router = APIRouter()

@router.get("/")
async def list_workflows():
    async with async_session() as db:
        rows = (await db.execute(select(Workflow))).scalars().all()
        return [{"id": str(r.id), "name": r.name, "description": r.description} for r in rows]

@router.post("/")
async def create_workflow(data: dict):
    spec = WorkflowSpec.parse_obj(data.get("graph_json"))
    async with async_session() as db:
        new_id = uuid4()
        await db.execute(insert(Workflow).values(
            id=new_id,
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            graph_json=spec.dict(),
        ))
        await db.commit()
        return {"id": str(new_id)}

@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    async with async_session() as db:
        wf = await db.get(Workflow, workflow_id)
        if not wf:
            raise HTTPException(404, "not found")
        return {"id": str(wf.id), "name": wf.name, "description": wf.description, "graph_json": wf.graph_json}

@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, data: dict):
    if "graph_json" in data:
        _ = WorkflowSpec.parse_obj(data["graph_json"])
    async with async_session() as db:
        await db.execute(update(Workflow).where(Workflow.id==workflow_id).values(
            name=data.get("name"), description=data.get("description"), graph_json=data.get("graph_json")
        ))
        await db.commit()
        return {"id": workflow_id, "updated": True}

@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    async with async_session() as db:
        await db.execute(delete(Workflow).where(Workflow.id==workflow_id))
        await db.commit()
        return {"deleted": workflow_id}
