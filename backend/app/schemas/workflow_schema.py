from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Literal

NodeTypes = Literal["llm", "tool", "router"]

class Node(BaseModel):
    id: str
    type: NodeTypes
    name: str
    config: Dict = Field(default_factory=dict)
    inputs: Dict = Field(default_factory=dict)
    
class Edge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    when: Optional[str] = None
    
class Limits(BaseModel):
    maxNodes: int = Field(default=20)
    maxTokens: int = Field(default=150000)
    timeoutSeconds: int = Field(default=120)
    
class WorkflowSpec(BaseModel):
    version: str
    entry: str
    nodes: List[Node]
    edges: List[Edge]
    limits: Limits = Limits()
    
    @validator("nodes")
    def unique_ids(cls, v):
        ids = [n.id for n in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Node IDs must be unique")
        return v
    
    @validator("entry")
    def entry_must_exist(cls, v, values):
        if "nodes" in values:
            ids = {n.id for n in values["nodes"]}
            if v not in ids:
                raise ValueError("entry node not present")
        return v