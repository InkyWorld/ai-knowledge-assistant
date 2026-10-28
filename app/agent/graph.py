import json
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agent.history import repair_tool_pairs, trim_to_last_turns
from app.agent.tools.registry import TOOLS, execute_tool
from app.core.clients import get_anthropic
from app.core.config import settings
from app.core.logs import logger
from app.prompts.agent import SYSTEM_AGENT


class AgentState(TypedDict):
    messages: Annotated[list[dict], operator.add]
    stop_reason: str
    steps: int
    tokens: int


def _to_param(block) -> dict:
    if block.type == "text":
        return {"type": "text", "text": block.text}
    return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}


def _current_turn(messages: list[dict]) -> list[dict]:
    starts = [i for i, m in enumerate(messages) if m["role"] == "user" and isinstance(m["content"], str)]
    return messages[starts[-1] :] if starts else messages


def _is_looping(messages: list[dict], window: int = 3) -> bool:
    calls = [
        (b["name"], json.dumps(b["input"], sort_keys=True, ensure_ascii=False))
        for m in _current_turn(messages)
        if m["role"] == "assistant" and not isinstance(m["content"], str)
        for b in m["content"]
        if b["type"] == "tool_use"
    ]
    return len(calls) >= window and len(set(calls[-window:])) == 1


def _limit_reason(state: AgentState) -> str | None:
    if state["steps"] >= settings.agent_max_steps:
        return "steps"
    if state["tokens"] >= settings.agent_max_tokens:
        return "tokens"
    if _is_looping(state["messages"]):
        return "loop"
    return None


def agent_node(state: AgentState) -> dict:
    window = repair_tool_pairs(trim_to_last_turns(state["messages"]))
    response = get_anthropic().messages.create(
        model=settings.anthropic_model,
        max_tokens=1500,
        system=SYSTEM_AGENT,
        tools=TOOLS,
        messages=window,
    )
    content = [_to_param(b) for b in response.content if b.type in ("text", "tool_use")]
    return {
        "messages": [{"role": "assistant", "content": content}],
        "stop_reason": response.stop_reason or "",
        "steps": state["steps"] + 1,
        "tokens": state["tokens"] + response.usage.input_tokens + response.usage.output_tokens,
    }


def tools_node(state: AgentState) -> dict:
    results = []
    for block in state["messages"][-1]["content"]:
        if block["type"] != "tool_use":
            continue
        output, is_error = execute_tool(block["name"], block["input"])
        item = {"type": "tool_result", "tool_use_id": block["id"], "content": output}
        if is_error:
            item["is_error"] = True
        results.append(item)
    return {"messages": [{"role": "user", "content": results}]}


def finalize_node(state: AgentState) -> dict:
    """limit reached: close dangling tool_use and ask for best answer without new tool calls."""
    reason = _limit_reason(state)
    logger.warning("agent limit reached: %s (steps=%s tokens=%s)", reason, state["steps"], state["tokens"])
    pending = [
        {
            "type": "tool_result",
            "tool_use_id": b["id"],
            "content": "Ліміт вичерпано, інструмент не виконано.",
            "is_error": True,
        }
        for b in state["messages"][-1]["content"]
        if b["type"] == "tool_use"
    ]
    closing = {
        "role": "user",
        "content": pending
        + [
            {
                "type": "text",
                "text": "Ліміт кроків вичерпано. Дай найкращу відповідь на основі вже зібраної інформації "
                "і чесно скажи, чого бракує. Не викликай інструменти.",
            }
        ],
    }
    response = get_anthropic().messages.create(
        model=settings.anthropic_model,
        max_tokens=800,
        system=SYSTEM_AGENT,
        tools=TOOLS,
        tool_choice={"type": "none"},
        messages=repair_tool_pairs(trim_to_last_turns(state["messages"] + [closing])),
    )
    text = (
        "".join(b.text for b in response.content if b.type == "text").strip() or "Не вдалося завершити за ліміт кроків."
    )
    return {
        "messages": [closing, {"role": "assistant", "content": [{"type": "text", "text": text}]}],
        "stop_reason": "limit",
    }


def route_after_agent(state: AgentState) -> str:
    if state["stop_reason"] != "tool_use":
        return END
    return "finalize" if _limit_reason(state) else "tools"


def build_agent_graph(checkpointer=None):
    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tools_node)
    builder.add_node("finalize", finalize_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "finalize": "finalize", END: END})
    builder.add_edge("tools", "agent")
    builder.add_edge("finalize", END)
    return builder.compile(checkpointer=checkpointer)


def new_turn_input(question: str) -> dict:
    """New message + reset counters (otherwise with checkpointer the limit will be "for the whole dialog")."""
    return {"messages": [{"role": "user", "content": question}], "stop_reason": "", "steps": 0, "tokens": 0}


def final_text(state: dict) -> str:
    return "".join(b["text"] for b in state["messages"][-1]["content"] if b["type"] == "text").strip()
