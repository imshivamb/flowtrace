from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_workflows():
    return []

@router.post("/")
async def create_workflow(data: dict):
    return {"id": "fake-id"}

@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    return {"id": workflow_id}

@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, data: dict):
    return {"id": workflow_id, "updated": True}

@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    return {"deleted": workflow_id}