# app/rag/crag.py
import operator
from dataclasses import dataclass
from typing import Annotated, TypedDict

from langfuse import observe
from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.domain.retrieval import RetrievedChunk
from app.rag.grading import llm_grade, rewrite_for_search
from app.rag.retriever import retrieve


class CragState(TypedDict):
    question: str
    query: str
    chunks: list[RetrievedChunk]
    attempts: int
    verdict: str                              # good | retry | not_found
    trace: Annotated[list[str], operator.add]


def retrieve_node(state: CragState) -> dict:
    chunks = retrieve(state["query"], search_limit=15, rerank_limit=4)
    n = state["attempts"] + 1
    top = chunks[0].rerank_score if chunks else None
    return {"chunks": chunks, "attempts": n, "trace": [f"retrieve#{n} q={state['query']!r} top={top}"]}


@observe(name="grade")
def grade_node(state: CragState) -> dict:
    chunks = state["chunks"]
    top = chunks[0].rerank_score if chunks else None
    if not chunks:
        verdict, how = "retry", "empty"
    elif top is not None and top >= settings.crag_pass_score:
        verdict, how = "good", "score"
    elif top is not None and top < settings.crag_reject_score:
        verdict, how = "retry", "score"
    else:                                     # серая зона (или реранкер выключен)
        verdict, how = ("good" if llm_grade(state["question"], chunks) else "retry"), "llm"
    if verdict == "retry" and state["attempts"] >= settings.crag_max_attempts:
        verdict = "not_found"
    return {"verdict": verdict, "trace": [f"grade[{how}] top={top} -> {verdict}"]}


@observe(name="rewrite_for_search")
def rewrite_node(state: CragState) -> dict:
    new_query = rewrite_for_search(state["question"], state["query"])
    return {"query": new_query, "trace": [f"rewrite -> {new_query!r}"]}


def build_crag():
    builder = StateGraph(CragState)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("grade", grade_node)
    builder.add_node("rewrite", rewrite_node)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "grade")
    builder.add_conditional_edges("grade", lambda s: s["verdict"],
                                  {"good": END, "not_found": END, "retry": "rewrite"})
    builder.add_edge("rewrite", "retrieve")
    return builder.compile()


_CRAG = build_crag()   # граф неизменяемый: компилируем один раз


@dataclass
class CragResult:
    chunks: list[RetrievedChunk]
    found: bool
    attempts: int
    trace: list[str]


@observe(name="crag")
def corrective_retrieve(question: str) -> CragResult:
    state = _CRAG.invoke({"question": question, "query": question, "chunks": [],
                          "attempts": 0, "verdict": "", "trace": []})
    return CragResult(state["chunks"], state["verdict"] == "good", state["attempts"], state["trace"])