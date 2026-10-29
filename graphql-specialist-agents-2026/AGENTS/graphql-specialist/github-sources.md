# GitHub sources — live-verified 2026-10-29

All star/fork/push figures below were verified against the GitHub REST API on
**2026-10-29** by the pack orchestrator. Do not edit numbers without
re-verifying. Two entries marked "(stars shields-verified only)" had their
star count confirmed via shields.io badge verification rather than a REST
round-trip; treat their fork counts with the same caution.

## Reference repositories

| Repository | Stars | Forks | Last push | Why it matters for testing |
|---|---:|---:|---|---|
| [dolevf/graphw00f](https://github.com/dolevf/graphw00f) | 912 | 100 | 2026-05-16 | GraphQL engine fingerprinting — the reference implementation for identifying the backend behind an endpoint. |
| [nikitastupin/clairvoyance](https://github.com/nikitastupin/clairvoyance) | 1548 | 138 | 2025-12-05 | Recovers hidden GraphQL schema fields via "Did you mean" suggestion mining when introspection is disabled. |
| [doyensec/inql](https://github.com/doyensec/inql) | 1812 | 190 | 2026-10-23 | Doyensec's GraphQL testing toolkit — schema browsing, query generation, and attack surface workflows to mirror. |
| [graphql-hive/graphql-inspector](https://github.com/graphql-hive/graphql-inspector) | 1768 | 218 | 2026-10-20 | Schema diffing/consistency tooling — useful for tracking schema changes between test rounds. |
| [apollographql/apollo-server](https://github.com/apollographql/apollo-server) | 13956 | 2000 | 2026-10-28 | Reference server implementation; source of truth for depth-limit / cost / batching middleware behavior you will encounter. |
| [graphql/graphql-spec](https://github.com/graphql/graphql-spec) | 14592 | 1160 | 2026-09-28 | The spec — validation rules (aliases, fragments, depth semantics) that abuse queries bend without breaking. |
| [graphql/graphiql](https://github.com/graphql/graphiql) | 16924 | 1861 | 2026-10-27 | Reference client; confirms what a legitimate client sends so probes blend in. |
| [OWASP/CheatSheetSeries](https://github.com/OWASP/CheatSheetSeries) | 33788 | 4701 | 2026-10-28 | OWASP GraphQL cheat sheet — authorization, depth limiting, and cost analysis guidance for remediation write-ups. |
| [swisskyrepo/PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) | 82187 | 17525 | 2026-08-27 | Its GraphQL payload section is a quick source of probe queries (injection, batching, introspection bypasses). |
| [facebook/dataloader](https://github.com/facebook/dataloader) | 13000 | 522 | (stars shields-verified only) | The N+1 batching pattern — what a fixed resolver layer looks like, and how to detect its absence. |
| [pa-bru/graphql-cost-analysis](https://github.com/pa-bru/graphql-cost-analysis) | 678 | 21 | 2023-01-04 | Query cost analysis middleware — reference for the complexity/cost limits you probe and recommend. |
| [strawberry-graphql/strawberry](https://github.com/strawberry-graphql/strawberry) | 4724 | 676 | 2026-10-27 | Modern Python GraphQL server with built-in DataLoader; useful for Python-side fix examples. |
| [graphql-python/graphene](https://github.com/graphql-python/graphene) | 8237 | 823 | 2025-09-04 | Widely deployed Python GraphQL server; older codebases to test against often run it. |
| [mercurius-js/mercurius](https://github.com/mercurius-js/mercurius) | 2493 | 256 | 2026-10-26 | Batching reference implementation (query batching with configurable limits). |
| [graph-gophers/graphql-go](https://github.com/graph-gophers/graphql-go) | 4754 | 501 | 2026-10-11 | Go GraphQL server; broadens engine fingerprint signatures. |
| [hasura/graphql-engine](https://github.com/hasura/graphql-engine) | 32125 | 2971 | 2026-10-29 | Authorization patterns at the engine level (role-based permissions) — BOLA remediation reference. |
| [grafbase/grafbase](https://github.com/grafbase/grafbase) | 1227 | 75 | 2026-07-01 | Edge GraphQL federation platform; another fingerprint signature and limit-config surface. |
| [dgraph-io/dgraph](https://github.com/dgraph-io/dgraph) | 21815 | 1610 | 2026-10-29 | GraphQL-native graph database; distinct error/batching behavior worth fingerprinting. |
| [graphql-compose/graphql-compose](https://github.com/graphql-compose/graphql-compose) | 1212 | 75 | 2026-10-13 | Schema-composition toolkit; explains odd generated schemas you may meet in the wild. |
| [altair-graphql/altair](https://github.com/altair-graphql/altair) | 5433 | 405 | 2026-10-23 | Full-featured GraphQL client; second reference client for realistic request shapes. |
| [graphql-kit/graphql-voyager](https://github.com/graphql-kit/graphql-voyager) | 8200 | 551 | (stars shields-verified only) | Schema visualization — turn your `schema_map` into a graph for the report appendix. |

## Honest verification note

> 26 candidates checked (21 verified + 5 rejected); rejected during
> verification: doyensec/clairvoyance (404 — correct repo is nikitastupin/clairvoyance), InsiderPhD/graphw00f (404 — correct owner is dolevf), 1NTheKut/GraphQLCop (404), tailcallhq/tailcall (404), 0xsha1n14/graphql-repeater (404, referenced in an earlier draft spec but does not exist).
