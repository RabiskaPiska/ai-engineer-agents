# GraphQL Specialist Agent — usage guide

Version: 1.0.0

The GraphQL Specialist Agent is the operator-facing persona of this pack: ten
skills, five MCP servers, one findings schema, one transport contract. This
guide covers how to drive it.

## What you need

- Python >= 3.10 with the pack installed (see `INSTALLERS/` at the repo root).
- A GraphQL endpoint you are **authorized** to test.
- For two-context BOLA testing: two sets of credentials or identity headers
  (on the demo target, two `X-User-ID` values, e.g. `u1` and `u2`).

## Quickstart against the demo target

```bash
# 1. Install (repo root)
bash INSTALLERS/install-linux.sh          # or install-macos.sh
source .venv/bin/activate                 # Windows: .venv\Scripts\Activate.ps1

# 2. Start the offline demo target
python examples/demo_target.py            # http://127.0.0.1:4000/graphql

# 3. Point a transport at it
```

```python
import sys; sys.path.insert(0, ".")       # repo root, once per script
from common.transport import HttpTransport
from common.loader import load_skill

t_a = HttpTransport("http://127.0.0.1:4000/graphql", headers={"X-User-ID": "u1"})
t_b = HttpTransport("http://127.0.0.1:4000/graphql", headers={"X-User-ID": "u2"})

# Fingerprint -> map -> BOLA
fp = load_skill("schema-fingerprinting").run(t_a)
sm = load_skill("introspection-enumeration").run(t_a)
# id_sample must be a REAL id on the target (demo ids are u1/u2/u3):
# identity A's own id is what B will be caught reading.
bola = load_skill("bola-idor-testing").run(t_a, t_b, sm["schema_map"], id_sample="u1")
print(bola["findings"])

# DoS-style probes (respect the caps)
# field="__typename" is the canonical alias probe: valid on any root type,
# scalar by definition (object-typed fields like "users" would need a
# subselection and are rejected as invalid probes).
ab = load_skill("alias-abuse-testing").run(t_a, field="__typename", n=100)
bb = load_skill("batch-abuse-testing").run(t_a, query="{ me { id } }", n=50)

# Report
report = load_skill("report-generation").generate(bola["findings"] + ab["findings"] + bb["findings"], fmt="markdown")
open("report.md", "w").write(report)
```

Expected output on the demo target: exactly **3 findings** —
`GQL-BOLA-1` (identity u2 reads user u1's record: `user(id:)` ignores
ownership), `GQL-ALIAS-ABUSE-1` (100 aliased `__typename` fields executed
with no alias limit), and `GQL-BATCH-ABUSE-1` (a 50-operation batch accepted
with no size limit) — and a `report.md` containing all three with full
request/response evidence.

With a `LocalTransport` (same `common.transport` module) the whole flow runs
offline against `examples.demo_target.build_demo_schema()` with no HTTP at
all — that is what the pytest suite does.

## Running the full agent workflow

`agent.md` is the binding workflow (fingerprint → map → BOLA → abuse probes
with caps → N+1 heuristic → report). Its thresholds live in `config.json`:
critical findings pause for operator review, confidence > 0.9 auto-reports,
confidence < 0.7 is flagged for manual verification.

## Standalone skills vs. MCP servers

- **Standalone skills** (`SKILLS/*/skill.py`) are plain Python:
  `load_skill(name).run(transport, ...)`. Use them directly in scripts and
  tests.
- **MCP servers** (`MCP_SERVERS/*/server.py`) expose the same capabilities
  over the Model Context Protocol for agent hosts: `graphql-mcp` for
  introspect/query/schema_map, `custom-api-mcp` for long-running test
  pipelines, `github-mcp` for reference lookups, `security-tools-mcp` for
  graphw00f/clairvoyance wrappers, `postgres-mcp` for read-only DB checks.
  Secrets come from env vars only (`GH_TOKEN`, `POSTGRES_URL`).

## Reading a finding

Every finding follows the pack schema (`common/findings.py`): id
(`GQL-<class>-<n>`), severity, confidence, target, timestamp, full
request/response evidence, description, impact, `proposed_fix`, and
`detection` notes. Nothing is fabricated: empty `findings` with honest
`meta` is a valid result. Unproven suspicions belong in `meta.suspicions`.

## Safety

- Authorized testing only — see the root README security note.
- DoS-style skills default to `max_ops=100` / `max_depth=20` and never exceed
  them unless you pass `aggressive=True` explicitly.
