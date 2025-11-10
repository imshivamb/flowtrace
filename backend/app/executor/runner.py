import asyncio, time
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, update, select
from app.schemas.workflow_schema import WorkflowSpec
from app.executor.compiler import compile_graph
from app.executor.tracing import emit_event
from app.executor.providers import call_llm
from app.models.workflow_runs import WorkflowRun
from app.models.run_steps import RunStep
from app.core.pricing import estimate_cost_cents

# Placeholder handlers (wire LLM/tools later)
async def handle_llm(db: AsyncSession, run_id: str, step_id: str, node, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Handle LLM node execution with real API calls"""
    # Get node config - update default to new model
    provider = node.config.get("provider", "openai")
    model = node.config.get("model", "gpt-5-fast")
    system = node.config.get("system", "")
    temperature = float(node.config.get("temperature", 0.0))
    
    # Render inputs (get prompt text)
    rendered_inputs = _render_inputs(node.inputs, ctx)
    prompt = rendered_inputs.get("text", "") if isinstance(rendered_inputs, dict) else str(rendered_inputs)
    
    # Emit request event
    await emit_event(db, run_id, step_id, "llm.request", {
        "provider": provider,
        "model": model,
        "system": system,
        "prompt": prompt
    })
    
    # Call LLM with fallback
    response_text, token_counts, provider_used = await call_llm(
        db=db,
        run_id=run_id,
        step_id=step_id,
        provider=provider,
        model=model,
        system=system,
        prompt=prompt,
        temperature=temperature
    )
    
    return {
        "output": response_text,
        "prompt_tokens": token_counts["input"],
        "completion_tokens": token_counts["output"],
        "provider": provider_used,
        "model": model,
    }

async def handle_tool(node, ctx) -> Dict[str, Any]:
    await asyncio.sleep(0.05)
    return {"output": {"ok": True, "echo": node.config}}

async def handle_router(node, ctx) -> Dict[str, Any]:
    # Extremely simple: compute len of provided text; set branch
    text = _render_inputs(node.inputs, ctx)
    rule = node.config.get("rule", "")
    branch = "deep" if len(str(text)) > 2000 else "shallow"
    return {"branch": branch, "output": branch}

def _render_inputs(inputs: Dict[str, Any], ctx: Dict[str, Any]) -> str:
    # minimal renderer: if there's a single key 'text', try basic template
    val = inputs.get("text", "")
    return str(_resolve_template(val, ctx))

def _resolve_template(template: str, ctx: Dict[str, Any]) -> str:
    # naive: allow {{node.<id>.output}} lookups only
    out = template
    # very simple resolve (not full mustache)
    for k, v in ctx.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out

async def execute_node(db: AsyncSession, run_id: str, node, ctx: Dict[str, Any]) -> None:
    # create step row
    step = await db.execute(insert(RunStep).values(
        run_id=run_id, node_id=node.id, node_type=node.type, status="running"
    ).returning(RunStep.id))
    step_id = str(step.scalar_one())
    await db.commit()

    t0 = time.perf_counter()
    try:
        await emit_event(db, run_id, step_id, "log", {"msg": f"start {node.type}:{node.id}"})
        if node.type == "llm":
            # Pass db, run_id, step_id to handle_llm
            result = await handle_llm(db, run_id, step_id, node, ctx)
            cost = estimate_cost_cents(result["provider"], result["model"], result["prompt_tokens"], result["completion_tokens"])
            ctx[f"node.{node.id}.output"] = result["output"]
            await db.execute(update(RunStep).where(RunStep.id==step_id).values(
                status="succeeded",
                latency_ms=int((time.perf_counter()-t0)*1000),
                tokens_input=result["prompt_tokens"],
                tokens_output=result["completion_tokens"],
                cost_cents=cost
            ))
            await emit_event(db, run_id, step_id, "llm.response", {
                "output": result["output"], 
                "tokens": (result["prompt_tokens"], result["completion_tokens"]), 
                "cost_cents": cost,
                "provider": result["provider"]
            })
        elif node.type == "tool":
            result = await handle_tool(node, ctx)
            ctx[f"node.{node.id}.output"] = result["output"]
            await db.execute(update(RunStep).where(RunStep.id==step_id).values(
                status="succeeded",
                latency_ms=int((time.perf_counter()-t0)*1000),
            ))
            await emit_event(db, run_id, step_id, "tool.response", {"output": result["output"]})
        elif node.type == "router":
            result = await handle_router(node, ctx)
            ctx["branch"] = result["branch"]
            ctx[f"node.{node.id}.output"] = result["output"]
            await db.execute(update(RunStep).where(RunStep.id==step_id).values(
                status="succeeded",
                latency_ms=int((time.perf_counter()-t0)*1000),
            ))
            await emit_event(db, run_id, step_id, "log", {"branch": result["branch"]})
        else:
            raise ValueError(f"unknown node type {node.type}")
        await db.commit()
    except Exception as e:
        await db.execute(update(RunStep).where(RunStep.id==step_id).values(
            status="failed",
            latency_ms=int((time.perf_counter()-t0)*1000),
            error=str(e)
        ))
        await db.commit()
        await emit_event(db, run_id, step_id, "log", {"error": str(e)})
        raise

async def run_workflow(db: AsyncSession, run_id: str, spec: WorkflowSpec) -> None:
    comp = compile_graph(spec)
    # mark run started
    await db.execute(update(WorkflowRun).where(WorkflowRun.id==run_id).values(status="running"))
    await db.commit()

    try:
        ctx: Dict[str, Any] = {}
        # execute level-by-level; within a level run concurrently
        for level in comp.levels:
            tasks = []
            for node_id in level:
                node = comp.nodes[node_id]
                tasks.append(asyncio.create_task(execute_node(db, run_id, node, ctx)))
            # wait a level
            for t in tasks:
                await t

        # compute totals (basic roll-up)
        from app.models.run_steps import RunStep
        q = await db.execute(select(RunStep.tokens_input, RunStep.tokens_output, RunStep.cost_cents).where(RunStep.run_id==run_id))
        tot_in = tot_out = tot_cost = 0
        for ti, to, cc in q.all():
            tot_in += ti or 0
            tot_out += to or 0
            tot_cost += cc or 0

        await db.execute(update(WorkflowRun).where(WorkflowRun.id==run_id).values(
            status="succeeded",
            total_tokens=tot_in + tot_out,
            total_cost_cents=tot_cost
        ))
        await db.commit()
        await emit_event(db, run_id, None, "log", {"msg": "run complete"})
    except Exception as e:
        await db.execute(update(WorkflowRun).where(WorkflowRun.id==run_id).values(status="failed", error_summary=str(e)))
        await db.commit()
        await emit_event(db, run_id, None, "log", {"msg": "run failed", "error": str(e)})
