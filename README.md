# AI-engineer agent pack: 10 language-expert agents (October 2026)

One expert AI-engineer agent per language, each with its own skill (a deep rule catalog plus verification
gates) and its own MCP servers. They are built for writing real applications, not one-off snippets.

| Agent | Language | Own skill | MCP servers it declares |
|---|---|---|---|
| `python-engineer` | Python | `python-engineering` | see the agent's frontmatter `mcpServers` |
| `cpp-engineer` | C++ | `cpp-engineering` | 〃 |
| `csharp-engineer` | C# / .NET | `csharp-engineering` | 〃 |
| `rust-engineer` | Rust | `rust-engineering` | 〃 |
| `javascript-engineer` | JavaScript (Node + browser) | `javascript-engineering` | 〃 |
| `typescript-engineer` | TypeScript | `typescript-engineering` | 〃 |
| `go-engineer` | Go | `go-engineering` | 〃 |
| `java-engineer` | Java | `java-engineering` | 〃 |
| `kotlin-engineer` | Kotlin | `kotlin-engineering` | 〃 |
| `web-engineer` | HTML / CSS | `web-engineering` | 〃 |

Each agent works in the same loop: understand, plan, write a failing test, implement, run its gates, report with the gate output
pasted. It has a `## Delegation` section for spawning its own test-writer, reviewer, security-auditor and
researcher subagents.

## What's in the ZIP

```
claude/agents/*.md          Claude Code agents (frontmatter: name, description, model, skills, mcpServers)
claude/skills/*/SKILL.md    the matching skills (+ references/)
opencode/agents/*.md        OpenCode builds of the same agents (mode: subagent)
opencode/skills/            the same skills, for ~/.config/opencode/skills
opencode/opencode-mcp.jsonc the MCP servers the agents expect, in OpenCode's "mcp" format
sources/<lang>.md           the 5 GitHub repos behind each agent, with live API evidence and what was taken
catalog/MCP-SERVERS-2026-10.md        45 verified MCP servers for software engineering, per language
catalog/SKILLS-AND-AGENTS-2026-10.md  39 verified skill and agent collections worth borrowing from
SCORES.md                   the blind honest score of every agent, plus a table of the 5 repos with live stars, last push and license
install.ps1 / install.sh    installers (they back up anything they replace)
```

## Install

**Windows (your main PC).** Unzip, open PowerShell in the folder, then:
```powershell
.\install.ps1              # Claude Code: %USERPROFILE%\.claude\agents + \skills
.\install.ps1 -OpenCode    # OpenCode:    %USERPROFILE%\.config\opencode\agents + \skills
```
**Linux / macOS:** `./install.sh` or `./install.sh --opencode`.

For OpenCode, merge `opencode/opencode-mcp.jsonc` into your `opencode.jsonc` (the `"mcp"` block). In Claude Code
the MCP servers come with each agent: inline `mcpServers` start when that agent runs. `github` is referenced by
name, so configure it once. Some servers need a one-time `cargo install`, `go install` or `uvx`; the
agent's `## MCP and skills usage` section says which.

## Using them from a prefix message

Name the agents you want and the work each one owns. For example:

```
Build <app>. Use the python-engineer agent for the API service and the typescript-engineer agent for the
web client. Each runs its own gates and pastes the output. Then run a security review over both.
```

Claude Code also picks an agent on its own when a task matches its description ("Use PROACTIVELY for …").

## Honest status

Read `SCORES.md`. Every agent was blind-scored by a separate adversarial agent, and every logged defect then
got a fix pass. **None reached 9.7.** The pre-fix blind scores run from 4.0 to 8.4, and the fixed versions were
not re-scored, because the run used its whole 30-agent budget. What is still open is listed in `_work/fixes/<lang>.md`
and in each score file under `_work/scores/`.
