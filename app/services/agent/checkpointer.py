import asyncio
import threading
from typing import Any, Sequence
from psycopg_pool import ConnectionPool
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.base import (
    Checkpoint,
    CheckpointMetadata,
    ChannelVersions,
    CheckpointTuple,
)
from app.db.base import DATABASE_URL


class _AsyncPostgresSaver(PostgresSaver):
    """Bridges PostgresSaver's sync methods for LangGraph's async execution.

    PostgresSaver only implements sync checkpointer methods (get_tuple, put,
    put_writes). LangGraph's AsyncPregelLoop calls the async variants
    (aget_tuple, aput, aput_writes), which raise NotImplementedError on the
    base class. This wrapper delegates them to the sync implementations via
    a thread-pool executor.
    """

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_tuple, config)

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.put, config, checkpoint, metadata, new_versions,
        )

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.put_writes, config, writes, task_id, task_path,
        )


_checkpointer: _AsyncPostgresSaver | None = None
_setup_lock = threading.Lock()


def get_checkpointer() -> _AsyncPostgresSaver:
    global _checkpointer
    if _checkpointer is None:
        with _setup_lock:
            if _checkpointer is None:
                pool = ConnectionPool(
                    conninfo=DATABASE_URL,
                    min_size=1,
                    max_size=5,
                    kwargs={"autocommit": True, "prepare_threshold": 0},
                )
                _checkpointer = _AsyncPostgresSaver(pool)
                _checkpointer.setup()
    return _checkpointer


def close_checkpointer() -> None:
    global _checkpointer
    if _checkpointer is not None and hasattr(_checkpointer.conn, "close"):
        _checkpointer.conn.close()
        _checkpointer = None
