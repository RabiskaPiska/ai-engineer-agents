# EVIDENCE — GitHub research (verified 2026-10-29)

Method: GitHub REST API v3 (authenticated, PAT held in Windows Credential Manager) for
stars/forks/pushed-at; shields.io JSON badges as fallback when the anonymous IP quota was
exhausted. Every number below was read from a live response on 2026-10-29. Nothing is from memory.

## Verified (21)

| Repo | Stars | Forks | Last push | Why it matters for GraphQL testing |
|---|---|---|---|---|
| dolevf/graphw00f | 912 | 100 | 2026-05-16 | GraphQL engine fingerprinting (the reference tool) |
| nikitastupin/clairvoyance | 1548 | 138 | 2025-12-05 | Hidden-field discovery via "Did you mean" suggestions |
| doyensec/inql | 1812 | 190 | 2026-10-23 | GraphQL testing/scanner toolkit (Burp + CLI) |
| graphql-hive/graphql-inspector | 1768 | 218 | 2026-10-20 | Schema diffing/consistency checks |
| apollographql/apollo-server | 13956 | 2000 | 2026-10-28 | Reference server; depth/complexity limit middleware patterns |
| graphql/graphql-spec | 14592 | 1160 | 2026-09-28 | Spec: validation rules the abuse techniques bend |
| graphql/graphiql | 16924 | 1861 | 2026-10-27 | Reference client/introspection behavior |
| OWASP/CheatSheetSeries | 33788 | 4701 | 2026-10-28 | GraphQL cheat sheet: authz, depth, cost, introspection |
| swisskyrepo/PayloadsAllTheThings | 82187 | 17525 | 2026-08-27 | GraphQL payload section (aliases, batching, nesting) |
| facebook/dataloader | 13000 | 522 | shields-only | Batching pattern — the N+1 fix detectors test for |
| pa-bru/graphql-cost-analysis | 678 | 21 | 2023-01-04 | Query cost analysis middleware (defense reference) |
| strawberry-graphql/strawberry | 4724 | 676 | 2026-10-27 | Python server w/ built-in DataLoader (defense reference) |
| graphql-python/graphene | 8237 | 823 | 2025-09-04 | Python server ecosystem |
| mercurius-js/mercurius | 2493 | 256 | 2026-10-26 | Batching reference implementation (batch-abuse defense) |
| graph-gophers/graphql-go | 4754 | 501 | 2026-10-11 | Go server (cross-language resolver patterns) |
| hasura/graphql-engine | 32125 | 2971 | 2026-10-29 | Authz patterns at resolver level (BOLA defense reference) |
| grafbase/grafbase | 1227 | 75 | 2026-07-01 | GraphQL platform, limits configuration reference |
| dgraph-io/dgraph | 21815 | 1610 | 2026-10-29 | GraphQL-native database, @auth directive reference |
| graphql-compose/graphql-compose | 1212 | 75 | 2026-10-13 | Schema composition (introspection edge cases) |
| altair-graphql/altair | 5433 | 405 | 2026-10-23 | Client for manual reproduction of findings |
| graphql-kit/graphql-voyager | 8200 | 551 | shields-only | Schema visualization for reports |

## Rejected during verification (5)

| Candidate | Result |
|---|---|
| doyensec/clairvoyance | HTTP 404 — correct repo is nikitastupin/clairvoyance |
| InsiderPhD/graphw00f | HTTP 404 — correct owner is dolevf |
| 1NTheKut/GraphQLCop | HTTP 404 (also GraphQL-Cop variant) |
| tailcallhq/tailcall | HTTP 404 (moved/renamed; not re-located in budget) |
| 0xsha1n14/graphql-repeater | HTTP 404 — referenced in an earlier draft spec but does not exist |

Total: 26 candidates checked, 21 verified, 5 rejected. The original draft spec's claims
(4,200 stars for graphw00f; 3,800 for a doyensec clairvoyance) were fabricated — real
values are in the table above.
