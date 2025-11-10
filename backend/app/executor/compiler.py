from typing import Dict, List, Set, Tuple
from app.schemas.workflow_schema import WorkflowSpec, Node, Edge


class CompiledGraph:
    def __init__(self, spec: WorkflowSpec):
        self.spec = spec
        self.nodes: Dict[str, Node] = {n.id: n for n in spec.nodes}
        self.adj: Dict[str, List[str]] = {n.id: [] for n in spec.nodes}
        self.rev: Dict[str, List[str]] = {n.id: [] for n in spec.nodes}
        for e in spec.edges:
            self.adj[e.from_].append(e.to)
            self.rev[e.to].append(e.from_)
            
        self.levels: List[List[str]] = self._levels()
        
    def _levels(self) -> List[List[str]]:
        #Kahn's algorithm to compute topological levels
        indeg: Dict[str, int] = {n: len(self.rev[n]) for n in self.nodes}
        frontier: List[str] = sorted([n for n, d in indeg.items() if d == 0])
        levels: List[List[str]] = []
        seen: Set[str] = set()
        
        while frontier:
            lvl = frontier[:]
            levels.append(lvl)
            frontier = []
            for u in lvl:
                seen.add(u)
                for v in self.adj[u]:
                    indeg[v] -= 1
                    if indeg[v] == 0:
                        frontier.append(v)
                        
        if len(seen) != len(self.nodes):
            raise ValueError("Graph contains a cycle")
        return levels
    
def compile_graph(spec: WorkflowSpec) -> CompiledGraph:
    # Basic sanity: entry must have no incoming edges
    compiled = CompiledGraph(spec)
    return compiled