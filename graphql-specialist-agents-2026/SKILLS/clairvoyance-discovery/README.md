# clairvoyance-discovery

**Purpose.** Discover hidden/unlisted root field names using only
`"Did you mean"` validation-error suggestions — the classic "clairvoyance"
technique — when introspection is disabled. Works on `Query` or `Mutation`
roots.

## Usage

```python
from common.loader import load_skill
from common.transport import HttpTransport

skill = load_skill("clairvoyance-discovery")
result = skill.run(HttpTransport("http://127.0.0.1:4000/graphql"))
# custom wordlist / caps:
result = skill.run(transport, wordlist=["admin", "token", "internal"],
                   root_type="Query", max_probes=50)
```

## Return shape

```jsonc
{
  "discovered": [{"field": "admin", "probable_type": null, "evidence": "Did you mean \"admin\"? ..."}],
  "suggestions_enabled": false,
  "findings": [/* one info finding when something was discovered */],
  "meta": {"probes_used": 12, "max_probes": 200, "batch_mode": true,
            "wordlist_size": 120, "root_type": "Query", "notes": []}
}
```

## How it works

For each candidate word we probe a **mutated** spelling (append `x`) so the
server's validation error fires, then harvest every `"Did you mean"` suggestion.
Servers only suggest *real* fields, so any harvested name is guaranteed to
exist — that guarantee is why confidence is 0.9 and `probable_type` stays
`None` (types are never claimed from suggestion errors). If a mutated probe
itself resolves with data, that name is recorded as directly-existing.

**Probe economy:** batching is attempted first via `execute_raw` (list body,
25 ops per request → 1 request per 25 words). If the server rejects list
bodies, it falls back to 1 request per word. `max_probes` caps **requests**
(200 default) and is never exceeded.

Default wordlist: 126 common GraphQL root-field names (`id`, `user`, `users`,
`email`, `token`, `admin`, `password`, `secret`, `internal`, `apiKey`, ...).
See `DEFAULT_WORDLIST` in `skill.py`; `meta.wordlist_size` always reports the
exact count used.

## Honest limitations

- `suggestions_enabled: False` → `discovered` is empty; no fake results.
- Discovery depends on the server's suggestion distance metric: a misspelling
  can suggest a *different* similar field, and fields dissimilar to any
  mutated probe are never found. This is best-effort, not exhaustive.
- `batch_mode` probing is opportunistic; a server that unwraps batch bodies
  silently can distort per-op error mapping (we treat a non-list reply as
  "batch not supported" and switch to singles).
- Batching itself is a feature the target may rate-limit; heavy wordlists
  against production targets are the caller's responsibility.
