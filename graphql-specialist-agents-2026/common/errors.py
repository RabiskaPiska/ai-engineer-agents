"""Retry helper + typed wrapper for GraphQL transport failures.

``retry`` only ever sleeps BETWEEN attempts (exponential backoff), never on
the first try and never after the final failure -- so fast test paths with
``backoff_s=0`` perform no sleeps at all.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

__all__ = ["GraphQLErrorEx", "retry"]

T = TypeVar("T")


class GraphQLErrorEx(Exception):
    """Rich wrapper around a GraphQL/transport failure.

    Attributes:
        message: human-readable failure description.
        status:  HTTP status code when known, else ``None``.
        payload: parsed response body (dict/list) when available, else ``None``.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        payload: dict | list | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.payload = payload


def retry(fn: Callable[[], T], attempts: int = 3, backoff_s: float = 1.0) -> T:
    """Call ``fn()`` up to ``attempts`` times with exponential backoff.

    Sleep ``backoff_s * 2**(attempt-1)`` between attempts only. On exhaustion,
    raise :class:`GraphQLErrorEx` chained from the last underlying exception
    (``__cause__`` keeps the original traceback). ``backoff_s <= 0`` disables
    sleeping entirely, which keeps test paths fast.
    """
    if attempts < 1:
        raise ValueError(f"attempts must be >= 1, got {attempts}")
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 -- deliberate: any failure is retryable
            last_exc = exc
            if attempt == attempts:
                break
            if backoff_s > 0:
                time.sleep(backoff_s * (2 ** (attempt - 1)))
    raise GraphQLErrorEx(
        f"retry exhausted after {attempts} attempt(s): {type(last_exc).__name__}: {last_exc}"
    ) from last_exc
