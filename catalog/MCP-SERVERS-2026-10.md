# MCP servers for AI-assisted software engineering (October 2026)

Catalog of 45 MCP servers that a language-expert engineer agent can use from **Claude Code** and **OpenCode**.
Built 2026-10-29 by C1. Scope covers general engineering servers (docs, VCS, semantic navigation, filesystem, browser
testing, sandboxes, databases, security, observability) and language-specific servers for the 10 pack slugs
(python, cpp, csharp, rust, javascript, typescript, go, java, kotlin, web). Skills, agent collections and the
per-language agent files are out of scope (sibling C2 and the language authors own them).

## How to read this catalog

- **Every repo was checked this session** with `ghapi.sh repos/<owner>/<repo>` (authenticated GitHub REST GET). The
  `verified` line in each entry is the raw output of that call, reduced to `full_name | stargazers_count | pushed_at |
  license.spdx_id | archived`. Stars and dates are as of 2026-10-29 (UTC). The full dump is in
  [Appendix A](#appendix-a-raw-github-verification-dump).
- **Freshness rule:** `pushed_at` in 2026 counts as live. Anything older is marked **STALE**.
- **Install lines** come from each project's own README or official docs page, read this session. Where a package
  version is quoted, it was read from the npm / PyPI / crates.io / NuGet registry API on 2026-10-29
  ([Appendix B](#appendix-b-package-registry-check)).
- **Remote endpoints** were probed with a single MCP `initialize` POST (no credentials). `200` means the server
  answered the handshake anonymously; `401` means it is live but needs OAuth or a token
  ([Appendix C](#appendix-c-remote-endpoint-probe)).
- Nothing here was installed or executed from a mined repo. "Works" claims are the vendors' claims unless the
  probe column says otherwise. Anything not verified in this session is marked `[UNVERIFIED]`.
- Secrets: every token below is a placeholder (`YOUR_...`, `${VAR}`, `{env:VAR}`). Never commit real values.

### Config formats used below (both verified 2026-10-29)

**Claude Code** (source: `https://code.claude.com/docs/en/mcp.md`). Three equivalent ways:

```bash
claude mcp add --transport http <name> <url>                 # remote (HTTP; falls back to SSE automatically)
claude mcp add <name> --env KEY=value -- <command> [args...]  # local stdio
claude mcp add-json <name> '<json entry>'                     # paste one entry
```

Project file `.mcp.json` (commit it to share with the team):

```json
{ "mcpServers": {
    "remote-one": { "type": "http", "url": "https://example.com/mcp",
                    "headers": { "Authorization": "Bearer ${MY_TOKEN}" } },
    "local-one":  { "type": "stdio", "command": "npx", "args": ["-y", "some-mcp@latest"],
                    "env": { "KEY": "${KEY}" } } } }
```

Two rules from the docs that bite people: an entry with a `url` but no `type` is read as stdio and is **skipped
with an error**, so always write `"type": "http"`; and `${VAR}` / `${VAR:-default}` is expanded in `.mcp.json`.
The same entry shape works **inline in a subagent's `mcpServers:` frontmatter** (per the pinned SPEC):

```yaml
mcpServers:
  - github                       # by-name reference to a server already configured
  - context7:                    # inline definition, same schema as a .mcp.json entry
      type: http
      url: https://mcp.context7.com/mcp
```

**OpenCode** (source: `https://opencode.ai/docs/mcp-servers/`; repo `sst/opencode` now redirects to
`anomalyco/opencode`, 222,892 stars, pushed 2026-10-29). Config lives in `opencode.json(c)` under `"mcp"`:

```jsonc
{ "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "local-one":  { "type": "local",  "command": ["npx", "-y", "some-mcp@latest"],
                    "environment": { "KEY": "{env:KEY}" }, "enabled": true },
    "remote-one": { "type": "remote", "url": "https://example.com/mcp",
                    "headers": { "Authorization": "Bearer {env:MY_TOKEN}" }, "oauth": false } } }
```

OpenCode handles OAuth for remote servers automatically (`opencode mcp auth <name>`); set `"oauth": false` when you
authenticate with a static header instead. Both clients warn that every server's tool list costs context, so
load only the servers an agent needs. GitHub's server in particular is large (see its entry).

In the entries below, **CC** = Claude Code, **OC** = OpenCode (the object that goes inside `"mcp": { ... }`).

---

## 1. Documentation and knowledge lookup

Ranked by usefulness for an engineer agent writing code against real, current APIs.

### 1.1 Context7 (upstash/context7) — current library docs by version

- Repo: https://github.com/upstash/context7 · 63,881 stars · pushed 2026-10-28 · MIT · transport: remote HTTP (also npm `@upstash/context7-mcp` 4.4.4 for stdio)
- verified: `upstash/context7 | 63881 | 2026-10-28T20:26:24Z | MIT | -`
- Probe: `https://mcp.context7.com/mcp` → **200** anonymous handshake.
- CC: `claude mcp add --transport http context7 https://mcp.context7.com/mcp` (add `--header "Authorization: Bearer YOUR_CONTEXT7_KEY"` for higher rate limits; README: "API Key Recommended", free at context7.com/dashboard). Vendor one-shot: `npx ctx7 setup --claude` (needs Node 22.13+; can install a skill instead of MCP).
- OC: `"context7": { "type": "remote", "url": "https://mcp.context7.com/mcp" }` (or `npx ctx7 setup --opencode`).
- Good for: `resolve-library-id` + `query-docs` returns version-matched docs and snippets for thousands of libraries (React, Next.js, Django, Spring, Tokio...). The default first call for any "how do I use library X" question.
- Caveats: community-submitted library index, so coverage and freshness vary per library; cite the doc version it returns. Anonymous use is rate-limited.

### 1.2 Microsoft Learn MCP (MicrosoftDocs/mcp) — official .NET / Azure / C# docs

- Repo: https://github.com/MicrosoftDocs/mcp · 1,958 stars · pushed 2026-10-25 · CC-BY-4.0 (docs repo) · remote HTTP
- verified: `MicrosoftDocs/mcp | 1958 | 2026-10-25T04:04:28Z | CC-BY-4.0 | -`
- Probe: `https://learn.microsoft.com/api/mcp` → **200** anonymous.
- CC: `claude mcp add --transport http microsoft-learn https://learn.microsoft.com/api/mcp`
- OC: `"microsoft-learn": { "type": "remote", "url": "https://learn.microsoft.com/api/mcp" }`
- Good for: searching and fetching first-party docs and code samples for .NET, C#, ASP.NET Core, EF Core, Azure SDKs. The authoritative docs source for the **csharp** agent.
- Caveats: the repo holds docs and config only (server is Microsoft-hosted, closed). README also offers a CLI-first mode (`@microsoft/learn-cli`) that skips MCP.

### 1.3 MDN MCP (mdn/mcp) — web platform docs + browser-compat data

- Repo: https://github.com/mdn/mcp · 193 stars · pushed 2026-10-26 · MPL-2.0 · remote HTTP (self-hostable)
- verified: `mdn/mcp | 193 | 2026-10-26T12:05:39Z | MPL-2.0 | -`
- Probe: `https://mcp.mdn.mozilla.net/` → **200** anonymous (`serverInfo.name: "mdn"`).
- CC: `claude mcp add --transport http mdn https://mcp.mdn.mozilla.net/` (exact line from MDN's page and README)
- OC: `"mdn": { "type": "remote", "url": "https://mcp.mdn.mozilla.net/" }`
- Good for: MDN search, page content and Baseline/BCD compatibility ("is `@view-transition` widely available?"). The primary docs server for the **web**, **javascript** and **typescript** agents.
- Caveats: MDN labels it **experimental, may be withdrawn**; query data is retained during the experiment (opt out of first-party analytics with header `X-Moz-1st-Party-Data-Opt-Out: 1`).

### 1.4 GitMCP (idosal/git-mcp) — docs for any GitHub repo, no install

- Repo: https://github.com/idosal/git-mcp · 8,495 stars · pushed 2026-05-08 · Apache-2.0 · remote HTTP
- verified: `idosal/git-mcp | 8495 | 2026-05-08T14:21:24Z | Apache-2.0 | -`
- Probe: `https://gitmcp.io/microsoft/playwright-mcp` → **200** (`serverInfo.name: GitMCP...`).
- CC: `claude mcp add --transport http <name> https://gitmcp.io/<owner>/<repo>` (generic endpoint: `https://gitmcp.io/docs`)
- OC: `"gitmcp-<repo>": { "type": "remote", "url": "https://gitmcp.io/<owner>/<repo>" }`
- Good for: pointing an agent at one library's README / llms.txt / docs folder when Context7 lacks it (niche crates, internal-looking OSS).
- Caveats: last push May 2026 (live but slowing); quality depends on the target repo's docs; public repos only.

### 1.5 Ref (ref-tools/ref-tools-mcp) — token-efficient docs search

- Repo: https://github.com/ref-tools/ref-tools-mcp · 1,184 stars · pushed 2026-10-24 · MIT · remote HTTP (recommended) or legacy stdio
- verified: `ref-tools/ref-tools-mcp | 1184 | 2026-10-24T00:25:58Z | MIT | -`
- Probe: `https://api.ref.tools/mcp` → **401** (needs API key).
- CC: `.mcp.json` → `"Ref": { "type": "http", "url": "https://api.ref.tools/mcp?apiKey=${REF_API_KEY}" }`
- OC: `"ref": { "type": "remote", "url": "https://api.ref.tools/mcp?apiKey={env:REF_API_KEY}", "oauth": false }`
- Good for: docs search that returns only the relevant section, to save context on long agent runs; also indexes private docs on paid plans.
- Caveats: commercial service (free tier, then paid). The repo itself says it "contains the legacy stdio server"; npm `ref-tools-mcp` was last published 2025-11-04, so prefer the remote endpoint.

### 1.6 Fetch (modelcontextprotocol/servers → src/fetch) — URL to markdown

- Repo: https://github.com/modelcontextprotocol/servers/tree/main/src/fetch · 91,658 stars (monorepo) · pushed 2026-10-29 · license transition MIT → Apache-2.0 (GitHub reports NOASSERTION) · stdio
- verified: `modelcontextprotocol/servers | 91658 | 2026-10-29T05:27:40Z | NOASSERTION | -`; PyPI `mcp-server-fetch` 2026.10.28 (2026-10-28)
- CC: `claude mcp add fetch -- uvx mcp-server-fetch`
- OC: `"fetch": { "type": "local", "command": ["uvx", "mcp-server-fetch"] }`
- Good for: reading a changelog, RFC or migration guide the docs servers do not cover, for agents in clients without a built-in fetch tool (OpenCode and Claude Code both have one, so this is optional).
- Caveats: reference implementation; the reference repo's LICENSE explains the MIT → Apache-2.0 transition. Fetched pages are untrusted input (prompt-injection surface).

---

## 2. Code hosting and version control

### 2.1 GitHub MCP Server (github/github-mcp-server) — official

- Repo: https://github.com/github/github-mcp-server · 34,054 stars · pushed 2026-10-29 · MIT · remote HTTP (recommended) or local Docker stdio
- verified: `github/github-mcp-server | 34054 | 2026-10-29T05:42:25Z | MIT | -`
- Probe: `https://api.githubcopilot.com/mcp/` → **401** "missing required Authorization header" (live, needs PAT or OAuth).
- CC (from `docs/installation-guides/install-claude.md`): `claude mcp add-json github '{"type":"http","url":"https://api.githubcopilot.com/mcp","headers":{"Authorization":"Bearer '"$GITHUB_PAT"'"}}'` · local: `claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=YOUR_GITHUB_PAT -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server`
- OC (from `docs/installation-guides/install-opencode.md`): `"github": { "type": "remote", "url": "https://api.githubcopilot.com/mcp/", "enabled": true, "oauth": false, "headers": { "Authorization": "Bearer {env:GITHUB_PERSONAL_ACCESS_TOKEN}" } }`
- Good for: issues, PRs, reviews, code search, Actions runs, releases, secret scanning, without shelling out to `gh`. Every language agent can reference it by name.
- Caveats: very large tool surface. Both GitHub's OpenCode guide and OpenCode's docs warn it can exceed the context limit; restrict with the `X-MCP-Toolsets` header (remote) or `--toolsets` (local). Use a fine-grained, least-privilege PAT.

### 2.2 Git (modelcontextprotocol/servers → src/git) — local repo operations

- Repo: https://github.com/modelcontextprotocol/servers/tree/main/src/git · (monorepo, see 1.6) · stdio
- verified: `modelcontextprotocol/servers | 91658 | 2026-10-29T05:27:40Z | NOASSERTION | -`; PyPI `mcp-server-git` 2026.10.28 (2026-10-28)
- CC: `claude mcp add git -- uvx mcp-server-git --repository "$(pwd)"`
- OC: `"git": { "type": "local", "command": ["uvx", "mcp-server-git", "--repository", "."] }`
- Good for: structured `git status/diff/log/show/branch/commit` results for clients or sandboxes where raw shell is disabled.
- Caveats: redundant when the agent has a Bash tool. It can commit; gate it with permissions in shared repos.

### 2.3 git-mcp-server (cyanheads/git-mcp-server) — fuller Git toolset

- Repo: https://github.com/cyanheads/git-mcp-server · 243 stars · pushed 2026-09-26 · Apache-2.0 · stdio (also HTTP)
- verified: `cyanheads/git-mcp-server | 243 | 2026-09-26T21:23:28Z | Apache-2.0 | -`; npm `@cyanheads/git-mcp-server` 2.15.3 (2026-08-24)
- CC: `claude mcp add git-plus -- npx -y @cyanheads/git-mcp-server@latest`
- OC: `"git-plus": { "type": "local", "command": ["npx", "-y", "@cyanheads/git-mcp-server@latest"] }`
- Good for: worktrees, rebase, cherry-pick, stash, tags, blame, as typed tools (needs Node 20+).
- Caveats: single-maintainer project; write-capable. Pick either 2.2 or 2.3, not both.

---

## 3. Semantic code navigation (LSP bridges, code search, IDE)

Ranked: for multi-language repos Serena is the strongest general choice; for one language prefer that language's
own server (section 9) or a thin LSP bridge.

### 3.1 Serena (oraios/serena) — symbol-level retrieval and editing across 40+ languages

- Repo: https://github.com/oraios/serena · 30,833 stars · pushed 2026-10-28 · **GPL-3.0-or-later** for the app (SolidLSP part is MIT; GitHub shows NOASSERTION) · stdio (or HTTP)
- verified: `oraios/serena | 30833 | 2026-10-28T10:45:55Z | NOASSERTION | -`; PyPI `serena-agent` 2.1.0 (2026-10-19)
- Install (README "Quick Start"; README warns **not** to install via MCP marketplaces): `uv tool install -p 3.13 serena-agent && serena init`
- CC (from `docs/02-usage/030_clients.md`): `claude mcp add --scope user serena -- serena start-mcp-server --context claude-code --project-from-cwd`
- OC (docs recommend the `ide` context for other agents): `"serena": { "type": "local", "command": ["serena", "start-mcp-server", "--context", "ide", "--project-from-cwd"] }`
- Good for: `find_symbol`, references, symbol-scoped replace/insert, rename, memories; strongest on large codebases where grep plus whole-file reads waste context. Supports Python, C/C++, C#, Rust, JS/TS, Go, Java, Kotlin, HTML/CSS/SCSS and more via language servers.
- Caveats: GPL-3.0 matters if you redistribute it inside a product. Some languages need the language server installed separately. The JetBrains backend is a paid plugin. It ships optional Claude Code hooks; review them before enabling.

### 3.2 mcp-language-server (isaacphi/mcp-language-server) — thin bridge to any LSP

- Repo: https://github.com/isaacphi/mcp-language-server · 1,611 stars · pushed 2026-03-01 · BSD-3-Clause · stdio
- verified: `isaacphi/mcp-language-server | 1611 | 2026-03-01T23:27:09Z | BSD-3-Clause | -`
- Install: `go install github.com/isaacphi/mcp-language-server@latest`
- CC (args from README; one server per language):
  - Go: `claude mcp add lsp-go -- mcp-language-server --workspace "$(pwd)" --lsp gopls`
  - Rust: `claude mcp add lsp-rust -- mcp-language-server --workspace "$(pwd)" --lsp rust-analyzer`
  - Python: `claude mcp add lsp-py -- mcp-language-server --workspace "$(pwd)" --lsp pyright-langserver -- --stdio`
  - TypeScript: `claude mcp add lsp-ts -- mcp-language-server --workspace "$(pwd)" --lsp typescript-language-server -- --stdio`
  - C/C++: `claude mcp add lsp-cpp -- mcp-language-server --workspace "$(pwd)" --lsp clangd -- --compile-commands-dir=build`
- OC: `"lsp-ts": { "type": "local", "command": ["mcp-language-server", "--workspace", ".", "--lsp", "typescript-language-server", "--", "--stdio"] }`
- Good for: definition, references, hover, diagnostics, rename on exactly one language server, with very little overhead.
- Caveats: last push March 2026, slower cadence. The workspace path must be absolute in some clients. OpenCode also has native LSP support (`opencode.ai/docs/lsp`), so this matters mostly for Claude Code.

### 3.3 mcpls (bug-ops/mcpls) — Rust-native universal MCP-to-LSP bridge

- Repo: https://github.com/bug-ops/mcpls · 80 stars · pushed 2026-10-28 · Apache-2.0 · stdio (optional HTTP)
- verified: `bug-ops/mcpls | 80 | 2026-10-28T21:48:33Z | Apache-2.0 | -`; crate `mcpls` 0.8.0 (2026-10-20)
- Install: `cargo install mcpls` (plus a language server, e.g. `rustup component add rust-analyzer`)
- CC: `claude mcp add --scope user mcpls -- mcpls` (README: "Rust projects need no configuration")
- OC: `"mcpls": { "type": "local", "command": ["mcpls"] }`
- Good for: hover/type info, references, implementations, call and type hierarchies, real compiler diagnostics, several language servers at once; has an untrusted-workspace mode. Single binary, no `unsafe`.
- Caveats: young project (80 stars). Non-Rust languages need a config file (see its book).

### 3.4 agent-lsp (blackwell-systems/agent-lsp) — LSP orchestration with workflow tools

- Repo: https://github.com/blackwell-systems/agent-lsp · 166 stars · pushed 2026-10-29 · MIT · stdio (Docker images per language)
- verified: `blackwell-systems/agent-lsp | 166 | 2026-10-29T04:51:07Z | MIT | -`
- Install: `go install github.com/blackwell-systems/agent-lsp/cmd/agent-lsp@latest` then `agent-lsp init` (writes the client config)
- CC (`.mcp.json` shape the README generates): `"lsp": { "type": "stdio", "command": "agent-lsp", "args": ["go:gopls", "typescript:typescript-language-server,--stdio", "python:pyright-langserver,--stdio"] }`
- OC: `"lsp": { "type": "local", "command": ["agent-lsp", "go:gopls", "typescript:typescript-language-server,--stdio", "python:pyright-langserver,--stdio"] }`
- Good for: polyglot repos that want one server with many LSPs and higher-level tools (README claims 65 tools).
- Caveats: small project; `init --with-skills` writes into `~/.claude/skills/`, so review before running. A large tool count costs context.

### 3.5 Claude Context (zilliztech/claude-context) — semantic (vector) code search

- Repo: https://github.com/zilliztech/claude-context · 12,658 stars · pushed 2026-07-14 · MIT · stdio
- verified: `zilliztech/claude-context | 12658 | 2026-07-14T12:00:38Z | MIT | -`; npm `@zilliz/claude-context-mcp` 0.1.15 (2026-06-22)
- CC (README): `claude mcp add claude-context -e OPENAI_API_KEY=YOUR_KEY -e MILVUS_ADDRESS=YOUR_ENDPOINT -e MILVUS_TOKEN=YOUR_TOKEN -- npx @zilliz/claude-context-mcp@latest`
- OC: `"claude-context": { "type": "local", "command": ["npx", "-y", "@zilliz/claude-context-mcp@latest"], "environment": { "OPENAI_API_KEY": "{env:OPENAI_API_KEY}", "MILVUS_ADDRESS": "{env:MILVUS_ADDRESS}", "MILVUS_TOKEN": "{env:MILVUS_TOKEN}" } }`
- Good for: "where is the retry logic for payments?" style natural-language search over very large monorepos.
- Caveats: needs an embedding provider and a Milvus/Zilliz vector DB, and **ships code to the embedding API**, so check data policy first. Index must be rebuilt as code changes. Last npm release June 2026.

### 3.6 JetBrains IDE built-in MCP server (IntelliJ IDEA, PyCharm, GoLand, Rider, CLion, WebStorm, Android Studio)

- Repo: the old standalone proxy https://github.com/JetBrains/mcp-jetbrains · 963 stars · pushed 2026-01-07 · Apache-2.0 · **README: "Deprecated ... integrated into all IntelliJ-based IDEs since version 2025.2"**
- verified: `JetBrains/mcp-jetbrains | 963 | 2026-01-07T16:21:45Z | Apache-2.0 | -` (kept only as provenance; the live server ships inside the IDE)
- Docs: https://www.jetbrains.com/help/idea/mcp-server.html (IntelliJ IDEA 2026.2 Help, read 2026-10-29): Settings | Tools | MCP Server → Enable → **Auto-Configure** for Claude Code, or copy the **SSE / Stdio / HTTP Stream** config for other clients.
- CC: use the IDE's Auto-Configure button for Claude Code. The port starts at 64342 and is not user-configurable (JetBrains KB SUPPORT-A-3223). Exact URL path of the HTTP endpoint: copy it from the IDE `[UNVERIFIED: not reproduced here]`.
- OC: paste the IDE's "Copy HTTP Stream Config" URL as `"jetbrains": { "type": "remote", "url": "<url copied from IDE>" }` (or the Stdio config as `type: local`).
- Good for: **java** and **kotlin** (and Android) where IntelliJ's indexing, inspections, refactorings, run configurations and debugger beat any open LSP; also Rider for C#.
- Caveats: the IDE must be running with the project open; "brave mode" lets clients run shell commands without confirmation, so leave it off. Not usable headless in CI.

### 3.7 Filesystem (modelcontextprotocol/servers → src/filesystem) — sandboxed file access

- Repo: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem · (monorepo) · stdio
- verified: `modelcontextprotocol/servers | 91658 | 2026-10-29T05:27:40Z | NOASSERTION | -`; npm `@modelcontextprotocol/server-filesystem` 2.1.0 (2026-10-28)
- CC: `claude mcp add fs -- npx -y @modelcontextprotocol/server-filesystem "$(pwd)"`
- OC: `"fs": { "type": "local", "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/abs/path/to/project"] }`
- Good for: giving a restricted or sandboxed agent read/write to allow-listed directories only.
- Caveats: redundant in Claude Code and OpenCode, which have native file tools; useful mainly for locked-down subagents. README says Node.js 24+ when run through npx.

---

## 4. Browser, UI and device testing

### 4.1 Playwright MCP (microsoft/playwright-mcp) — browser automation through accessibility snapshots

- Repo: https://github.com/microsoft/playwright-mcp · 38,797 stars · pushed 2026-10-22 · Apache-2.0 · stdio (also HTTP)
- verified: `microsoft/playwright-mcp | 38797 | 2026-10-22T17:43:26Z | Apache-2.0 | -`; npm `@playwright/mcp` 0.0.83 (2026-09-28)
- CC (README): `claude mcp add playwright npx @playwright/mcp@latest` (add `--headless --isolated` for CI or parallel agents)
- OC (README "opencode" block): `"playwright": { "type": "local", "command": ["npx", "@playwright/mcp@latest"], "enabled": true }`
- Good for: driving real Chromium/Firefox/WebKit, end-to-end checks of a feature, form flows, reproducing UI bugs; snapshots are structured text, not pixels.
- Caveats: still `0.0.x`; the persistent profile can be used by one client at a time, so pass `--isolated` per parallel agent. Pages are untrusted input.

### 4.2 Chrome DevTools MCP (ChromeDevTools/chrome-devtools-mcp) — performance, network, console

- Repo: https://github.com/ChromeDevTools/chrome-devtools-mcp · 54,394 stars · pushed 2026-10-29 · Apache-2.0 · stdio
- verified: `ChromeDevTools/chrome-devtools-mcp | 54394 | 2026-10-29T09:31:38Z | Apache-2.0 | -`; npm `chrome-devtools-mcp` 1.12.0 (2026-10-22)
- CC: `claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest --no-usage-statistics` (or `/plugin marketplace add ChromeDevTools/chrome-devtools-mcp`, then `/plugin install chrome-devtools-mcp@chrome-devtools-plugins`)
- OC: `"chrome-devtools": { "type": "local", "command": ["npx", "-y", "chrome-devtools-mcp@latest", "--no-usage-statistics"] }`
- Good for: performance traces and insights (LCP/INP/CLS), Lighthouse audits, network request inspection, console errors, heap snapshots. Complements Playwright: use DevTools to diagnose, Playwright to script flows.
- Caveats: **Google usage statistics are on by default**; opt out with `--no-usage-statistics` or the `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS` env var. Needs current Chrome and Node LTS.

### 4.3 Next.js DevTools MCP (vercel/next-devtools-mcp)

- Repo: https://github.com/vercel/next-devtools-mcp · 834 stars · pushed 2026-09-15 · MIT (from the npm `license` field; the repo has no LICENSE file, so GitHub reports none) · stdio
- verified: `vercel/next-devtools-mcp | 834 | 2026-09-15T00:32:28Z | None | -`; npm `next-devtools-mcp` 0.4.0 (2026-06-24)
- CC (README): `claude mcp add next-devtools npx next-devtools-mcp@latest`
- OC: `"next-devtools": { "type": "local", "command": ["npx", "-y", "next-devtools-mcp@latest"] }`
- Good for: Next.js 16+ apps: connects to the running dev server for build/runtime errors and routes, points the agent at the version-matched docs bundled in `node_modules/next/dist/docs/`, and guides upgrades (`npx @next/codemod@latest upgrade latest`).
- Caveats: Next.js only; 0.x; it does **not** fetch docs itself.

### 4.4 shadcn MCP (shadcn-ui/ui, built into the `shadcn` CLI)

- Repo: https://github.com/shadcn-ui/ui · 126,870 stars · pushed 2026-10-29 · MIT · stdio
- verified: `shadcn-ui/ui | 126870 | 2026-10-29T08:19:27Z | MIT | -`; npm `shadcn` 4.23.0 (2026-10-27)
- CC (ui.shadcn.com/docs/mcp): `npx shadcn@latest mcp init --client claude`, or `.mcp.json` → `"shadcn": { "command": "npx", "args": ["shadcn@latest", "mcp"] }`
- OC: `npx shadcn@latest mcp init --client opencode`, or `"shadcn": { "type": "local", "command": ["npx", "shadcn@latest", "mcp"] }`
- Good for: React/Tailwind front ends: search, view and install components and blocks from the shadcn registry and any namespaced registry in `components.json`.
- Caveats: React-centric. Third-party registries are untrusted code that it installs into your repo. Do not confuse it with shadcn.io's paid, unofficial MCP.

### 4.5 Mobile MCP (mobile-next/mobile-mcp) — Android / iOS device and emulator automation

- Repo: https://github.com/mobile-next/mobile-mcp · 10,102 stars · pushed 2026-10-26 · Apache-2.0 · stdio
- verified: `mobile-next/mobile-mcp | 10102 | 2026-10-26T18:09:31Z | Apache-2.0 | -`; npm `@mobilenext/mobile-mcp` 1.0.14 (2026-10-26)
- CC: `claude mcp add mobile-mcp -- npx -y @mobilenext/mobile-mcp@latest` (README also has `npx @mobilenext/mobile-mcp@latest install`)
- OC: `"mobile-mcp": { "type": "local", "command": ["npx", "-y", "@mobilenext/mobile-mcp@latest"] }`
- Good for: the **kotlin** agent on Android apps (and Swift/RN apps): launch the app on an emulator, tap, type, screenshot, read the accessibility tree.
- Caveats: needs Android SDK/emulator or Xcode simulators locally; slow in CI.

---

## 5. Sandboxes, containers and runtimes

### 5.1 Container Use (dagger/container-use) — isolated, parallel dev environments per agent

- Repo: https://github.com/dagger/container-use · 4,080 stars · pushed 2026-09-21 · Apache-2.0 · stdio
- verified: `dagger/container-use | 4080 | 2026-09-21T14:05:02Z | Apache-2.0 | -`
- Install: `brew install dagger/tap/container-use` (README also offers a curl|bash installer; this box's policy denies `curl|sh`, so use brew or a release binary)
- CC (README): `claude mcp add container-use -- container-use stdio`
- OC: `"container-use": { "type": "local", "command": ["container-use", "stdio"] }`
- Good for: letting an agent build/test in a container on its own git branch, so several agents work in parallel without trampling the checkout; reviewable with `cu log/diff/merge`.
- Caveats: README: "early development and actively evolving". Needs Docker/Dagger. The agent must be told (via its rules file) to use the environment tools instead of host shell.

### 5.2 Docker MCP Gateway (docker/mcp-gateway) — run catalog MCP servers in containers

- Repo: https://github.com/docker/mcp-gateway · 1,616 stars · pushed 2026-10-26 · MIT · stdio (or `--transport streaming` HTTP)
- verified: `docker/mcp-gateway | 1616 | 2026-10-26T18:57:04Z | MIT | -`
- CC (README): `docker mcp client connect claude-code --profile <profile-id> --global`, or manually `claude mcp add docker-gateway -- docker mcp gateway run --profile <profile-id>`
- OC: `"docker-gateway": { "type": "local", "command": ["docker", "mcp", "gateway", "run", "--profile", "<profile-id>"] }`
- Good for: running third-party MCP servers (from Docker's catalog) each in its own container with minimal host privileges, behind a single entry. A safer way to try untrusted servers.
- Caveats: needs Docker Desktop's MCP Toolkit / `docker mcp` plugin; profiles are behind `docker mcp feature enable profiles` per README. One more moving part to debug.

### 5.3 Jupyter MCP Server (datalayer/jupyter-mcp-server) — live notebook execution

- Repo: https://github.com/datalayer/jupyter-mcp-server · 1,315 stars · pushed 2026-10-27 · BSD-3-Clause · stdio (uvx/Docker) or HTTP
- verified: `datalayer/jupyter-mcp-server | 1315 | 2026-10-27T15:00:40Z | BSD-3-Clause | -`; PyPI `jupyter-mcp-server` 2.2.4 (2026-10-11)
- CC: `claude mcp add jupyter -e JUPYTER_URL=http://localhost:8888 -e JUPYTER_TOKEN=YOUR_TOKEN -e ALLOW_IMG_OUTPUT=true -- uvx jupyter-mcp-server@latest`
- OC: `"jupyter": { "type": "local", "command": ["uvx", "jupyter-mcp-server@latest"], "environment": { "JUPYTER_URL": "http://localhost:8888", "JUPYTER_TOKEN": "{env:JUPYTER_TOKEN}", "ALLOW_IMG_OUTPUT": "true" } }`
- Good for: **python** data/ML work: inserting and executing cells in a running kernel, reading outputs and plots, iterating on a notebook.
- Caveats: executes arbitrary code in your kernel; point it at a disposable environment. Needs a running JupyterLab.

> Removed from consideration: `e2b-dev/mcp-server` (archived, last push 2026-04-16), `pydantic/mcp-run-python` (archived), `daytonaio/daytona` (repo archived). See [Rejected](#rejected-or-stale-candidates).

---

## 6. Databases

### 6.1 DBHub (bytebase/dbhub) — one server for Postgres, MySQL, MariaDB, SQL Server, Oracle, SQLite

- Repo: https://github.com/bytebase/dbhub · 3,752 stars · pushed 2026-10-26 · MIT · stdio or HTTP
- verified: `bytebase/dbhub | 3752 | 2026-10-26T09:22:30Z | MIT | -`; npm `@bytebase/dbhub` 1.5.0 (2026-10-09)
- CC (dbhub.ai/installation): `claude mcp add --transport stdio dbhub -- npx @bytebase/dbhub@latest --transport stdio --dsn "postgres://user:password@localhost:5432/dbname"`
- OC: `"dbhub": { "type": "local", "command": ["npx", "@bytebase/dbhub@latest", "--transport", "stdio", "--dsn", "{env:DATABASE_DSN}"] }`
- Good for: schema exploration, guarded SQL execution, opt-in `explain_sql`, custom parameterized tools in `dbhub.toml`; the default DB server for any language agent.
- Caveats: Node.js 22.5+ for npx. Keep DSNs in env, not in committed files. Use read-only DB users for agents.

### 6.2 Postgres MCP Pro (crystaldba/postgres-mcp) — Postgres tuning and health

- Repo: https://github.com/crystaldba/postgres-mcp · 3,440 stars · pushed 2026-08-17 · MIT · stdio (or SSE via Docker)
- verified: `crystaldba/postgres-mcp | 3440 | 2026-08-17T05:06:35Z | MIT | -`; PyPI `postgres-mcp` **0.3.0 (2025-05-16)**
- CC: `claude mcp add postgres -e DATABASE_URI=postgresql://user:pass@localhost:5432/db -- uvx postgres-mcp --access-mode=restricted`
- OC: `"postgres": { "type": "local", "command": ["uvx", "postgres-mcp", "--access-mode=restricted"], "environment": { "DATABASE_URI": "{env:DATABASE_URI}" } }`
- Good for: index recommendations, EXPLAIN plan analysis, health checks (bloat, vacuum, cache hit), restricted read-only mode for production.
- Caveats: the repo is live, but the **last PyPI release is May 2025**, so the published package lags the repo (maturity flag). README examples use `unrestricted` (dev only).

### 6.3 Supabase MCP (supabase/mcp)

- Repo: https://github.com/supabase/mcp (redirected from `supabase-community/supabase-mcp`) · 2,982 stars · pushed 2026-10-29 · Apache-2.0 · remote HTTP (OAuth)
- verified: `supabase/mcp | 2982 | 2026-10-29T09:33:00Z | Apache-2.0 | -`
- Probe: `https://mcp.supabase.com/mcp` → **401** "No access token provided" (OAuth).
- CC: `claude mcp add --transport http supabase "https://mcp.supabase.com/mcp?project_ref=<ref>&read_only=true"`
- OC: `"supabase": { "type": "remote", "url": "https://mcp.supabase.com/mcp?project_ref=<ref>&read_only=true" }`
- Good for: schema/migrations, SQL, logs, advisors, edge functions, type generation on Supabase projects.
- Caveats: scope to one `project_ref` and `read_only=true` for agents. Local CLI endpoint `http://localhost:54321/mcp` has a reduced toolset and no OAuth.

### 6.4 MongoDB MCP Server (mongodb-js/mongodb-mcp-server) — official

- Repo: https://github.com/mongodb-js/mongodb-mcp-server · 1,152 stars · pushed 2026-10-29 · Apache-2.0 · stdio
- verified: `mongodb-js/mongodb-mcp-server | 1152 | 2026-10-29T09:20:54Z | Apache-2.0 | -`; npm `mongodb-mcp-server` 3.2.2 (2026-10-29)
- CC: `claude mcp add mongodb -e MDB_MCP_CONNECTION_STRING=mongodb://localhost:27017/myDatabase -- npx -y mongodb-mcp-server@latest --readOnly`
- OC: `"mongodb": { "type": "local", "command": ["npx", "-y", "mongodb-mcp-server@latest", "--readOnly"], "environment": { "MDB_MCP_CONNECTION_STRING": "{env:MDB_MCP_CONNECTION_STRING}" } }`
- Good for: querying collections, aggregations, index and schema inspection; Atlas admin tools with API credentials.
- Caveats: Node 20 support is deprecated (README: use Node 22.13+). Keep `--readOnly` unless the task needs writes.

### 6.5 Redis MCP Server (redis/mcp-redis) — official

- Repo: https://github.com/redis/mcp-redis · 641 stars · pushed 2026-10-26 · MIT · stdio
- verified: `redis/mcp-redis | 641 | 2026-10-26T16:33:56Z | MIT | -`; PyPI `redis-mcp-server` 0.5.1 (2026-08-05)
- CC: `claude mcp add redis -- uvx --from redis-mcp-server@latest redis-mcp-server --url redis://localhost:6379/0`
- OC: `"redis": { "type": "local", "command": ["uvx", "--from", "redis-mcp-server@latest", "redis-mcp-server", "--url", "redis://localhost:6379/0"] }`
- Good for: inspecting keys and data structures, streams, JSON and vector search indexes while debugging caches and queues.
- Caveats: 0.x; full read/write by default. Use an ACL user with limited commands.

---

## 7. Security scanning and supply chain

Ranked by breadth for a code-writing agent: SAST first (Semgrep, Snyk), then dependency risk (Socket), secrets
(GitGuardian), then container/IaC (Trivy) and CodeQL query work.

### 7.1 Semgrep MCP (built into the `semgrep` CLI; semgrep/semgrep)

- Repo: https://github.com/semgrep/semgrep/tree/develop/cli/src/semgrep/mcp · 17,335 stars · pushed 2026-10-29 · LGPL-2.1 · stdio or streamable HTTP
- verified: `semgrep/semgrep | 17335 | 2026-10-29T00:01:57Z | LGPL-2.1 | -`; PyPI `semgrep` 1.182.1 (2026-10-22). The old standalone repo `semgrep/mcp` is **archived** (README: "moved ... to the main semgrep repository").
- CC: `claude mcp add semgrep -- semgrep mcp` (install the CLI with `brew install semgrep` or `pipx install semgrep`; Docker: `docker run -i --rm semgrep/semgrep semgrep mcp -t stdio`). Vendor alternative: the Semgrep Claude Code plugin from `/plugin`, then `/setup-semgrep-plugin`.
- OC: `"semgrep": { "type": "local", "command": ["semgrep", "mcp"] }`
- Good for: scanning the code the agent just wrote (OWASP-class bugs, custom rules), returning findings as structured data; works for Python, JS/TS, Go, Java, Kotlin, C#, Rust, C/C++ and more.
- Caveats: Pro/cross-file rules need a Semgrep account (`SEMGREP_APP_TOKEN`). Stdio mode looks idle until a client connects (expected).

### 7.2 Snyk MCP (built into the Snyk CLI; snyk/cli)

- Repo: https://github.com/snyk/cli · 5,692 stars · pushed 2026-10-29 · Apache-2.0 (LICENSE file; GitHub shows NOASSERTION) · stdio or SSE
- verified: `snyk/cli | 5692 | 2026-10-29T08:27:17Z | NOASSERTION | -`; npm `snyk` 1.1308.3 (2026-10-23)
- CC (docs.snyk.io Claude Code guide): `.mcp.json` → `"snyk": { "command": "npx", "args": ["-y", "snyk@latest", "mcp", "-t", "stdio"] }` (or `snyk mcp configure --tool=claude-cli`)
- OC: `"snyk": { "type": "local", "command": ["npx", "-y", "snyk@latest", "mcp", "-t", "stdio"] }`
- Good for: `snyk_code_scan` (SAST), open-source dependency, container and IaC scans in one tool; supports C/C++, .NET, Go, Java/Kotlin, JS/TS, Python, Rust and others per Snyk's docs.
- Caveats: requires a Snyk account and `snyk auth`; free-tier test limits apply. Results go through Snyk's cloud.

### 7.3 Socket MCP (SocketDev/socket-mcp) — dependency risk scores before you add a package

- Repo: https://github.com/SocketDev/socket-mcp · 137 stars · pushed 2026-10-27 · MIT · remote HTTP (OAuth) or local npm
- verified: `SocketDev/socket-mcp | 137 | 2026-10-27T15:47:31Z | MIT | -`
- Probe: `https://mcp.socket.dev/` → **200** (`serverInfo.name: "socket"`, version 0.3.0).
- CC (README): `claude mcp add --transport http socket-mcp https://mcp.socket.dev/`
- OC: `"socket-mcp": { "type": "remote", "url": "https://mcp.socket.dev/" }`
- Good for: checking supply-chain, quality, maintenance, vulnerability and license scores of npm, PyPI, Maven, Cargo, NuGet and Go packages **before** the agent adds a dependency. Catches typosquats and malware that CVE scanners miss.
- Caveats: scores are heuristics; still pin versions and read the lockfile diff.

### 7.4 GitGuardian MCP (GitGuardian/ggmcp) — secrets detection

- Repo: https://github.com/GitGuardian/ggmcp (redirected from `GitGuardian/gg-mcp`) · 41 stars · pushed 2026-10-23 · MIT · remote HTTP (OAuth) or stdio
- verified: `GitGuardian/ggmcp | 41 | 2026-10-23T07:14:06Z | MIT | -`
- Probe: `https://mcp.gitguardian.com/mcp` → **401** (auth required). EU: `https://mcp.eu1.gitguardian.com/mcp`.
- CC: `claude mcp add --transport http gitguardian https://mcp.gitguardian.com/mcp`
- OC: `"gitguardian": { "type": "remote", "url": "https://mcp.gitguardian.com/mcp" }`
- Good for: scanning diffs and files for hard-coded secrets before commit, and triaging existing incidents.
- Caveats: needs a GitGuardian account. The stdio browser-OAuth flow is deprecated per README; use the remote server or a PAT with `ENABLE_LOCAL_OAUTH=false`.

### 7.5 Trivy MCP (aquasecurity/trivy-mcp) — containers, filesystems, IaC — **STALE**

- Repo: https://github.com/aquasecurity/trivy-mcp · 56 stars · **pushed 2025-12-17 (STALE)** · MIT · stdio (default), SSE, streamable HTTP
- verified: `aquasecurity/trivy-mcp | 56 | 2025-12-17T16:02:32Z | MIT | -`
- Install: `trivy plugin install mcp`
- CC: `claude mcp add trivy -- trivy mcp`
- OC: `"trivy": { "type": "local", "command": ["trivy", "mcp"] }`
- Good for: vulnerability, misconfiguration and secret scans of Dockerfiles, images, Terraform/K8s manifests and lockfiles, using the Trivy you already run in CI.
- Caveats: no push in 2026, so treat it as maintenance-mode. Trivy itself is current; the CLI is a fine fallback via shell.

### 7.6 CodeQL Development MCP Server (advanced-security/codeql-development-mcp-server)

- Repo: https://github.com/advanced-security/codeql-development-mcp-server · 38 stars · pushed 2026-10-22 · **GitHub CodeQL Terms and Conditions** (not OSI; GitHub shows NOASSERTION) · stdio
- verified: `advanced-security/codeql-development-mcp-server | 38 | 2026-10-22T21:13:40Z | NOASSERTION | -`; npm `codeql-development-mcp-server` 2.27.3 (2026-10-22)
- CC: `claude mcp add ql-mcp -- npx -y codeql-development-mcp-server`
- OC: `"ql-mcp": { "type": "local", "command": ["npx", "-y", "codeql-development-mcp-server"] }`
- Good for: writing and testing custom CodeQL queries (AST/CFG inspection, query compile/run via CLI and LSP) for deep taint analysis in C/C++, C#, Go, Java/Kotlin, JS/TS, Python, Rust.
- Caveats: CodeQL licensing restricts use on non-open-source code without GitHub Advanced Security. Needs the CodeQL CLI. A query-development tool, not a one-click scanner.

---

## 8. Observability and errors

### 8.1 Sentry MCP (getsentry/toolkit, formerly getsentry/sentry-mcp)

- Repo: https://github.com/getsentry/toolkit (redirect from `getsentry/sentry-mcp`) · 949 stars · pushed 2026-10-29 · FSL-1.1-Apache-2.0 (GitHub shows NOASSERTION) · remote HTTP (OAuth) or stdio
- verified: `getsentry/toolkit | 949 | 2026-10-29T09:34:02Z | NOASSERTION | -`; npm `@sentry/mcp-server` 0.42.0 (2026-09-25)
- Probe: `https://mcp.sentry.dev/mcp` → **401** (OAuth).
- CC: `claude mcp add --transport http sentry https://mcp.sentry.dev/mcp` (OAuth). Self-hosted Sentry: `claude mcp add sentry -- npx @sentry/mcp-server@latest --access-token=YOUR_TOKEN --host=sentry.example.com`
- OC: `"sentry": { "type": "remote", "url": "https://mcp.sentry.dev/mcp" }` (OpenCode docs use Sentry as their own OAuth example)
- Good for: pulling the real stack trace, breadcrumbs and release info for a production error into the debugging loop; Seer root-cause analysis.
- Caveats: FSL is source-available (converts to Apache-2.0 later), not OSI today. The README says to set `EMBEDDED_AGENT_PROVIDER` explicitly for AI-powered tools.

---

## 9. Language-specific servers

### 9.1 LLDB MCP (`lldb-mcp`, ships with LLDB; llvm/llvm-project) — cpp, rust (native debugging)

- Repo: https://github.com/llvm/llvm-project (lldb/) · 41,242 stars · pushed 2026-10-29 · Apache-2.0 WITH LLVM-exception (GitHub shows NOASSERTION) · stdio
- verified: `llvm/llvm-project | 41242 | 2026-10-29T09:38:24Z | NOASSERTION | -`
- Docs: https://lldb.llvm.org/use/mcp.html (page dated 2026-10-17): "LLDB ships with `lldb-mcp`, a binary that speaks MCP over stdio". Tools include `session_create`, `sessions_list`, `command`. To attach to an LLDB you already have open: `(lldb) protocol-server start MCP`, and `lldb-mcp` discovers it via `~/.lldb`.
- CC: `claude mcp add lldb --transport stdio -- /path/to/lldb-mcp` (the docs page renders the flags with odd spacing; this is the standard `claude mcp add` form)
- OC: `"lldb": { "type": "local", "command": ["/path/to/lldb-mcp"] }`
- Good for: agent-driven debugging of C/C++ (and Rust/Swift) binaries: breakpoints, stepping, frame/variable inspection, core files.
- Caveats: which LLVM release first shipped the `lldb-mcp` binary is `[UNVERIFIED]`; check `lldb-mcp --help` on your toolchain (the in-LLDB `protocol-server` command dates from June 2025 commits). Debugging runs arbitrary binaries.

### 9.2 Roslyn CodeLens MCP (MarcelRoozekrans/roslyn-codelens-mcp) — csharp

- Repo: https://github.com/MarcelRoozekrans/roslyn-codelens-mcp · 70 stars · pushed 2026-10-28 · MIT · stdio (optional `--http`)
- verified: `MarcelRoozekrans/roslyn-codelens-mcp | 70 | 2026-10-28T03:02:11Z | MIT | -`; npm launcher `roslyn-codelens-mcp` 2.18.2 (2026-10-13); NuGet `RoslynCodeLens.Mcp` 2.18.2
- CC: `claude mcp add roslyn -- dnx RoslynCodeLens.Mcp --yes` (needs .NET 10 SDK) · or `claude mcp add roslyn -- npx -y roslyn-codelens-mcp`
- OC: `"roslyn": { "type": "local", "command": ["dnx", "RoslynCodeLens.Mcp", "--yes"] }`
- Good for: Roslyn-semantic C#: symbol search, references, call graphs, diagnostics and analyzers across a `.sln`, which is far more precise than grep on large .NET solutions.
- Caveats: small single-maintainer project. The npm package is only a launcher that installs the .NET tool. Alternatives: Serena (C# via LSP) or Rider's built-in MCP (3.6). `kooshi/SharpToolsMCP` was rejected because it must be built from source.

### 9.3 NuGet MCP Server (DimonSmart/NugetMcpServer) — csharp

- Repo: https://github.com/DimonSmart/NugetMcpServer · 24 stars · pushed 2026-10-22 · 0BSD (LICENSE file "Zero-Clause BSD"; GitHub shows NOASSERTION) · stdio
- verified: `DimonSmart/NugetMcpServer | 24 | 2026-10-22T17:40:15Z | NOASSERTION | -`; NuGet `DimonSmart.NugetMcpServer` latest 1.1.10 (README still pins 1.1.7)
- CC (README form, version updated): `claude mcp add --transport stdio nuget -- dnx DimonSmart.NugetMcpServer@1.1.10 --yes`
- OC: `"nuget": { "type": "local", "command": ["dnx", "DimonSmart.NugetMcpServer@1.1.10", "--yes"] }`
- Good for: real public API surface (types, members) and versions of NuGet packages before writing code against them, which cuts hallucinated APIs.
- Caveats: tiny project; pin the version as shown. Docker alternative: `ghcr.io/dimonsmart/nugetmcpserver:latest`.

### 9.4 rust-analyzer MCP (zeenix/rust-analyzer-mcp) — rust

- Repo: https://github.com/zeenix/rust-analyzer-mcp · 86 stars · pushed 2026-09-15 · MIT · stdio
- verified: `zeenix/rust-analyzer-mcp | 86 | 2026-09-15T17:14:45Z | MIT | -`; crate `rust-analyzer-mcp` 0.4.0 (2026-08-22)
- Install: `cargo install rust-analyzer-mcp` (plus `rustup component add rust-analyzer`)
- CC (README `.mcp.json`): `"rust-analyzer": { "command": "rust-analyzer-mcp" }` · or `claude mcp add rust-analyzer -- rust-analyzer-mcp`
- OC: `"rust-analyzer": { "type": "local", "command": ["rust-analyzer-mcp"] }`
- Good for: hover types, definitions, references, diagnostics, completions with Cargo features enabled (`"args": ["--features", "serde,tokio"]` per README).
- Caveats: small project; mcpls (3.3) is the more actively released alternative. Large workspaces take a while for rust-analyzer to index.

### 9.5 crates.io MCP (joshrotenberg/cratesio-mcp) — rust

- Repo: https://github.com/joshrotenberg/cratesio-mcp · 18 stars · pushed 2026-08-05 · Apache-2.0 · stdio
- verified: `joshrotenberg/cratesio-mcp | 18 | 2026-08-05T23:27:17Z | Apache-2.0 | -`; crate `cratesio-mcp` 0.4.1 (2026-08-05)
- CC: `cargo install cratesio-mcp` then `claude mcp add cratesio -- cratesio-mcp`
- OC: `"cratesio": { "type": "local", "command": ["cratesio-mcp"] }`
- Good for: current crate versions, features, dependencies and download stats before editing `Cargo.toml`.
- Caveats: very small project (18 stars); `cargo search` / `cargo info` via shell is an equally valid fallback. Pair with Context7 or docs.rs for API docs.

### 9.6 gopls MCP (golang/tools, built into gopls v0.20+) — go

- Repo: https://github.com/golang/tools (gopls/) · 8,011 stars · pushed 2026-10-28 · BSD-3-Clause · stdio ("detached") or SSE ("attached", `gopls serve -mcp.listen=localhost:8092`)
- verified: `golang/tools | 8011 | 2026-10-28T18:27:01Z | BSD-3-Clause | -`
- Docs: `gopls/doc/features/mcp.md`: "Gopls includes an **experimental** built-in server for MCP".
- CC (from the doc): `claude mcp add gopls -- gopls mcp`; load its model instructions with `gopls mcp -instructions > CLAUDE-gopls.md` and reference the file from CLAUDE.md
- OC: `"gopls": { "type": "local", "command": ["gopls", "mcp"] }`
- Good for: Go workspace symbol search, package API summaries, references, diagnostics after edits, all from the official Go toolchain team.
- Caveats: marked experimental; detached mode sees saved files only. Requires gopls ≥ v0.20 on PATH.

### 9.7 godig (samber/godig) — go (pkg.go.dev)

- Repo: https://github.com/samber/godig · 21 stars · pushed 2026-10-18 · MIT · stdio or remote HTTP
- verified: `samber/godig | 21 | 2026-10-18T22:42:40Z | MIT | -`
- Probe: `https://godig.samber.dev/mcp` → **200** (`serverInfo.name: "godig"`).
- CC (README): `claude mcp add --transport http pkg-go-dev https://godig.samber.dev/mcp` · local: `go install github.com/samber/godig/cmd/godig@latest` then `claude mcp add pkg-go-dev -- godig mcp`
- OC: `"pkg-go-dev": { "type": "remote", "url": "https://godig.samber.dev/mcp" }`
- Good for: module versions, package docs, symbols, importers and licenses from pkg.go.dev, so the agent picks real, current modules.
- Caveats: tiny, single-maintainer (author of `samber/lo`); the hosted endpoint is a personal service. Prefer the local binary for reliability.

### 9.8 Maven Tools MCP (arvindand/maven-tools-mcp) — java, kotlin

- Repo: https://github.com/arvindand/maven-tools-mcp · 35 stars · pushed 2026-10-26 · MIT · stdio (Docker)
- verified: `arvindand/maven-tools-mcp | 35 | 2026-10-26T14:40:58Z | MIT | -`
- CC: `claude mcp add maven-tools -- docker run -i --rm arvindand/maven-tools-mcp:latest`
- OC: `"maven-tools": { "type": "local", "command": ["docker", "run", "-i", "--rm", "arvindand/maven-tools-mcp:latest"] }`
- Good for: latest stable versions, version comparison, dependency health and upgrade advice from Maven Central for `pom.xml` / Gradle version catalogs.
- Caveats: small project; Docker required (a JAR build is documented as the Docker-free path).

### 9.9 Gradle MCP (rnett/gradle-mcp) — java, kotlin

- Repo: https://github.com/rnett/gradle-mcp · 68 stars · pushed 2026-10-25 · Apache-2.0 · stdio (JBang)
- verified: `rnett/gradle-mcp | 68 | 2026-10-25T17:38:04Z | Apache-2.0 | -`
- CC (README JSON): `claude mcp add gradle -- jbang run --quiet --fresh gradle-mcp@rnett`
- OC: `"gradle": { "type": "local", "command": ["jbang", "run", "--quiet", "--fresh", "gradle-mcp@rnett"] }`
- Good for: running Gradle tasks and tests through the Tooling API with structured results (failed tests, build errors), project/task introspection; useful for Kotlin and Android builds.
- Caveats: needs JBang and a JDK. `--fresh` re-resolves on every start (slower but current). Small project.

---

## Recommended per language

Each language agent should declare `github` (by name) and `context7` (inline) per the SPEC, plus 2–4 of the following.
Picks are ranked; the first two are the default set and the others are situational. Numbers refer to entries above.

| slug | 1st pick | 2nd pick | 3rd (situational) | 4th (situational) | why this set |
|---|---|---|---|---|---|
| python | Serena 3.1 (pyright/LSP symbols) | Semgrep 7.1 | Jupyter 5.3 (notebooks, data/ML) | DBHub 6.1 | Symbol nav plus SAST; notebooks only when the repo has them. |
| cpp | mcp-language-server 3.2 with `clangd` (needs `compile_commands.json`) | LLDB `lldb-mcp` 9.1 | Semgrep 7.1 | CodeQL dev 7.6 | clangd for semantics, LLDB for crashes/UB; CodeQL for deep taint work. |
| csharp | Microsoft Learn 1.2 | Roslyn CodeLens 9.2 | NuGet MCP 9.3 | Snyk 7.2 | Official docs, Roslyn semantics, real package APIs. Rider users: JetBrains 3.6 instead of 9.2. |
| rust | mcpls 3.3 (or rust-analyzer-mcp 9.4) | crates.io MCP 9.5 | Semgrep 7.1 | LLDB 9.1 | rust-analyzer diagnostics, crate metadata, debugger for `unsafe`/FFI bugs. |
| javascript | MDN 1.3 | Socket 7.3 | Playwright 4.1 | Chrome DevTools 4.2 | Web-platform docs, dependency risk before `npm install`, browser checks. |
| typescript | mcp-language-server 3.2 with `typescript-language-server` (or Serena 3.1) | Socket 7.3 | Next.js DevTools 4.3 (Next apps) | Playwright 4.1 | tsserver-backed types and refs; Next.js server only when `next` is a dependency. |
| go | gopls MCP 9.6 | godig 9.7 | Semgrep 7.1 | DBHub 6.1 | Official gopls tools plus pkg.go.dev module facts. |
| java | JetBrains built-in 3.6 (if IntelliJ runs) else Serena 3.1 (jdtls) | Maven Tools 9.8 | Gradle MCP 9.9 | Snyk 7.2 | IDE-grade Java semantics, dependency versions, structured build/test results. |
| kotlin | JetBrains built-in 3.6 (IntelliJ / Android Studio) else Serena 3.1 | Gradle MCP 9.9 | Maven Tools 9.8 | Mobile MCP 4.5 (Android) | Kotlin semantics are best in IntelliJ; Gradle is the build system; device automation for Android. |
| web | MDN 1.3 | Chrome DevTools 4.2 | Playwright 4.1 | shadcn 4.4 (React/Tailwind projects) | Baseline/compat facts, CWV/Lighthouse and console, scripted UI checks. |

Cross-cutting add-ons any agent may load on demand: GitHub 2.1 (default, by name), Context7 1.1 (default), DBHub 6.1
(any SQL DB), Sentry 8.1 (production errors), Container Use 5.1 (parallel isolated runs), GitGuardian 7.4 (pre-commit
secrets check).

### Copy-paste example: `.mcp.json` for a TypeScript project (Claude Code)

```json
{
  "mcpServers": {
    "context7": { "type": "http", "url": "https://mcp.context7.com/mcp" },
    "mdn":      { "type": "http", "url": "https://mcp.mdn.mozilla.net/" },
    "socket-mcp": { "type": "http", "url": "https://mcp.socket.dev/" },
    "lsp-ts": { "type": "stdio", "command": "mcp-language-server",
                "args": ["--workspace", "${CLAUDE_PROJECT_DIR:-.}", "--lsp", "typescript-language-server", "--", "--stdio"] },
    "playwright": { "type": "stdio", "command": "npx", "args": ["@playwright/mcp@latest", "--headless", "--isolated"] }
  }
}
```

### Same set for OpenCode (`opencode.jsonc`)

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "context7":   { "type": "remote", "url": "https://mcp.context7.com/mcp" },
    "mdn":        { "type": "remote", "url": "https://mcp.mdn.mozilla.net/" },
    "socket-mcp": { "type": "remote", "url": "https://mcp.socket.dev/" },
    "lsp-ts":     { "type": "local", "command": ["mcp-language-server", "--workspace", ".", "--lsp", "typescript-language-server", "--", "--stdio"] },
    "playwright": { "type": "local", "command": ["npx", "@playwright/mcp@latest", "--headless", "--isolated"] }
  }
}
```

(The `${CLAUDE_PROJECT_DIR:-.}` default is the form the Claude Code MCP docs require for that variable in a
project-scoped `.mcp.json`. Whether `mcp-language-server` accepts a relative `.` workspace in OpenCode is
`[UNVERIFIED]`; use an absolute path if it complains.)

---

## Rejected or stale candidates

Checked this session and left out (all via `ghapi.sh repos/<owner>/<repo>`):

| repo | stars | pushed_at | reason |
|---|---|---|---|
| semgrep/mcp | 686 | 2025-10-28 | **archived**; moved into the `semgrep` binary (7.1) |
| e2b-dev/mcp-server | 392 | 2026-04-16 | **archived** |
| pydantic/mcp-run-python | 193 | 2026-01-30 | **archived** |
| storybookjs/mcp | 271 | 2026-09-07 | **archived** |
| pydantic/logfire-mcp | 162 | 2026-07-13 | README: archived, stdio server replaced by a remote server |
| sammcj/mcp-package-version | 121 | 2026-01-28 | **archived** |
| docfork/docfork | 484 | 2026-06-13 | **archived** |
| browserbase/mcp-server-browserbase | 3,397 | 2026-07-20 | **archived** |
| daytonaio/daytona | 71,442 | 2026-07-24 | **archived** repo |
| JetBrains/mcp-jetbrains | 963 | 2026-01-07 | deprecated; built into IDEs 2025.2+ (kept only as provenance for 3.6) |
| JetBrains/mcp-server-plugin | 132 | 2025-08-18 | stale; superseded by the bundled plugin |
| Govcraft/rust-docs-mcp-server | 300 | 2025-11-24 | STALE; needs an OpenAI key for embeddings |
| felipeerias/clangd-mcp-server | 50 | 2025-12-03 | STALE; README's npm install is commented out (build from source) |
| Tritlo/lsp-mcp, jonrad/lsp-mcp | 128 / 192 | 2025-07 / 2025-03 | STALE |
| minhalvp/android-mcp-server | 811 | 2025-05-28 | STALE; mobile-mcp (4.5) covers Android |
| kooshi/SharpToolsMCP | 228 | 2026-06-02 | build-from-source only; 9.2 is installable via `dnx` |
| stephanj/LSP4J-MCP | 38 | 2026-10-05 | no license file (GitHub `license: null`) |
| Artmann/package-registry-mcp | 39 | 2025-12-02 | STALE |
| loonghao/pypi-query-mcp-server | 19 | 2026-10-26 | repo live but last PyPI release 0.6.5 on 2025-08-02 |
| zeenix alternative `ciresnave/rust-analyzer-mcp-server` | 8 | 2026-10-28 | too small to recommend |
| Kotlin/kotlin-lsp | 3,541 | 2026-10-29 | a language server, not an MCP server; usable through Serena / LSP bridges |

---

## Appendix A: raw GitHub verification dump

Command (run 2026-10-29 from the scratchpad; prints `full_name | stargazers_count | pushed_at | license.spdx_id | archived | html_url`):

```
ghapi.sh repos/<owner>/<repo>   # for each repo below, fields extracted with python3 -I
```

```
upstash/context7 | 63881 | 2026-10-28T20:26:24Z | MIT | - | https://github.com/upstash/context7
MicrosoftDocs/mcp | 1958 | 2026-10-25T04:04:28Z | CC-BY-4.0 | - | https://github.com/MicrosoftDocs/mcp
mdn/mcp | 193 | 2026-10-26T12:05:39Z | MPL-2.0 | - | https://github.com/mdn/mcp
idosal/git-mcp | 8495 | 2026-05-08T14:21:24Z | Apache-2.0 | - | https://github.com/idosal/git-mcp
ref-tools/ref-tools-mcp | 1184 | 2026-10-24T00:25:58Z | MIT | - | https://github.com/ref-tools/ref-tools-mcp
modelcontextprotocol/servers | 91658 | 2026-10-29T05:27:40Z | NOASSERTION | - | https://github.com/modelcontextprotocol/servers
github/github-mcp-server | 34054 | 2026-10-29T05:42:25Z | MIT | - | https://github.com/github/github-mcp-server
cyanheads/git-mcp-server | 243 | 2026-09-26T21:23:28Z | Apache-2.0 | - | https://github.com/cyanheads/git-mcp-server
oraios/serena | 30833 | 2026-10-28T10:45:55Z | NOASSERTION | - | https://github.com/oraios/serena
isaacphi/mcp-language-server | 1611 | 2026-03-01T23:27:09Z | BSD-3-Clause | - | https://github.com/isaacphi/mcp-language-server
bug-ops/mcpls | 80 | 2026-10-28T21:48:33Z | Apache-2.0 | - | https://github.com/bug-ops/mcpls
blackwell-systems/agent-lsp | 166 | 2026-10-29T04:51:07Z | MIT | - | https://github.com/blackwell-systems/agent-lsp
zilliztech/claude-context | 12658 | 2026-07-14T12:00:38Z | MIT | - | https://github.com/zilliztech/claude-context
JetBrains/mcp-jetbrains | 963 | 2026-01-07T16:21:45Z | Apache-2.0 | - | https://github.com/JetBrains/mcp-jetbrains
microsoft/playwright-mcp | 38797 | 2026-10-22T17:43:26Z | Apache-2.0 | - | https://github.com/microsoft/playwright-mcp
ChromeDevTools/chrome-devtools-mcp | 54394 | 2026-10-29T09:31:38Z | Apache-2.0 | - | https://github.com/ChromeDevTools/chrome-devtools-mcp
vercel/next-devtools-mcp | 834 | 2026-09-15T00:32:28Z | None | - | https://github.com/vercel/next-devtools-mcp
shadcn-ui/ui | 126870 | 2026-10-29T08:19:27Z | MIT | - | https://github.com/shadcn-ui/ui
mobile-next/mobile-mcp | 10102 | 2026-10-26T18:09:31Z | Apache-2.0 | - | https://github.com/mobile-next/mobile-mcp
dagger/container-use | 4080 | 2026-09-21T14:05:02Z | Apache-2.0 | - | https://github.com/dagger/container-use
docker/mcp-gateway | 1616 | 2026-10-26T18:57:04Z | MIT | - | https://github.com/docker/mcp-gateway
datalayer/jupyter-mcp-server | 1315 | 2026-10-27T15:00:40Z | BSD-3-Clause | - | https://github.com/datalayer/jupyter-mcp-server
bytebase/dbhub | 3752 | 2026-10-26T09:22:30Z | MIT | - | https://github.com/bytebase/dbhub
crystaldba/postgres-mcp | 3440 | 2026-08-17T05:06:35Z | MIT | - | https://github.com/crystaldba/postgres-mcp
supabase/mcp | 2982 | 2026-10-29T09:33:00Z | Apache-2.0 | - | https://github.com/supabase/mcp
mongodb-js/mongodb-mcp-server | 1152 | 2026-10-29T09:20:54Z | Apache-2.0 | - | https://github.com/mongodb-js/mongodb-mcp-server
redis/mcp-redis | 641 | 2026-10-26T16:33:56Z | MIT | - | https://github.com/redis/mcp-redis
semgrep/semgrep | 17335 | 2026-10-29T00:01:57Z | LGPL-2.1 | - | https://github.com/semgrep/semgrep
snyk/cli | 5692 | 2026-10-29T08:27:17Z | NOASSERTION | - | https://github.com/snyk/cli
SocketDev/socket-mcp | 137 | 2026-10-27T15:47:31Z | MIT | - | https://github.com/SocketDev/socket-mcp
GitGuardian/ggmcp | 41 | 2026-10-23T07:14:06Z | MIT | - | https://github.com/GitGuardian/ggmcp
aquasecurity/trivy-mcp | 56 | 2025-12-17T16:02:32Z | MIT | - | https://github.com/aquasecurity/trivy-mcp
advanced-security/codeql-development-mcp-server | 38 | 2026-10-22T21:13:40Z | NOASSERTION | - | https://github.com/advanced-security/codeql-development-mcp-server
getsentry/toolkit | 949 | 2026-10-29T09:34:02Z | NOASSERTION | - | https://github.com/getsentry/toolkit
llvm/llvm-project | 41242 | 2026-10-29T09:38:24Z | NOASSERTION | - | https://github.com/llvm/llvm-project
MarcelRoozekrans/roslyn-codelens-mcp | 70 | 2026-10-28T03:02:11Z | MIT | - | https://github.com/MarcelRoozekrans/roslyn-codelens-mcp
DimonSmart/NugetMcpServer | 24 | 2026-10-22T17:40:15Z | NOASSERTION | - | https://github.com/DimonSmart/NugetMcpServer
zeenix/rust-analyzer-mcp | 86 | 2026-09-15T17:14:45Z | MIT | - | https://github.com/zeenix/rust-analyzer-mcp
joshrotenberg/cratesio-mcp | 18 | 2026-08-05T23:27:17Z | Apache-2.0 | - | https://github.com/joshrotenberg/cratesio-mcp
golang/tools | 8011 | 2026-10-28T18:27:01Z | BSD-3-Clause | - | https://github.com/golang/tools
samber/godig | 21 | 2026-10-18T22:42:40Z | MIT | - | https://github.com/samber/godig
arvindand/maven-tools-mcp | 35 | 2026-10-26T14:40:58Z | MIT | - | https://github.com/arvindand/maven-tools-mcp
rnett/gradle-mcp | 68 | 2026-10-25T17:38:04Z | Apache-2.0 | - | https://github.com/rnett/gradle-mcp
anomalyco/opencode | 222892 | 2026-10-29T08:58:28Z | MIT | - | https://github.com/anomalyco/opencode
```

`NOASSERTION` licenses were resolved by reading each repo's LICENSE file via `ghapi.sh repos/<r>/license`:
serena = MIT (SolidLSP) + GPL-3.0-or-later (app); modelcontextprotocol/servers = MIT→Apache-2.0 transition (docs
CC-BY-4.0); getsentry/toolkit = FSL-1.1-Apache-2.0; snyk/cli = Apache-2.0; DimonSmart/NugetMcpServer = 0BSD;
codeql-development-mcp-server = GitHub CodeQL Terms and Conditions. llvm-project's Apache-2.0 WITH LLVM-exception
is from general knowledge of the project, not re-read this session `[UNVERIFIED this session]`.
vercel/next-devtools-mcp has no LICENSE file; npm metadata says `MIT`.

## Appendix B: package registry check

Read from the registry JSON APIs on 2026-10-29 (`latest` tag / max version, publish date):

```
npm @playwright/mcp 0.0.83 2026-09-28        npm chrome-devtools-mcp 1.12.0 2026-10-22
npm next-devtools-mcp 0.4.0 2026-06-24       npm @zilliz/claude-context-mcp 0.1.15 2026-06-22
npm @cyanheads/git-mcp-server 2.15.3 2026-08-24   npm @bytebase/dbhub 1.5.0 2026-10-09
npm mongodb-mcp-server 3.2.2 2026-10-29      npm @modelcontextprotocol/server-filesystem 2.1.0 2026-10-28
npm roslyn-codelens-mcp 2.18.2 2026-10-13    npm @mobilenext/mobile-mcp 1.0.14 2026-10-26
npm codeql-development-mcp-server 2.27.3 2026-10-22   npm @sentry/mcp-server 0.42.0 2026-09-25
npm shadcn 4.23.0 2026-10-27                 npm snyk 1.1308.3 2026-10-23
npm ref-tools-mcp 3.0.3 2025-11-04           npm ctx7 0.8.2 2026-10-23
npm @upstash/context7-mcp 4.4.4 2026-10-19
pypi mcp-server-git 2026.10.28 2026-10-28    pypi mcp-server-fetch 2026.10.28 2026-10-28
pypi serena-agent 2.1.0 2026-10-19           pypi postgres-mcp 0.3.0 2025-05-16
pypi jupyter-mcp-server 2.2.4 2026-10-11     pypi redis-mcp-server 0.5.1 2026-08-05
pypi semgrep 1.182.1 2026-10-22              pypi pypi-query-mcp-server 0.6.5 2025-08-02
crate mcpls 0.8.0 2026-10-20                 crate rust-analyzer-mcp 0.4.0 2026-08-22
crate cratesio-mcp 0.4.1 2026-08-05
nuget RoslynCodeLens.Mcp 2.18.2              nuget DimonSmart.NugetMcpServer 1.1.10
```

## Appendix C: remote endpoint probe

One MCP `initialize` JSON-RPC POST per endpoint, no credentials, 2026-10-29:

```
https://mcp.context7.com/mcp                 -> 200 (protocolVersion 2025-06-18)
https://gitmcp.io/microsoft/playwright-mcp   -> 200 (GitMCP)
https://learn.microsoft.com/api/mcp          -> 200
https://mcp.mdn.mozilla.net/                 -> 200 (serverInfo mdn 0.0.1)
https://mcp.socket.dev/                      -> 200 (serverInfo socket 0.3.0)
https://godig.samber.dev/mcp                 -> 200 (serverInfo godig)
https://api.githubcopilot.com/mcp/           -> 401 missing Authorization header
https://mcp.supabase.com/mcp                 -> 401 No access token provided
https://mcp.sentry.dev/mcp                   -> 401
https://mcp.gitguardian.com/mcp              -> 401
https://api.ref.tools/mcp                    -> 401 Unauthorized
```

Local (stdio) servers were **not** started. Their install lines are copied from the vendors' READMEs and docs and are
untested on this box (`[UNVERIFIED: not executed]`), as the SPEC forbids running code from mined repos.

## Sources read this session (2026-10-29)

- Claude Code MCP docs: https://code.claude.com/docs/en/mcp.md
- OpenCode MCP docs: https://opencode.ai/docs/mcp-servers/
- Each repo's README (downloaded via the GitHub contents API), plus: github-mcp-server `docs/installation-guides/install-claude.md` and `install-opencode.md`; serena `docs/02-usage/030_clients.md`; semgrep `cli/src/semgrep/mcp/README.md`; trivy-mcp `docs/configuration.md`, `docs/ide/claude.md`; gopls `gopls/doc/features/mcp.md`; modelcontextprotocol/servers `src/{git,filesystem,fetch}/README.md`
- https://dbhub.ai/installation · https://docs.snyk.io/agent-security/agentic-security-with-snyk-studio/quickstart-guides/claude-code-guide.md · https://ui.shadcn.com/docs/mcp · https://developer.mozilla.org/en-US/mcp · https://lldb.llvm.org/use/mcp.html · https://www.jetbrains.com/help/idea/mcp-server.html · https://youtrack.jetbrains.com/articles/SUPPORT-A-3223
