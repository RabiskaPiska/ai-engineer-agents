# Scores, sources and freshness: AI-engineer agent pack (2026-10-29)

**How the numbers were made.** Each language agent was written by one author agent and then scored **blind** by a
separate adversarial scorer, using the honest rubric: subtractive, evidence-capped, final = MIN over dimensions.
The scorer had to run checks, not reason from memory. Every defect it found was then fixed (see each fix log in `_work/fixes/`).
**The fixed versions were not re-scored**, because the run used its whole 30-agent budget. So the honest score for
each agent is the blind pre-fix MIN below. **No agent reached 9.7.** The fixes target exactly the logged defects, but
a raised score would need a fresh blind scorer, and none was run.

| Agent | Blind MIN (pre-fix) | Defects logged | Fixed by | Data current to |
|---|---|---|---|---|
| `python-engineer` (Python) | 6.5 | 15 | fixer agent | 2026-10-29 (versions from official release pages) |
| `cpp-engineer` (C++) | 8.4 | 13 | fixer agent | 2026-10-29 (versions from official release pages) |
| `csharp-engineer` (C# / .NET) | 4.0 | 13 | orchestrator (30-agent cap reached) | 2026-10-29 (versions from official release pages) |
| `rust-engineer` (Rust) | 7.0 | 16 | orchestrator (30-agent cap reached) | 2026-10-29 (versions from official release pages) |
| `javascript-engineer` (JavaScript) | 7.0 | 13 | fixer agent | 2026-10-29 (versions from official release pages) |
| `typescript-engineer` (TypeScript) | 7.5 | 14 | fixer agent | 2026-10-29 (versions from official release pages) |
| `go-engineer` (Go) | 7.9 | 11 | fixer agent | 2026-10-29 (versions from official release pages) |
| `java-engineer` (Java) | 6.7 | 10 | fixer agent | 2026-10-29 (versions from official release pages) |
| `kotlin-engineer` (Kotlin) | 6.0 | 10 | fixer agent | 2026-10-29 (versions from official release pages) |
| `web-engineer` (HTML / CSS) | 6.3 | 11 | fixer agent | 2026-10-29 (versions from official release pages) |

## The 5 GitHub repositories behind each agent (re-verified live 2026-10-29 via the GitHub API)

### Python (`python-engineer`)
| # | Repo | Stars | Last push | License |
|---|---|---|---|---|
| 1 | [wshobson/agents](https://github.com/wshobson/agents) | 41,969 | 2026-10-26 | MIT |
| 2 | [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 26,165 | 2026-10-11 | MIT |
| 3 | [trailofbits/skills](https://github.com/trailofbits/skills) | 7,872 | 2026-10-28 | CC-BY-SA-4.0 |
| 4 | [scientific-python/cookie](https://github.com/scientific-python/cookie) | 411 | 2026-10-26 | BSD-3-Clause |
| 5 | [zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) | 18,260 | 2026-08-27 | none stated |
What was taken from each, and the pasted API evidence, is in `sources/python.md`.

### C++ (`cpp-engineer`)
| # | Repo | Stars | Last push | License |
|---|---|---|---|---|
| 1 | [trailofbits/skills](https://github.com/trailofbits/skills) | 7,872 | 2026-10-28 | CC-BY-SA-4.0 |
| 2 | [isocpp/CppCoreGuidelines](https://github.com/isocpp/CppCoreGuidelines) | 45,393 | 2026-10-26 | NOASSERTION |
| 3 | [cpp-best-practices/cmake_template](https://github.com/cpp-best-practices/cmake_template) | 1,818 | 2026-08-17 | Unlicense |
| 4 | [github/awesome-copilot](https://github.com/github/awesome-copilot) | 40,545 | 2026-10-29 | MIT |
| 5 | [wshobson/agents](https://github.com/wshobson/agents) | 41,969 | 2026-10-26 | MIT |
What was taken from each, and the pasted API evidence, is in `sources/cpp.md`.

### C# / .NET (`csharp-engineer`)
| # | Repo | Stars | Last push | License |
|---|---|---|---|---|
| 1 | [dotnet/skills](https://github.com/dotnet/skills) | 5,762 | 2026-10-29 | MIT |
| 2 | [Aaronontheweb/dotnet-skills](https://github.com/Aaronontheweb/dotnet-skills) | 1,242 | 2026-10-28 | MIT |
| 3 | [github/awesome-copilot](https://github.com/github/awesome-copilot) | 40,545 | 2026-10-29 | MIT |
| 4 | [davidfowl/AspNetCoreDiagnosticScenarios](https://github.com/davidfowl/AspNetCoreDiagnosticScenarios) | 8,503 | 2024-05-28 (older; kept as a reference) | none stated |
| 5 | [stryker-mutator/stryker-net](https://github.com/stryker-mutator/stryker-net) | 2,116 | 2026-10-29 | Apache-2.0 |
What was taken from each, and the pasted API evidence, is in `sources/csharp.md`.

### Rust (`rust-engineer`)
| # | Repo | Stars | Last push | License |
|---|---|---|---|---|
| 1 | [morganlinton/BeautifulRust](https://github.com/morganlinton/BeautifulRust) | 1,385 | 2026-10-28 | MIT |
| 2 | [microsoft/rust-guidelines](https://github.com/microsoft/rust-guidelines) | 221 | 2026-10-28 | MIT |
| 3 | [apollographql/rust-best-practices](https://github.com/apollographql/rust-best-practices) | 165 | 2026-10-15 | Apache-2.0 |
| 4 | [leonardomso/rust-skills](https://github.com/leonardomso/rust-skills) | 655 | 2026-06-14 | MIT |
| 5 | [rust-lang/rust-clippy](https://github.com/rust-lang/rust-clippy) | 13,599 | 2026-10-28 | Apache-2.0 |
What was taken from each, and the pasted API evidence, is in `sources/rust.md`.

### JavaScript (`javascript-engineer`)
| # | Repo | Stars | Last push | License |
|---|---|---|---|---|
| 1 | [mcollina/skills](https://github.com/mcollina/skills) | 1,961 | 2026-10-27 | MIT |
| 2 | [goldbergyoni/nodebestpractices](https://github.com/goldbergyoni/nodebestpractices) | 105,684 | 2026-06-15 | CC-BY-SA-4.0 |
| 3 | [antfu/skills](https://github.com/antfu/skills) | 6,023 | 2026-10-23 | MIT |
| 4 | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 111,582 | 2026-10-29 | MIT |
| 5 | [wshobson/agents](https://github.com/wshobson/agents) | 41,969 | 2026-10-26 | MIT |
What was taken from each, and the pasted API evidence, is in `sources/javascript.md`.

### TypeScript (`typescript-engineer`)
| # | Repo | Stars | Last push | License |
|---|---|---|---|---|
| 1 | [typescript-eslint/typescript-eslint](https://github.com/typescript-eslint/typescript-eslint) | 16,458 | 2026-10-28 | MIT |
| 2 | [microsoft/TypeScript](https://github.com/microsoft/TypeScript) | 111,662 | 2026-10-29 | Apache-2.0 |
| 3 | [Jeffallan/claude-skills](https://github.com/Jeffallan/claude-skills) | 12,125 | 2026-10-29 | MIT |
| 4 | [wshobson/agents](https://github.com/wshobson/agents) | 41,969 | 2026-10-26 | MIT |
| 5 | [mattpocock/skills](https://github.com/mattpocock/skills) | 306,125 | 2026-10-29 | MIT |
What was taken from each, and the pasted API evidence, is in `sources/typescript.md`.

### Go (`go-engineer`)
| # | Repo | Stars | Last push | License |
|---|---|---|---|---|
| 1 | [samber/cc-skills-golang](https://github.com/samber/cc-skills-golang) | 3,721 | 2026-10-23 | MIT |
| 2 | [uber-go/guide](https://github.com/uber-go/guide) | 17,756 | 2026-04-15 | Apache-2.0 |
| 3 | [google/styleguide](https://github.com/google/styleguide) | 39,773 | 2026-10-29 | NOASSERTION |
| 4 | [wshobson/agents](https://github.com/wshobson/agents) | 41,969 | 2026-10-26 | MIT |
| 5 | [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 26,165 | 2026-10-11 | MIT |
What was taken from each, and the pasted API evidence, is in `sources/go.md`.

### Java (`java-engineer`)
| # | Repo | Stars | Last push | License |
|---|---|---|---|---|
| 1 | [github/awesome-copilot](https://github.com/github/awesome-copilot) | 40,545 | 2026-10-29 | MIT |
| 2 | [jabrena/plinth](https://github.com/jabrena/plinth) | 456 | 2026-10-29 | Apache-2.0 |
| 3 | [google/error-prone](https://github.com/google/error-prone) | 7,263 | 2026-10-29 | Apache-2.0 |
| 4 | [uber/NullAway](https://github.com/uber/NullAway) | 4,126 | 2026-10-28 | MIT |
| 5 | [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 26,165 | 2026-10-11 | MIT |
What was taken from each, and the pasted API evidence, is in `sources/java.md`.

### Kotlin (`kotlin-engineer`)
| # | Repo | Stars | Last push | License |
|---|---|---|---|---|
| 1 | [Kotlin/kotlin-agent-skills](https://github.com/Kotlin/kotlin-agent-skills) | 1,100 | 2026-10-28 | Apache-2.0 |
| 2 | [Kotlin/kotlinx.coroutines](https://github.com/Kotlin/kotlinx.coroutines) | 13,822 | 2026-10-28 | Apache-2.0 |
| 3 | [chrisbanes/skills](https://github.com/chrisbanes/skills) | 1,127 | 2026-10-27 | Apache-2.0 |
| 4 | [maxrave-dev/kotlin-footguns](https://github.com/maxrave-dev/kotlin-footguns) | 1,747 | 2026-10-29 | GPL-3.0 |
| 5 | [android/skills](https://github.com/android/skills) | 10,009 | 2026-10-29 | Apache-2.0 |
What was taken from each, and the pasted API evidence, is in `sources/kotlin.md`.

### HTML / CSS (`web-engineer`)
| # | Repo | Stars | Last push | License |
|---|---|---|---|---|
| 1 | [GoogleChrome/modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance) | 2,573 | 2026-10-26 | Apache-2.0 |
| 2 | [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) | 1,061 | 2026-10-05 | MIT |
| 3 | [addyosmani/web-quality-skills](https://github.com/addyosmani/web-quality-skills) | 3,006 | 2026-08-24 | MIT |
| 4 | [vojtaholik/good-css](https://github.com/vojtaholik/good-css) | 395 | 2026-10-10 | MIT |
| 5 | [web-platform-dx/web-features](https://github.com/web-platform-dx/web-features) | 952 | 2026-10-29 | Apache-2.0 |
What was taken from each, and the pasted API evidence, is in `sources/web.md`.

## License handling
Repos under MIT or Apache-2.0 were adapted, with attribution in `sources/`. Repos under CC-BY-SA-4.0, GPL-3.0, NOASSERTION
or with no license were **paraphrased only**; no text was copied. No code from any mined repo was executed.
