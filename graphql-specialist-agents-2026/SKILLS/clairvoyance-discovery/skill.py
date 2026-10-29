# ruff: noqa: I001
"""clairvoyance-discovery -- hidden root-field discovery via "Did you mean" errors.

Usage (via the pack loader)::

    from common.loader import load_skill
    from common.transport import HttpTransport

    skill = load_skill("clairvoyance-discovery")
    result = skill.run(HttpTransport("http://127.0.0.1:4000/graphql"))
    # -> {"discovered": [{"field", "probable_type", "evidence"}...],
    #     "suggestions_enabled": bool, "findings": [...], "meta": {...}}

Technique: for each candidate word we probe a MUTATED spelling (append ``x``)
at the requested root type. Validation errors for a misspelled field carry
"Did you mean ...?" suggestions, and servers only ever suggest REAL fields --
so any suggestion harvested is guaranteed to exist. If a mutation itself
resolves with data, that name exists too (recorded as direct evidence).
Types are never claimed from suggestion errors (``probable_type`` stays
``None`` -- honest unknown).

Probe economy: batching is attempted first via ``execute_raw`` (one request
per ``batch_size`` words, default 25); if the server rejects list bodies, it
falls back to one request per word. ``max_probes`` caps REQUESTS, hard.
"""
import sys, pathlib
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import re
from typing import Any

from common.findings import new_finding
from common.transport import Transport

__all__ = ["DEFAULT_BATCH_SIZE", "DEFAULT_WORDLIST", "run"]

DEFAULT_BATCH_SIZE = 25

_DID_YOU_MEAN_RE = re.compile(
    r"Did you mean (?P<alts>(?:'[^']+'|\"[^\"]+\")"
    r"(?: or (?:'[^']+'|\"[^\"]+\"))*)\?"
)
_WORD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# ~120 common GraphQL root-field names (exact count exposed as len()).
DEFAULT_WORDLIST: list[str] = [
    "id", "user", "users", "me", "account", "accounts", "profile", "profiles",
    "username", "email", "password", "apiKey", "apiKeys", "token", "tokens",
    "accessToken", "refreshToken", "secret", "secrets", "admin", "admins",
    "internal", "debug", "config", "settings", "status", "health", "healthCheck",
    "version", "info", "meta", "data", "items", "item", "orders", "order",
    "products", "product", "posts", "post", "comments", "comment", "messages",
    "message", "threads", "thread", "notifications", "notification", "files",
    "file", "uploads", "upload", "documents", "document", "images", "image",
    "attachments", "attachment", "search", "node", "nodes", "edges",
    "connection", "page", "pageSize", "limit", "offset", "cursor", "total",
    "session", "sessions", "auth", "login", "logout", "register", "signup",
    "refresh", "verify", "reset", "invite", "invites", "role", "roles",
    "permission", "permissions", "group", "groups", "team", "teams", "member",
    "members", "organization", "org", "billing", "payment", "payments",
    "invoice", "invoices", "subscription", "subscriptions", "plan", "plans",
    "price", "prices", "customer", "customers", "report", "reports",
    "analytics", "metrics", "stats", "logs", "audit", "events", "event",
    "jobs", "task", "tasks", "cache", "storage", "webhook", "webhooks",
    "endpoint", "endpoints", "service", "services",
]


def _mutate(word: str) -> str:
    """Deterministic mutation: append 'x' (or 'y' when the word already ends in x)."""
    return word + ("y" if word.endswith("x") else "x")


def _suggestions(message: str) -> list[str]:
    match = _DID_YOU_MEAN_RE.search(message)
    if match is None:
        return []
    return [alt.strip("'\"") for alt in match.group("alts").split(" or ")]


def _error_messages(response: Any) -> list[str]:
    if not isinstance(response, dict) or not isinstance(response.get("errors"), list):
        return []
    return [str(err.get("message", "")) for err in response["errors"] if isinstance(err, dict)]


def _probe_query(word: str, root_type: str) -> str:
    keyword = "mutation" if root_type.lower().startswith("mut") else "query"
    return f"{keyword} Clairvoyance {{ {word} }}"


