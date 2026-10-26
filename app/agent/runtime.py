from contextlib import contextmanager

from langgraph.checkpoint.postgres import PostgresSaver

from app.agent.graph import build_agent_graph
from app.core.config import settings


@contextmanager
def agent_with_memory():
    with PostgresSaver.from_conn_string(settings.checkpoint_database_url) as checkpointer:
        checkpointer.setup()
        yield build_agent_graph(checkpointer)