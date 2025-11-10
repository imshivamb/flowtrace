from fastapi import FastAPI
from .api import workflows, runs, stream

app = FastAPI(title="FlowTrace")

app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(stream.router, prefix="/api/stream", tags=["stream"])

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"commit": "local-dev"}