def run(
    transport: Transport,
    wordlist: list[str] | None = None,
    root_type: str = "Query",
    max_probes: int = 200,
    batch_size: int = DEFAULT_BATCH_SIZE,
    headers: dict | None = None,
) -> dict:
    """Discover hidden root fields from suggestion errors. Never exceeds max_probes requests."""
    words = list(DEFAULT_WORDLIST) if wordlist is None else [
        str(w) for w in wordlist if _WORD_RE.match(str(w))
    ]
    batch_size = max(1, int(batch_size))
    max_probes = max(0, int(max_probes))

    discovered: dict[str, dict] = {}
    probes_used = 0
    validation_errors_seen = 0
    suggestions_seen = 0
    batch_mode: bool | None = None
    probe_errors: list[str] = []
    # Real request/response of the most recent suggestion-bearing probe, kept
    # for the finding's evidence (the summary alone is synthesized, not raw).
    last_suggestion_probe: dict[str, Any] | None = None

    def record(field: str, evidence: str) -> None:
        if field and _WORD_RE.match(field) and field not in discovered:
            discovered[field] = {"field": field, "probable_type": None, "evidence": evidence}

    def harvest(word: str, response: Any) -> None:
        nonlocal validation_errors_seen, suggestions_seen, last_suggestion_probe
        messages = _error_messages(response)
        data = response.get("data") if isinstance(response, dict) else None
        if isinstance(data, dict) and data.get(word) is not None:
            # The mutated spelling itself resolved: this name really exists.
            record(word, f"mutated probe '{word}' returned data directly")
        for message in messages:
            lower = message.lower()
            if "cannot query field" in lower or "not found in type" in lower \
                    or "validation error" in lower:
                validation_errors_seen += 1
            for suggestion in _suggestions(message):
                suggestions_seen += 1
                last_suggestion_probe = {
                    "request": {
                        "query": _probe_query(_mutate(word), root_type),
                        "variables": None, "operation_name": None, "headers": headers,
                    },
                    "response": response,
                }
                record(suggestion, f"server suggestion in error: {message}")

    for chunk_start in range(0, len(words), batch_size):
        if probes_used >= max_probes:
            break
        chunk = words[chunk_start:chunk_start + batch_size]
        chunk = chunk[:max_probes - probes_used]  # hard probe cap
        if not chunk:
            break

        if batch_mode is not False:
            # Try (or continue) batched probing: one request per chunk.
            bodies = [
                {"query": _probe_query(_mutate(w), root_type), "operationName": None}
                for w in chunk
            ]
            probes_used += 1
            try:
                response = transport.execute_raw(bodies)
            except Exception as exc:  # noqa: BLE001 - transport/network failure, recorded never fabricated around
                probe_errors.append(f"batch probe failed: {type(exc).__name__}: {exc}")
                response = None
            if isinstance(response, list):
                batch_mode = True
                for word, entry in zip(chunk, response):
                    harvest(word, entry)
                continue
            if batch_mode is None:
                batch_mode = False

        # Single-request fallback: one request per word.
        for word in chunk:
            if probes_used >= max_probes:
                break
            probes_used += 1
            try:
                response = transport.execute(
                    _probe_query(_mutate(word), root_type), headers=headers
                )
            except Exception as exc:  # noqa: BLE001 - transport/network failure, recorded never fabricated around
                probe_errors.append(
                    f"probe '{word}' failed: {type(exc).__name__}: {exc}"
                )
                continue
            harvest(word, response)

    suggestions_enabled = suggestions_seen > 0
    notes = []
    if not words:
        notes.append("empty wordlist: nothing to probe")
    elif validation_errors_seen > 0 and not suggestions_enabled:
        notes.append("validation errors were observed but never carried suggestions; "
                     "field suggestions appear to be disabled")
    elif probes_used >= max_probes and len(discovered) == 0 and not validation_errors_seen:
        notes.append("probe budget exhausted before any usable response was observed")

    meta: dict[str, Any] = {
        "probes_used": probes_used,
        "max_probes": max_probes,
        "batch_mode": batch_mode,
        "wordlist_size": len(words),
        "root_type": root_type,
        "notes": notes,
        "suspicions": probe_errors,
    }

    findings: list[dict] = []
    if discovered:
        names = sorted(discovered)
        findings.append(new_finding(
            vuln_class="FIELD-SUGGESTIONS",
            seq=1,
            title=f"{len(names)} root field name(s) discovered via field suggestions",
            severity="info",
            confidence=0.9,
            target=str(getattr(transport, "url", "local-transport")),
            evidence={
                "request": {"query": _probe_query(_mutate(words[0]) if words else "x", root_type),
                            "variables": None, "operation_name": None, "headers": headers},
                "response": {"discovered_fields": names,
                             "sample_evidence": next(iter(discovered.values()))["evidence"]},
                # Raw server traffic from the last suggestion-bearing probe:
                # the summary above is synthesized; this pair is the real
                # request/response evidence behind it.
                "probe": last_suggestion_probe,
            },
            description=(
                "The endpoint returns 'Did you mean' suggestions for misspelled fields. "
                "Field enumeration is possible without introspection; the following "
                f"root field names on {root_type} were confirmed to exist: "
                + ", ".join(names[:25]) + ("..." if len(names) > 25 else "")
            ),
            impact="Attackers can map the schema even when introspection is disabled, "
                   "accelerating targeted abuse of sensitive or hidden operations.",
            proposed_fix={
                "summary": "Disable field suggestions in production, or gate them behind auth.",
                "config_or_code": (
                    "# Apollo Server (graphql-js >=16):\n"
                    "new ApolloServer({ schema, fieldResolverSuggestions: undefined, "
                    "validationRules: [], introspection: false, "
                    "formatError: () => ({ message: 'Invalid request' }) })\n"
                    "# graphql-core: build a custom error formatter that strips "
                    "'Did you mean' from validation messages."
                ),
                "language": "javascript/python",
                "references": [
                    "https://www.apollographql.com/docs/apollo-server/api/apollo-server/",
                    "https://github.com/graphql/graphw00f",
                ],
            },
            detection={
                "waf_rule": None,
                "log_query": None,
                "notes": "Look for validation errors containing 'Did you mean' in server logs.",
            },
        ))

    return {
        "discovered": list(discovered.values()),
        "suggestions_enabled": suggestions_enabled,
        "findings": findings,
        "meta": meta,
    }
