import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agent.history import repair_tool_pairs, trim_to_last_turns
from app.agent.manual_react import AgentResult
from app.agent.tools.registry import TOOLS, execute_tool
from app.core.clients import get_anthropic
from app.core.config import settings
from app.prompts.agent import SYSTEM_AGENT


class AgentState(TypedDict):
    messages: Annotated[list[dict], operator.add]
    stop_reason: str
    steps: Annotated[list[dict], operator.add]


def _text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text").strip()


def build_agent_graph(checkpointer=None):
    def agent_node(state: AgentState) -> dict:
        response = get_anthropic().messages.create(
            model=settings.anthropic_model,
            max_tokens=1500,
            system=SYSTEM_AGENT,
            tools=TOOLS,
            messages=repair_tool_pairs(trim_to_last_turns(state["messages"])),
        )
        if response.stop_reason != "tool_use":
            text = _text(response)
            return {
                "messages": [{"role": "assistant", "content": [{"type": "text", "text": text}]}],
                "stop_reason": response.stop_reason or "end_turn",
                "steps": [],
            }
        steps: list[dict] = []
        tool_results: list[dict] = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            output, is_error = execute_tool(block.name, block.input)
            steps.append({"tool": block.name, "input": block.input,
                          "is_error": is_error, "output_preview": output[:200]})
            tool_results.append({"type": "tool_result", "tool_use_id": block.id,
                                 "content": output, "is_error": is_error})
        assistant_content = [b.model_dump(exclude_none=True)
                             for b in response.content if b.type in ("text", "tool_use")]
        return {
            "messages": [{"role": "assistant", "content": assistant_content},
                         {"role": "user", "content": tool_results}],
            "stop_reason": "",
            "steps": steps,
        }

    def route(state: AgentState) -> str:
        return "end" if state["stop_reason"] else "agent"

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", route, {"agent": "agent", "end": END})
    return graph.compile(checkpointer=checkpointer)


def run_agent_graph(question: str, history: list[dict] | None = None) -> AgentResult:
    """Режим без збереження (День 24): вся історія передається явно, чекпоінтер не використовується."""
    messages = (history or []) + [{"role": "user", "content": question}]
    state = build_agent_graph().invoke({"messages": messages, "stop_reason": "", "steps": []})
    content = state["messages"][-1]["content"]
    answer = "".join(b["text"] for b in content if b["type"] == "text").strip()
    return AgentResult(answer=answer, steps=state.get("steps", []), stopped_by=state["stop_reason"])
