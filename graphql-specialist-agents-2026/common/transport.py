"""Transport protocol shared by every skill in the pack (SPEC.md contract).

Three implementations ship here:

- :class:`HttpTransport`  -- real HTTP endpoint via ``httpx``.
- :class:`LocalTransport` -- in-process execution via ``graphql-core``.
- :class:`MapTransport`   -- canned dict responses for unit tests.

Every transport is STATELESS per call; auth/identity differences are expressed
as extra ``headers`` per call (e.g. ``{"X-User-ID": "u2"}``), never as transport
state.
"""
from __future__ import annotations

import copy
import json
import time
from typing import Any, Protocol, runtime_checkable

__all__ = ["HttpTransport", "LocalTransport", "MapTransport", "Transport"]


@runtime_checkable
class Transport(Protocol):
    """The one contract everything in the pack shares (SPEC.md)."""

    def execute(
        self,
        query: str,
        variables: dict | None = None,
        operation_name: str | None = None,
        headers: dict | None = None,
    ) -> dict:
        """Raw GraphQL JSON: ``{"data": ..., "errors": [...]}`` (errors may be absent)."""
        ...  # pragma: no cover

    def execute_raw(self, body: dict | list) -> dict | list:
        """POST an arbitrary JSON body (batch = list). Returns parsed JSON."""
        ...  # pragma: no cover


def _error_response(message: str, **extra: Any) -> dict:
    err: dict[str, Any] = {"message": message}
    err.update(extra)
    return {"data": None, "errors": [err]}


class HttpTransport:
    """HTTP JSON transport. Records ``.last_status`` and ``.last_elapsed_ms``."""

    def __init__(
        self,
        url: str,
        headers: dict | None = None,
        timeout_s: float = 30.0,
    ) -> None:
        self.url = url
        self.headers: dict[str, str] = {str(k): str(v) for k, v in (headers or {}).items()}
        self.timeout_s = float(timeout_s)
        self.last_status: int | None = None
        self.last_elapsed_ms: float | None = None

    def _merge_headers(self, headers: dict | None) -> dict[str, str]:
        merged = dict(self.headers)
        for key, value in (headers or {}).items():
            merged[str(key)] = str(value)
        return merged

    def _post(self, body: dict | list, headers: dict | None) -> dict:
        import httpx  # lazy: keeps LocalTransport/MapTransport importable without httpx

        start = time.perf_counter()
        self.last_status = None
        self.last_elapsed_ms = None
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                resp = client.post(
                    self.url,
                    json=body,
                    headers={"Content-Type": "application/json", **self._merge_headers(headers)},
                )
        except httpx.HTTPError as exc:
            self.last_elapsed_ms = (time.perf_counter() - start) * 1000.0
            return _error_response(f"transport error: {type(exc).__name__}: {exc}")
        self.last_status = resp.status_code
        self.last_elapsed_ms = (time.perf_counter() - start) * 1000.0
        try:
            parsed = resp.json()
        except ValueError:
            return _error_response(
                f"HTTP {resp.status_code}: non-JSON response",
                extensions={"http_status": resp.status_code},
            )
        if not isinstance(parsed, (dict, list)):
            return _error_response(
                f"HTTP {resp.status_code}: unexpected JSON payload type {type(parsed).__name__}"
            )
        return parsed

    def execute(
        self,
        query: str,
        variables: dict | None = None,
        operation_name: str | None = None,
        headers: dict | None = None,
    ) -> dict:
        body: dict[str, Any] = {"query": query}
        if variables is not None:
            body["variables"] = variables
        if operation_name is not None:
            body["operationName"] = operation_name
        result = self._post(body, headers)
        return result if isinstance(result, dict) else _error_response(
            "unexpected list payload for single operation"
        )

    def execute_raw(self, body: dict | list) -> dict | list:
        return self._post(body, None)


class LocalTransport:
    """In-process transport backed by ``graphql-core``'s ``graphql_sync``.

    ``execute_raw`` on a list executes each operation and returns a LIST of
    responses (batch accepted by construction). Errors are serialized to plain
    dicts via ``GraphQLError.formatted``.

    When ``context`` is a dict, per-call ``headers`` are merged into a shallow
    copy of the context under the ``"headers"`` key so resolvers can honor
    per-request identity (mirrors the HTTP header model).
    """

    def __init__(self, schema: Any, context: Any = None) -> None:
        self._schema_source = schema
        self._schema: Any = None
        self._context = context

    def _get_schema(self) -> Any:
        if self._schema is None:
            if isinstance(self._schema_source, str):
                from graphql import build_schema

                self._schema = build_schema(self._schema_source)
            else:
                self._schema = self._schema_source
        return self._schema

    def _run(self, query: str, variables: dict | None, operation_name: str | None,
             headers: dict | None) -> dict:
        from graphql import graphql_sync

        context = self._context
        if isinstance(context, dict):
            context = dict(context)
            if headers:
                context["headers"] = dict(headers)
        result = graphql_sync(
            self._get_schema(),
            query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=context,
        )
        response: dict[str, Any] = {}
        if result.data is not None or result.errors is None:
            response["data"] = result.data
        if result.errors:
            response["errors"] = [err.formatted for err in result.errors]
        return response

    def execute(
        self,
        query: str,
        variables: dict | None = None,
        operation_name: str | None = None,
        headers: dict | None = None,
    ) -> dict:
        return self._run(query, variables, operation_name, headers)

    def execute_raw(self, body: dict | list) -> dict | list:
        if isinstance(body, list):
            return [self._single(item) for item in body]
        return self._single(body)

    def _single(self, item: dict) -> dict:
        if not isinstance(item, dict) or "query" not in item:
            return _error_response("batch entry must be an object with a 'query' field")
        return self._run(
            str(item["query"]),
            item.get("variables") if isinstance(item.get("variables"), dict) else None,
            item.get("operationName") if isinstance(item.get("operationName"), str) else None,
            None,
        )


class MapTransport:
    """Canned-response transport for unit tests.

    ``mapping`` keys are exact query strings; values are response dicts (or
    callables ``(query, variables, operation_name, headers) -> dict`` for
    dynamic behavior). ``default`` (optional) answers queries with no exact
    match. Responses are deep-copied so callers cannot mutate the canned data.
    """

    def __init__(self, mapping: dict, default: dict | None = None) -> None:
        self._mapping = mapping
        self._default = default
        self.last_status: int | None = 200
        self.last_elapsed_ms: float | None = 0.0

    def _respond(self, query: Any, variables: Any, operation_name: Any, headers: Any) -> dict:
        value = self._mapping.get(query if isinstance(query, str) else "", self._default)
        if value is None:
            raise KeyError(f"MapTransport: no canned response for query: {str(query)[:80]!r}")
        if callable(value):
            return copy.deepcopy(value(query, variables, operation_name, headers))
        return copy.deepcopy(value)

    def execute(
        self,
        query: str,
        variables: dict | None = None,
        operation_name: str | None = None,
        headers: dict | None = None,
    ) -> dict:
        return self._respond(query, variables, operation_name, headers)

    def execute_raw(self, body: dict | list) -> dict | list:
        if isinstance(body, list):
            return [self._respond(b.get("query"), b.get("variables"),
                                  b.get("operationName"), None) for b in body]
        return self._respond(body.get("query"), body.get("variables"),
                             body.get("operationName"), None)


def dumps(obj: Any) -> str:
    """Stable JSON dump used for response-size accounting (shared helper)."""
    return json.dumps(obj, default=str, sort_keys=False)
