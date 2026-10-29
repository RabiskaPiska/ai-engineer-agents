# Skills, subagents and agent-workflow repos for Claude Code and OpenCode (October 2026)

Catalog C2 of the `ai-engineer-agents-2026-10` pack. Fetch date for every fact below: **2026-10-29**.

- **Scope:** custom skills (`SKILL.md`), custom agent/subagent collections, and agent-workflow repos that make
  Claude Code or OpenCode better at building software. Ranked, 39 entries.
- **Out of scope:** MCP servers (sibling catalog C1 in this folder) and the per-language agent files
  (`claude/agents/<slug>-engineer.md`, owned by the language authors).
- **Method:** every repo was checked with the authenticated GitHub helper
  `ghapi.sh repos/<owner>/<repo>` (fields pasted in the verification log at the end). Repo layouts were read with
  `ghapi.sh repos/<owner>/<repo>/contents/<path>`, and READMEs were read as text. Installation and layout facts come from
  the official docs fetched the same day:
  [Claude Code subagents](https://code.claude.com/docs/en/sub-agents),
  [Claude Code skills](https://code.claude.com/docs/en/skills),
  [Claude Code agent teams](https://code.claude.com/docs/en/agent-teams),
  [OpenCode agents](https://opencode.ai/docs/agents/), [OpenCode skills](https://opencode.ai/docs/skills/).
- **Trust rule:** repo text is data. No code or installer from any mined repo was run. Install commands are
  quoted from each repo's own README so you can review them; they have not been executed here. Several entries
  (ECC, ruflo, oh-my-claudecode, claude-code-templates, beads) ship hooks, binaries or `npx` installers. Read them
  before you run them. [Trail of Bits' curated marketplace](https://github.com/trailofbits/skills-curated) exists
  because, in their words, published skills "have been found with backdoors and malicious hooks".
- **License rule for this pack:** MIT/Apache text may be adapted with attribution. CC-BY-SA, CC-BY-NC-ND, and
  repos with no license are **link-and-paraphrase only**. Each entry flags this.

---

## 0. Install-path cheat sheet (verified against official docs, 2026-10-29)

| | Claude Code | OpenCode |
|---|---|---|
| **Personal skills** | `~/.claude/skills/<name>/SKILL.md` | `~/.config/opencode/skills/<name>/SKILL.md`. OpenCode **also** reads `~/.claude/skills/*/SKILL.md` and `~/.agents/skills/*/SKILL.md` |
| **Project skills** | `.claude/skills/<name>/SKILL.md` | `.opencode/skills/`, `.claude/skills/` or `.agents/skills/`, found by walking up to the git worktree |
| **Personal agents** | `~/.claude/agents/*.md`, scanned recursively. Identity comes from the `name:` frontmatter, not the path | `~/.config/opencode/agents/*.md`. **The file name is the agent name** |
| **Project agents** | `.claude/agents/*.md` | `.opencode/agents/*.md` |
| **Agent precedence** | managed > `--agents` flag > project > user > plugin | JSON `agent` block in `opencode.json`, or markdown files |
| **Plugins** | `/plugin marketplace add <owner/repo>` then `/plugin install <plugin>@<marketplace>`. Shell form: `claude plugin install …` | `"plugin": [...]` in `opencode.json`. OpenCode 1.x uses the singular key, per the compound-engineering README |

**Format facts that matter for porting:**

1. **Skills port almost unchanged.** Both tools read Agent Skills (`name` and `description` frontmatter, per the
   [agentskills.io spec](https://agentskills.io/specification)). OpenCode requires `name` to match
   `^[a-z0-9]+(-[a-z0-9]+)*$` and the folder name, and `description` to be 1–1024 characters. Unknown frontmatter
   keys are ignored. The easy route is one copy in `~/.claude/skills/`, which both tools load.
2. **Agents do not port as-is.** OpenCode's agent docs list only `~/.config/opencode/agents/` and `.opencode/agents/`
   as markdown agent locations, so Claude `.claude/agents/*.md` files are not loaded natively. To convert a Claude agent:
   - Keep `description`.
   - Add `mode: subagent`.
   - Drop `name`, because the file name becomes the name.
   - Map `tools:` allowlists to OpenCode `permission:`, for example `edit: deny`, `bash: deny`. OpenCode marks
     `tools` as deprecated.
   - Drop `model: inherit`. An OpenCode subagent with no `model` uses the invoking primary agent's model, which
     matches Claude's `inherit`.
   - Otherwise use `provider/model-id`.
   - Claude-only fields such as `skills:`, `mcpServers:`, `hooks:`, `memory:` and `isolation:` have no 1:1 OpenCode
     equivalent. Move skills into the body ("load skill X") and MCP servers into `opencode.json`.
3. **Multi-harness repos already ship OpenCode builds.** For wshobson/agents, superpowers, ECC, compound-engineering
   and addyosmani, prefer the repo's own OpenCode route over hand conversion.
4. **`npx skills` (vercel-labs/skills) install targets**, from its `docs/agents.md`: Claude Code →
   `.claude/skills/` (project) or `~/.claude/skills/` (`-g`). OpenCode → `.agents/skills/` (project) or
   `~/.config/opencode/skills/` (`-g`).
5. **Claude Code nesting:** a subagent can spawn its own subagents up to **three layers** below the main
   conversation by default. `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` changes the limit.
   **Agent teams** are experimental and need `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. They do not spawn in `-p` or
   Agent SDK sessions. Source: the sub-agents and agent-teams docs above.

---

## 1. Ranked summary

Ranking weighs, in order:
- (a) direct value for building real software with a language-expert agent pack
- (b) evidence of quality, such as tests, evals, vetted maintainers or a vendor owner
- (c) maintenance (pushed in the last 30 days scores best)
- (d) license freedom to adapt
- (e) adoption (stars), used only as a tiebreaker

Stars are noisy in 2026: several repos passed 200k stars inside a year, so they rank nothing alone.

| # | Repo | ★ | pushed_at | License | Kind | Take first |
|---|---|---:|---|---|---|---|
| 1 | [obra/superpowers](https://github.com/obra/superpowers) | 307,818 | 2026-10-23 | MIT | skills methodology | TDD, systematic-debugging, verification, subagent-driven-development (2-stage review) |
| 2 | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) | 45,193 | 2026-10-29 | Apache-2.0 | official plugins | `code-review` (4 parallel agents, ≥80 confidence), `pr-review-toolkit`, `feature-dev`, 8 language-LSP plugins |
| 3 | [anthropics/skills](https://github.com/anthropics/skills) | 184,622 | 2026-10-28 | per-skill (Apache-2.0 examples; docx/pdf/pptx/xlsx source-available) | official skills | `skill-creator` eval loop, `mcp-builder`, `webapp-testing`, Agent Skills spec |
| 4 | [mattpocock/skills](https://github.com/mattpocock/skills) | 306,088 | 2026-10-27 | MIT | skills | `tdd`, `diagnosing-bugs`, two-axis `code-review`, `implement-spec` task-graph |
| 5 | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 111,565 | 2026-10-29 | MIT | skills + 4 personas | anti-rationalization tables, `orchestration-patterns.md`, security/test personas |
| 6 | [wshobson/agents](https://github.com/wshobson/agents) | 41,968 | 2026-10-26 | MIT | 202 agents / 185 skills | `*-pro` language agents, `agent-teams` plugin, `make install-opencode` |
| 7 | [trailofbits/skills](https://github.com/trailofbits/skills) | 7,872 | 2026-10-28 | CC-BY-SA-4.0 | security skills | `c-review`, `rust-review`, `differential-review`, `insecure-defaults`, `fp-check`, `modern-python`, `modern-cpp` |
| 8 | [affaan-m/ECC](https://github.com/affaan-m/ECC) (was everything-claude-code) | 292,109 | 2026-10-26 | MIT | harness: agents+skills+rules | per-language `*-reviewer` + `*-build-resolver` agents; per-language `rules/` |
| 9 | [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 26,164 | 2026-10-11 | MIT | 161 subagents | language specialists for all 10 pack languages; meta-orchestration agents |
| 10 | [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) | 25,762 | 2026-10-29 | MIT | workflow plugin (36 skills) | `ce-code-review` persona catalog + findings schema; `ce-compound` learning capture |
| 11 | [Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | 40,382 | 2026-10-29 | MIT | team orchestration | `team-plan → prd → exec → verify → fix` pipeline; `verifier`/`critic`/`tracer` agents |
| 12 | [github/spec-kit](https://github.com/github/spec-kit) | 143,778 | 2026-10-28 | MIT | spec-driven workflow | constitution → spec → plan → tasks → implement |
| 13 | [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | 73,307 | 2026-10-28 | MIT | spec-driven workflow | light `/opsx:propose → apply → archive` change folders |
| 14 | [dotnet/skills](https://github.com/dotnet/skills) | 5,762 | 2026-10-29 | MIT | **official** C#/.NET skills | 17 plugins: msbuild, nuget, diag, test, aspnetcore, upgrade, data |
| 15 | [samber/cc-skills-golang](https://github.com/samber/cc-skills-golang) | 3,719 | 2026-10-23 | MIT | Go skills | 46 `golang-*` skills (concurrency, error-handling, security, performance, gopls) |
| 16 | [Kotlin/kotlin-agent-skills](https://github.com/Kotlin/kotlin-agent-skills) | 1,100 | 2026-10-28 | Apache-2.0 | **official** Kotlin skills | java-to-kotlin, JPA entity mapping, AGP 9, Gradle toolchain |
| 17 | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | 33,186 | 2026-10-28 | none at repo level | vendor skills (React/web) | `react-best-practices`, `web-design-guidelines`, `composition-patterns` |
| 18 | [getsentry/skills](https://github.com/getsentry/skills) | 1,098 | 2026-10-26 | Apache-2.0 | vendor-internal eng skills | `code-review`, `find-bugs`, `security-review`, `gha-security-review`, `iterate-pr` |
| 19 | [microsoft/skills](https://github.com/microsoft/skills) | 3,155 | 2026-10-28 | MIT | vendor SDK skills | Azure SDK skills for Python, .NET, TypeScript, Java, Rust; role agents |
| 20 | [leonardomso/rust-skills](https://github.com/leonardomso/rust-skills) | 654 | 2026-06-14 | MIT | Rust rules skill | indexed rule files (ownership, errors, async, unsafe, clippy) |
| 21 | [Jeffallan/claude-skills](https://github.com/Jeffallan/claude-skills) | 12,124 | 2026-10-29 | MIT | 67 dev skills | `python-pro`, `rust-engineer`, `cpp-pro`, `golang-pro`, `kotlin-specialist`, `typescript-pro` skills |
| 22 | [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | 54,721 | 2026-10-27 | MIT (+trademark) | agile multi-role workflow | analyst/PM/architect/dev/QA role hand-offs |
| 23 | [OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files) | 27,747 | 2026-10-28 | MIT | memory skill | `task_plan.md` / `findings.md` / `progress.md` survives `/clear` |
| 24 | [gastownhall/beads](https://github.com/gastownhall/beads) (was steveyegge/beads) | 28,281 | 2026-10-29 | MIT | agent issue-graph memory | dependency-aware task graph CLI `bd` |
| 25 | [muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) | 18,237 | 2026-10-12 | MIT | meta skills | `multi-agent-patterns`, `context-degradation`, `long-horizon-prompting` |
| 26 | [alvinunreal/oh-my-opencode-slim](https://github.com/alvinunreal/oh-my-opencode-slim) | 9,844 | 2026-10-29 | MIT | **OpenCode-native** orchestration | Orchestrator / Explorer / Oracle / Librarian / Designer / Fixer roles |
| 27 | [humanlayer/humanlayer](https://github.com/humanlayer/humanlayer) | 12,694 | 2026-10-29 | Apache-2.0 | workflow + steering app | Research-Plan-Implement (RPI) skills plugin |
| 28 | [open-gsd/gsd-core](https://github.com/open-gsd/gsd-core) (successor of gsd-build/get-shit-done) | 10,988 | 2026-10-29 | MIT | meta-prompting / SDD | phase plans with fresh-context executors |
| 29 | [snarktank/ralph](https://github.com/snarktank/ralph) | 22,083 | 2026-02-02 | MIT | loop runner | PRD-item loop until done (also official `ralph-loop` plugin) |
| 30 | [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) | 32,964 | 2026-10-29 | MIT | component installer | `npx claude-code-templates --agent …` picker |
| 31 | [SuperClaude-Org/SuperClaude_Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework) | 23,916 | 2026-09-27 | MIT | commands + personas | 30 slash commands, cognitive personas |
| 32 | [ruvnet/ruflo](https://github.com/ruvnet/ruflo) (was claude-flow) | 80,044 | 2026-10-29 | MIT | swarm harness | swarm/queen-worker ideas; heavy, partly MCP |
| 33 | [trailofbits/claude-code-config](https://github.com/trailofbits/claude-code-config) | 2,143 | 2026-08-24 | none | config defaults | sandbox, permission and hook defaults from a security firm |
| 34 | [trailofbits/skills-curated](https://github.com/trailofbits/skills-curated) | 522 | 2026-07-14 | CC-BY-SA-4.0 | vetted marketplace | a reviewed allowlist of third-party plugins |
| 35 | [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) | 226,164 | 2026-04-20 | none | single CLAUDE.md | 4 anti-overengineering principles (paraphrase only) |
| 36 | [vercel-labs/skills](https://github.com/vercel-labs/skills) | 37,084 | 2026-10-29 | MIT | installer CLI (`npx skills`) | cross-agent skill install with verified Claude/OpenCode paths |
| 37 | [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 36,542 | 2026-10-29 | MIT | curated index | discovery of vendor-official skills |
| 38 | [github/awesome-copilot](https://github.com/github/awesome-copilot) | 40,541 | 2026-10-29 | MIT | Copilot agents/instructions | per-language instruction files (need format conversion) |
| 39 | [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 56,798 | 2026-10-29 | CC-BY-NC-ND-4.0 (NOASSERTION in API) | curated index | discovery only; no derivatives allowed |

Reference, not ranked: [anomalyco/opencode](https://github.com/anomalyco/opencode), formerly sst/opencode (222,892★,
pushed 2026-10-29, MIT). The OpenCode docs site showed an "OpenCode v2 is now available" banner on 2026-10-29. The
paths above come from the docs as served that day.

---

## 2. Entries in detail

Language keys used below: **py** python · **cpp** C++ · **cs** C#/.NET · **rs** Rust · **js** JavaScript ·
**ts** TypeScript · **go** Go · **java** Java · **kt** Kotlin · **web** HTML/CSS. "All" means language-agnostic process
that applies to every pack agent.

### 1. obra/superpowers: the methodology layer
- **Verified:** MIT · 307,818★ · pushed 2026-10-23 · not archived.
- **What it is:** 15 composable skills under `skills/`: `brainstorming`, `writing-plans`, `executing-plans`,
  `subagent-driven-development`, `dispatching-parallel-agents`, `test-driven-development`, `systematic-debugging`,
  `verification-before-completion`, `requesting-code-review`, `receiving-code-review`, `using-git-worktrees`,
  `finishing-a-development-branch`, `writing-skills`, `using-superpowers` and `diagnosing-superpowers`.
  A `hooks/session-start` bootstrap tells the agent to use them.
- **Worth taking:**
  - `subagent-driven-development` ships separate `implementer-prompt.md`, `task-reviewer-prompt.md` and
    `re-review-prompt.md`. The README describes it as "two-stage review (spec compliance, then code quality)". This
    is the cleanest implementer → reviewer hand-off pattern in the catalog.
  - `verification-before-completion` matches the pack's "paste gate output" rule.
  - `writing-skills` brings a test methodology for skills. The README points to an eval harness (`superpowers-evals`).
- **Languages:** All (process). No language-specific content.
- **Claude Code:**
  - Plugin: `/plugin install superpowers@claude-plugins-official`.
  - Manual: copy `skills/<name>/` to `~/.claude/skills/`. There are no agent files.
  - Without the plugin you lose the session-start hook, so name the skill in each agent's `skills:` list instead.
- **OpenCode:** the repo ships `.opencode/INSTALL.md`. The README says to tell OpenCode to fetch and follow that
  file. Alternatively copy `skills/*` to `~/.config/opencode/skills/`.
- **Caveat:** the README warns that the brainstorming visual companion loads a logo from the vendor site by default.
  It calls this telemetry.

### 2. anthropics/claude-plugins-official: Anthropic's plugin directory
- **Verified:** Apache-2.0 (per-plugin LICENSE files, e.g. `plugins/feature-dev/LICENSE` is Apache-2.0) · 45,193★ ·
  pushed 2026-10-29.
- **What it is:** `plugins/` holds Anthropic-maintained plugins and `external_plugins/` holds partner plugins.
  Development-relevant plugins seen in `plugins/`: `code-review`, `pr-review-toolkit`, `feature-dev`,
  `code-simplifier`, `security-guidance`, `hookify`, `plugin-dev`, `skill-creator`, `agent-sdk-dev`, `mcp-server-dev`,
  `ralph-loop`, `commit-commands`, `claude-md-management` and `code-modernization`, plus language-server plugins.
- **Worth taking:**
  - **`code-review`** command (README): skips trivial or already-reviewed PRs and collects CLAUDE.md files. It then
    launches **4 parallel agents**: 2 check CLAUDE.md compliance, 1 hunts obvious bugs, 1 analyses git blame and
    history. Each issue is scored 0–100 and anything below **80** is dropped. Copy this confidence-gate design into
    every reviewer seat.
  - **`pr-review-toolkit`** agents: `code-reviewer`, `code-simplifier`, `comment-analyzer`, `pr-test-analyzer`,
    `silent-failure-hunter`, `type-design-analyzer`. These are good single-dimension reviewer templates.
    `silent-failure-hunter` targets swallowed errors in every language.
  - **`feature-dev`** has a 7-phase flow. It launches 2–3 parallel `code-explorer` agents, asks clarifying
    questions, has `code-architect` design, then runs `code-reviewer`. Good research-then-design seating.
  - **LSP plugins** give per-language code intelligence: `clangd-lsp` (cpp), `csharp-lsp` (cs), `gopls-lsp` (go),
    `jdtls-lsp` (java), `kotlin-lsp` (kt), `pyright-lsp` (py), `rust-analyzer-lsp` (rs), `typescript-lsp` (js/ts).
    These map directly onto the pack's languages.
- **Languages:** All, plus LSP plugins for 9 of the 10 pack languages (web uses typescript-lsp for JS in HTML).
- **Claude Code:**
  - Install: `/plugin install <name>@claude-plugins-official`.
  - Manual: copy `plugins/<p>/agents/*.md` to `~/.claude/agents/` and `plugins/<p>/skills/*` to `~/.claude/skills/`.
- **OpenCode:** no native adapter. Convert agent files (see §0) into `~/.config/opencode/agents/`. The LSP plugins
  are Claude-specific; OpenCode has its own LSP configuration.

### 3. anthropics/skills: reference skills and the spec
- **Verified:** no repo-level license (API `null`) · 184,622★ · pushed 2026-10-28.
  - `skills/skill-creator/LICENSE.txt` is Apache-2.0.
  - `skills/docx/LICENSE.txt` reads "© 2025 Anthropic, PBC. All rights reserved", and the README calls the
    docx/pdf/pptx/xlsx skills "source-available, not open source".
- **What it is:** 19 skills plus `spec/` (Agent Skills specification) and `template/`.
- **Worth taking:**
  - `skill-creator` ships `agents/`, `eval-viewer/` and `scripts/`, so it can test skills. Use it to evaluate the
    pack's `<slug>-engineering` skills.
  - `mcp-builder`, for any agent that builds MCP servers.
  - `webapp-testing`, a Playwright-based check of local web apps (web/js/ts).
  - `claude-api`.
- **Languages:** web/js/ts (`webapp-testing`, `frontend-design`); others process.
- **Claude Code:**
  - Install: `/plugin marketplace add anthropics/skills`, then `/plugin install example-skills@anthropic-agent-skills`.
  - Manual: copy `skills/<name>/` to `~/.claude/skills/`.
- **OpenCode:** copy to `~/.config/opencode/skills/`, or leave the files in `~/.claude/skills/`, which OpenCode also reads.
- **License action:** adapt only the Apache-2.0 skills. Do not copy docx/pdf/pptx/xlsx.

### 4. mattpocock/skills: small, composable engineering skills
- **Verified:** MIT · 306,088★ · pushed 2026-10-27.
- **What it is:** a `skills/engineering/*` and `skills/productivity/*` set. The README positions it against
  process-owning frameworks: "Approaches like GSD, BMAD, and Spec-Kit try to help by owning the process… these
  skills are designed to be small, easy to adapt, and composable."
- **Worth taking:**
  - `tdd`: red-green-refactor, one vertical slice at a time.
  - `diagnosing-bugs`: build a loop that goes red on the bug → minimise → hypothesise → instrument → fix →
    regression-test.
  - `code-review`: two axes, **Standards** and **Spec**, "run as parallel sub-agents so neither pollutes the other".
  - `implement-spec`: works tickets as a task graph, with implementer subagents across the ready frontier.
  - `grill-with-docs`: an interview that builds `GLOSSARY.md` and ADRs.
  - `research`: a background agent that writes cited findings.
- **Languages:** All (process). Some TS-specific productivity skills, such as shoehorn migrations, are listed by
  third parties. **[UNVERIFIED]** for this repo.
- **Claude Code:**
  - Install: `claude plugin install mattpocock-skills@claude-plugins-official`.
  - Manual: copy `skills/engineering/<name>/` to `~/.claude/skills/`.
  - Run `/setup-matt-pocock-skills` once per repo.
- **OpenCode:** `npx skills@latest add mattpocock/skills -a opencode` (README) installs to OpenCode's skill path.
  The README warns against installing both the plugin and skills.sh, because you then get every skill twice.

### 5. addyosmani/agent-skills: lifecycle skills with anti-rationalization
- **Verified:** MIT · 111,565★ · pushed 2026-10-29.
- **What it is:** 25 skills (24 lifecycle skills plus the `using-agent-skills` meta skill), 9 slash commands
  (`/spec /plan /build /test /constraints /review /webperf /code-simplify /ship`), 4 personas in `agents/`
  (`code-reviewer`, `test-engineer`, `security-auditor`, `web-performance-auditor`), and 7 checklists in `references/`.
- **Worth taking:**
  - **Anti-rationalization tables.** Each skill lists the excuses an agent uses to skip a step and answers each one.
    This maps directly onto the pack's "Anti-patterns" section.
  - `doubt-driven-development`: fresh-context adversarial review (CLAIM → EXTRACT → DOUBT → RECONCILE → STOP).
  - `security-and-hardening`.
  - `references/orchestration-patterns.md`, a catalog of endorsed and anti-patterns. See §4.
- **Languages:**
  - All.
  - web/js/ts: `frontend-ui-engineering`, the `/webperf` auditor.
- **Claude Code:**
  - Install: `/plugin marketplace add addyosmani/agent-skills`, then `/plugin install agent-skills@addy-agent-skills`.
  - Manual: copy `skills/*` to `~/.claude/skills/` and `agents/*.md` to `~/.claude/agents/`.
- **OpenCode:** the README says to copy skills to `.opencode/skills/` or `~/.config/opencode/skills/`, add
  `AGENTS.md`, and see `docs/opencode-setup.md`. Convert `agents/*.md` per §0.

### 6. wshobson/agents: the largest maintained multi-harness agent library
- **Verified:** MIT · 41,968★ · pushed 2026-10-26.
- **What it is:** per the README, 94 plugins (92 local) holding 202 agents, 185 skills and 105 commands. A single
  Markdown source is adapted to Claude Code, Codex, Cursor, OpenCode, Antigravity, Copilot and Pi. CI checks structure
  (`make validate STRICT=1`), and `plugin-eval` gives static skill scoring. The README says the LLM-judge layer "is
  not validated against human labels".
- **Worth taking:**
  - Language agents:
    - `plugins/systems-programming/agents/{c-pro,cpp-pro,golang-pro,rust-pro}.md`
    - `plugins/jvm-languages/agents/{csharp-pro,java-pro,scala-pro}.md`
    - `plugins/python-development/agents/{python-pro,django-pro,fastapi-pro}.md`, with 16 Python skills such as
      `python-type-safety`, `python-testing-patterns` and `uv-package-manager`
    - `plugins/javascript-typescript/agents/{javascript-pro,typescript-pro}.md`
    - `plugins/dotnet-contribution/agents/dotnet-architect.md`
  - **`plugins/agent-teams`**: `team-lead`, `team-reviewer`, `team-debugger` and `team-implementer`, with commands
    `/team-review`, `/team-debug` and `/team-feature`. Per the README, implementers work "within strict file ownership
    boundaries".
  - `comprehensive-review` and `full-stack-orchestration`, for reviewer and security seats.
- **Languages:**
  - py, cpp, cs, rs, js, ts, go and java have dedicated agents.
  - kt: only via `jvm-languages` and `functional-programming`. **[UNVERIFIED]** whether a Kotlin agent exists.
  - web: via `frontend-mobile-development` and `accessibility-compliance`.
- **Claude Code:**
  - Install: `/plugin marketplace add wshobson/agents`, then `/plugin install python-development@claude-code-workflows`.
  - Manual: copy `plugins/<p>/agents/*.md` to `~/.claude/agents/` and `plugins/<p>/skills/*` to `~/.claude/skills/`.
  - Skills only: `npx skills add wshobson/agents --skill <name>`, or `gh skill install wshobson/agents <name>`
    (needs gh ≥ 2.90 per README).
- **OpenCode:** `make install-opencode` from a clone (README; needs uv and Python ≥ 3.12). It generates agents with
  translated tool permissions.

### 7. trailofbits/skills: the security seat
- **Verified:** **CC-BY-SA-4.0** · 7,872★ · pushed 2026-10-28.
- **What it is:** a security-firm marketplace with a "Trophy Case" of bugs found using it.
- **Worth taking (paraphrase only):**
  - **Per-language reviewers:**
    - `c-review` (C/C++ security review, "coverage verified against a parse of the source", ships `agents/` and
      `workflows/`)
    - `rust-review` (unsafe boundary, FFI, panic-DoS, async; SARIF output)
    - `modern-python` (uv, ruff, pytest)
    - `modern-cpp` (C++20/23/26 with compiler hardening)
    - `zeroize-audit` (C/C++/Rust)
    - `constant-time-analysis`
  - **Reviewer-quality controls:**
    - `fp-check` (false-positive verification with gate reviews)
    - `insecure-defaults` ("a refuting verifier per candidate file")
    - `differential-review` (diff + git history)
    - `variant-analysis`
    - `static-analysis` (CodeQL, Semgrep, SARIF)
    - `supply-chain-risk-auditor` (npm, PyPI, Go)
    - `property-based-testing` (Hypothesis, fast-check, proptest)
    - `mutation-testing`
  - **Dev:** `second-opinion` (independent review from another model) and `devcontainer-setup`.
- **Languages:** cpp, rs and py are strong. js/ts are covered via `property-based-testing` (fast-check) and
  `supply-chain-risk-auditor` (npm). go via supply-chain. All languages via `differential-review` and `fp-check`.
- **Claude Code:**
  - Install: `/plugin marketplace add trailofbits/skills`, then `/plugin menu`.
  - Manual: copy `plugins/<p>/skills/*` to `~/.claude/skills/` and `plugins/<p>/agents/*` to `~/.claude/agents/`.
- **OpenCode:** copy the skills to `~/.config/opencode/skills/`. Convert agents per §0.
- **License action:** CC-BY-SA. Link these from the pack and do not copy their text into the MIT pack.

### 8. affaan-m/ECC: per-language reviewer and build-fixer pairs
- **Verified:** MIT · 292,109★ · pushed 2026-10-26. Repo renamed from `affaan-m/everything-claude-code`; the API
  redirects.
- **What it is:** a large harness. Its README, as fetched, lists 71 agents, skills, hooks and opt-in `rules/`.
  It has adapters for Codex, Cursor, OpenCode (beta), Copilot and more.
- **Worth taking:**
  - The agent naming shows a two-seat pattern per language: `cpp-reviewer`/`cpp-build-resolver`,
    `go-reviewer`/`go-build-resolver`, `java-…`, `kotlin-…`, `rust-…`, plus `python-reviewer`, `typescript-reviewer`,
    `csharp-reviewer`, `react-reviewer` and `database-reviewer`.
  - Generic seats: `planner`, `architect`, `tdd-guide`, `security-reviewer`, `silent-failure-hunter`,
    `type-design-analyzer`.
  - `rules/` packs exist for `cpp, csharp, golang, java, kotlin, python, rust, typescript, web` and more.
- **Languages:** all 10. js is covered via `typescript-reviewer` and the `react` rules.
- **Claude Code:**
  - Install: `/plugin marketplace add https://github.com/affaan-m/ECC`, then `/plugin install ecc@ecc`.
  - Manual: `cp agents/*.md ~/.claude/agents/` and `cp -r .agents/skills/* ~/.claude/skills/`. Then copy
    `rules/common` plus **one** language pack to `~/.claude/rules/ecc/`.
  - The README itself says rules are "always loaded, so install them selectively". It also warns against mixing the
    plugin install with `install.sh --profile full`.
- **OpenCode:** `npm install && npm run build:opencode && ./install.sh --profile full --target opencode --enable-hooks`
  (README; beta).
- **Caveat:** heavy hooks and an installer. Take individual agent files, not the whole harness.

### 9. VoltAgent/awesome-claude-code-subagents: broadest subagent catalog
- **Verified:** MIT · 26,164★ · pushed 2026-10-11.
- **What it is:** 161 subagents across 10 categories (`categories/NN-*/<agent>.md`), each category also shipped as a
  plugin (`voltagent-lang`, `voltagent-infra`, `voltagent-meta`, …).
- **Worth taking:**
  - `02-language-specialists` has an agent for every pack language: `python-pro`, `cpp-pro`, `csharp-developer`,
    `dotnet-core-expert`, `rust-engineer`, `javascript-pro`, `typescript-pro`, `node-specialist`, `golang-pro`,
    `java-architect`, `spring-boot-engineer`, `kotlin-specialist`.
  - web is covered in `01-core-development` (`frontend-developer`, `ui-designer`), plus `accessibility-tester`.
  - `09-meta-orchestration` has `agent-organizer`, `multi-agent-coordinator`, `workflow-orchestrator`,
    `task-distributor`, `context-manager`, `knowledge-synthesizer` and `error-coordinator`.
- **Caveat:** quality is uneven. Version claims inside some agents lag; the README lists `dotnet-core-expert` as
  ".NET 8" and `angular-architect` as "Angular 15+". Use these as structure templates, not version sources.
- **Claude Code:**
  - Install: `claude plugin marketplace add VoltAgent/awesome-claude-code-subagents`, then
    `claude plugin install voltagent-lang`.
  - Manual: copy the files to `~/.claude/agents/`.
- **OpenCode:** convert per §0 into `~/.config/opencode/agents/`.

### 10. EveryInc/compound-engineering-plugin: review personas plus learning capture
- **Verified:** MIT · 25,762★ · pushed 2026-10-29 · `plugin.json` version 3.33.2.
- **What it is:** 36 skills (`skills/ce-*`) around brainstorm → plan → work → simplify → review → **compound**.
  The compound step writes what was learned so the next change is easier.
- **Worth taking:**
  - **`skills/ce-code-review/references/`** is the best reviewer-seat source found:
    - `personas/` (correctness, security, performance, reliability, testing, maintainability, api-contract,
      data-migration, adversarial, project-standards, previous-comments)
    - `persona-catalog.md`, `select-and-route.md`, `dispatch-reviewers.md`
    - a `findings-schema.json`, a `validator-batch-template.md`, `cross-model-review.md`
  - `ce-compound`, which is the learning loop.
- **Languages:** All. One Swift persona exists; there are no pack-language-specific personas.
- **Claude Code:**
  - Install: `/plugin marketplace add EveryInc/compound-engineering-plugin`, then `/plugin install compound-engineering`.
  - Manual: copy `skills/ce-*` to `~/.claude/skills/`.
- **OpenCode:** add `"compound-engineering@git+https://github.com/EveryInc/compound-engineering-plugin.git"` to the
  `plugin` array in `opencode.json` (README).

### 11. Yeachan-Heo/oh-my-claudecode: staged team pipeline
- **Verified:** MIT · 40,382★ · pushed 2026-10-29.
- **What it is:** a Claude Code plugin plus an `omc` CLI. Since v4.1.7, "Team" is the canonical surface:
  `team-plan → team-prd → team-exec → team-verify → team-fix (loop)`. It uses native agent teams when
  `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set.
- **Worth taking:** the `agents/` roles `planner`, `architect`, `critic`, `executor`, `verifier`, `tracer`,
  `debugger`, `security-reviewer`, `test-engineer`, `code-simplifier` and `explore`. The verify→fix loop as a
  first-class stage.
- **Languages:** All.
- **Claude Code:**
  - Install: `/plugin install oh-my-claudecode` (README), or the npm runtime `oh-my-claude-sisyphus`.
  - Manual: copy `agents/*.md` to `~/.claude/agents/`.
- **OpenCode:** none native. Convert agents per §0.

### 12. github/spec-kit: spec-driven development
- **Verified:** MIT · 143,778★ · pushed 2026-10-28.
- **Worth taking:** the constitution → specify → plan → tasks → implement artifacts, extensions and "bundles" for
  roles or teams. The pack's agents can treat a spec-kit `tasks` file as their input contract.
- **Languages:** All.
- **Install (README):** `uv tool install specify-cli`, then `specify init <project> --integration <agent>`. It writes
  agent-specific command or skill files into the project. Integration keys exist for Claude Code and other agents;
  for OpenCode, see the integrations page linked from the README. The **OpenCode key is [UNVERIFIED]** this session.

### 13. Fission-AI/OpenSpec: lightweight change proposals
- **Verified:** MIT · 73,307★ · pushed 2026-10-28.
- **Worth taking:** change folders with ADDED/MODIFIED requirements, and the `/opsx:explore`, `/opsx:propose`,
  `/opsx:apply` and `/opsx:archive` commands. This is lighter than spec-kit for brownfield work.
- **Languages:** All.
- **Install (README):** single-binary installer or `npm install -g @fission-ai/openspec@latest`, then
  `openspec init`, which writes the commands for the tools you pick. README docs list supported tools at
  openspec.dev. **OpenCode support [UNVERIFIED]**.

### 14. dotnet/skills: official .NET skills (C#)
- **Verified:** MIT · 5,762★ · pushed 2026-10-29.
- **What it is:** 17 plugins: `dotnet`, `dotnet-advanced`, `dotnet-ai`, `dotnet-aspnetcore`, `dotnet-blazor`,
  `dotnet-data`, `dotnet-diag`, `dotnet-experimental`, `dotnet-maui`, `dotnet-msbuild`, `dotnet-nuget`,
  `dotnet-template-engine`, `dotnet-test`, `dotnet-test-migration`, `dotnet-upgrade`, `dotnet-winforms` and
  `dotnet11`. The `dotnet` plugin carries C# LSP config (`lsp.json`). There is a public "Skill Value" dashboard
  (token use, activation and pass rates).
- **Languages:** cs (primary source for the csharp agent).
- **Claude Code:**
  - Install: `/plugin marketplace add dotnet/skills`, then `/plugin install <plugin>@dotnet-agent-skills`.
  - Manual: copy `plugins/<p>/skills/*` to `~/.claude/skills/`.
- **OpenCode:** copy the skills to `~/.config/opencode/skills/`. `agents/*.agent.md` files use **Copilot**
  custom-agent conventions (README), so convert them before use.

### 15. samber/cc-skills-golang: deep Go skills
- **Verified:** MIT · 3,719★ · pushed 2026-10-23.
- **What it is:** 46 `skills/golang-*`, including `golang-concurrency`, `golang-context`, `golang-error-handling`,
  `golang-safety`, `golang-security`, `golang-performance`, `golang-benchmark`, `golang-testing`, `golang-lint`,
  `golang-modernize`, `golang-gopls` and `golang-observability`. Also `EVALUATIONS.md` and
  `GOLANG-AI-DRIVEN-REVIEW.md`. The README says the skills were "edited, tested, reviewed and reworked by a human".
- **Languages:** go.
- **Claude Code:**
  - Install: plugin manifest `.claude-plugin/` exists, or `npx skills add https://github.com/samber/cc-skills-golang --all`.
  - Manual: copy `skills/golang-*` to `~/.claude/skills/`.
- **OpenCode:** the same `npx skills … -a opencode` route, or copy to `~/.config/opencode/skills/`.

### 16. Kotlin/kotlin-agent-skills: official Kotlin skills (JetBrains incubator)
- **Verified:** Apache-2.0 · 1,100★ · pushed 2026-10-28. Linked from
  [kotlinlang.org/docs/kotlin-ai-skills.html](https://kotlinlang.org/docs/kotlin-ai-skills.html).
- **What it is:** 10 skills: `kotlin-tooling-java-to-kotlin`, `kotlin-backend-jpa-entity-mapping`,
  `kotlin-tooling-agp9-migration`, `kotlin-tooling-kotlin-toolchain`, `kotlin-tooling-native-build-performance`,
  Gradle toolchain skills, and others.
- **Languages:** kt (and java, through Java→Kotlin).
- **Claude Code:** `claude plugin marketplace add Kotlin/kotlin-agent-skills`, then
  `claude plugin install kotlin-agent-skills@Kotlin`. Or `cp -r skills/<name> ~/.claude/skills/`.
- **OpenCode:** `npx skills add Kotlin/kotlin-agent-skills`, or copy to `~/.config/opencode/skills/`.

### 17. vercel-labs/agent-skills: React and web rules from Vercel
- **Verified:** no repo-level license (API `null`) · 33,186★ · pushed 2026-10-28.
- **What it is:** `react-best-practices` (`SKILL.md` + `rules/` + `AGENTS.md`), `composition-patterns`,
  `react-view-transitions`, `react-native-skills`, `web-design-guidelines`, `writing-guidelines`, `vercel-optimize`
  and `deploy-to-vercel`.
- **Languages:** ts, js, web.
- **Install:**
  - Claude Code: `npx skills add vercel-labs/agent-skills` (choose claude-code), or copy `skills/<name>` to
    `~/.claude/skills/`.
  - OpenCode: the same CLI with opencode as the target.
- **License action:** no license, so link and paraphrase only.

### 18. getsentry/skills: Sentry's internal engineering skills
- **Verified:** Apache-2.0 · 1,098★ · pushed 2026-10-26.
- **Worth taking:**
  - Skills: `code-review`, `find-bugs`, `security-review`, `gha-security-review` (GitHub Actions),
    `iterate-pr`, `skill-scanner` (scans skills for risk), `skill-writer`, `agents-md` and `claude-settings-audit`.
  - Agents: `code-simplifier.md` and `senpai.md`.
  - Python/Django-specific: `django-perf-review` and `django-access-review`.
- **Languages:** All; py (Django).
- **Claude Code:** `claude plugin marketplace add getsentry/skills`, then
  `claude plugin install sentry-skills@sentry-skills`. Or copy `skills/*` to `~/.claude/skills/` and `agents/*` to
  `~/.claude/agents/`.
- **OpenCode:** copy skills; convert agents per §0.

### 19. microsoft/skills: Azure SDK skills per language
- **Verified:** MIT · 3,155★ · pushed 2026-10-28.
- **What it is:** about 175 skills (README) grouped into `### Python`, `### .NET`, `### TypeScript`, `### Java`
  and `### Rust` sections under `.github/plugins/*/skills/`, plus role agents (backend, frontend, infrastructure,
  planner) and an `AGENTS.md` template.
- **Languages:** py, cs, ts, java, rs. This only matters when the app targets Azure.
- **Install:** `npx skills add microsoft/skills` (wizard). For OpenCode, the README shows
  `ln -s ../.github/skills .opencode/skills`.

### 20. leonardomso/rust-skills: rule-indexed Rust skill
- **Verified:** MIT · 654★ · pushed 2026-06-14 (4.5 months ago; flagged as slower-moving).
- **What it is:** one skill whose `SKILL.md` is an index of `rules/<prefix>-<name>.md` files. The API description
  says "265 rules across 26 categories". Each rule gives why, bad code, good code and doc links.
- **Worth taking:** the **index-plus-rule-files** layout. It keeps the always-loaded part tiny, and the pack's
  `skills/<slug>-engineering/references/` can mirror it.
- **Languages:** rs.
- **Claude Code:** `git clone https://github.com/leonardomso/rust-skills.git ~/.claude/skills/rust-skills` (README).
- **OpenCode:** the same clone into `~/.config/opencode/skills/rust-skills`.

### 21. Jeffallan/claude-skills: 67 full-stack skills
- **Verified:** MIT · 12,124★ · pushed 2026-10-29.
- **Worth taking:**
  - Per-language skills: `python-pro`, `cpp-pro`, `csharp-developer`, `dotnet-core-expert`, `rust-engineer`,
    `javascript-pro`, `typescript-pro`, `golang-pro`, `java-architect`, `spring-boot-engineer`, `kotlin-specialist`.
  - Process: `test-master`, `debugging-wizard`, `secure-code-guardian`, `security-reviewer`, `spec-miner`,
    `the-fool` (devil's advocate).
  - Each skill has `references/`.
- **Languages:** all 10 (web via `vue-expert`, `react-expert`, `nextjs-developer`).
- **Claude Code:** `/plugin marketplace add jeffallan/claude-skills`, then
  `/plugin install fullstack-dev-skills@fullstack-dev-skills`. Or copy `skills/<name>` to `~/.claude/skills/`.
- **OpenCode:** copy to `~/.config/opencode/skills/`.

### 22. bmad-code-org/BMAD-METHOD: role-based agile workflow
- **Verified:** MIT (API `NOASSERTION`; the LICENSE file reads MIT, with "BMad" trademarks in `TRADEMARK.md`) ·
  54,721★ · pushed 2026-10-27.
- **Worth taking:** explicit role hand-offs, where decisions are kept as documents rather than chat. Stable line
  v6.12; v7 is in alpha (README).
- **Languages:** All.
- **Install (README):**
  - `npx bmad-method install`, or `npx skills add bmad-code-org/BMAD-METHOD --skill '*'` (choose Claude Code or
    OpenCode).
  - Claude Code plugin: `/plugin marketplace add bmad-code-org/bmad-plugins`.

### 23. OthmanAdi/planning-with-files: crash-proof planning memory
- **Verified:** MIT · 27,747★ · pushed 2026-10-28.
- **Worth taking:** the 3-file pattern (`task_plan.md`, `findings.md`, `progress.md`). Long agent runs survive
  `/clear` and compaction.
- **Languages:** All.
- **Install:** `npx skills add OthmanAdi/planning-with-files --skill planning-with-files -g`. It installs to
  `~/.claude/skills/` or `~/.config/opencode/skills/` depending on the agent chosen.

### 24. gastownhall/beads: dependency-graph issue memory
- **Verified:** MIT · 28,281★ · pushed 2026-10-29. Repo moved from `steveyegge/beads`.
- **Worth taking:** a dependency-aware task graph (`bd`, Dolt-backed) instead of markdown TODOs, for long-horizon
  multi-agent work. `bd setup claude` installs hooks and settings.
- **Languages:** All.
- **Install:** a `curl … | bash` installer (README). **Review it before running.** This box's policy denies `curl|sh`.

### 25. muratcankoylan/Agent-Skills-for-Context-Engineering
- **Verified:** MIT · 18,237★ · pushed 2026-10-12.
- **Worth taking:** `multi-agent-patterns` (orchestrator, peer-to-peer, hierarchical), `context-degradation`
  (lost-in-middle, poisoning, distraction, clash), `long-horizon-prompting` (success predicates for long runs),
  `filesystem-context` and `tool-design`. Good inputs for the pack's Delegation sections.
- **Languages:** All.
- **Install:** copy `skills/<name>/` to `~/.claude/skills/` or `~/.config/opencode/skills/`.

### 26. alvinunreal/oh-my-opencode-slim: OpenCode-native multi-agent suite
- **Verified:** MIT · 9,844★ · pushed 2026-10-29.
- **Worth taking:** a named role split for OpenCode:
  - **Orchestrator**, which plans the work graph and delegates.
  - **Explorer** and **Librarian**, for code and docs research.
  - **Oracle**, which reviews between phases.
  - **Designer**, for UI.
  - **Fixer**, the implementer.
  Per-role model and skill assignment lives in `~/.config/opencode/oh-my-opencode-slim.json`.
- **Languages:** All.
- **Install (README):** `bunx oh-my-opencode-slim@latest install` (or `npx`). It edits the OpenCode `plugin` array.
- **Note:** the parent project [code-yeongyu/oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) (was
  oh-my-opencode, 70,458★) now ships its own `omo` harness under the **Sustainable Use License**, so it is excluded.
  See §5.

### 27. humanlayer/humanlayer: Research-Plan-Implement
- **Verified:** Apache-2.0 · 12,694★ · pushed 2026-10-29.
- **Worth taking:** `apps/riptide-rpi-claude-plugin` (README) holds Research-Plan-Implement skills. Research with
  subagents, write a plan, then implement against it with a human reviewing the plan rather than the diff. The repo
  also has Claude Code and OpenCode session-mirroring plugins.
- **Languages:** All.
- **Install:** self-host or app (README). The RPI skills can be copied as files.

### 28. open-gsd/gsd-core: successor to Get Shit Done
- **Verified:** MIT · 10,988★ · pushed 2026-10-29. The original
  [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) (64,188★) is **archived** (pushed 2026-05-31),
  and its README says "GSD Has Moved" to `open-gsd/gsd-core`.
- **Worth taking:** phase plans executed by fresh-context subagents, so the orchestrator never fills its own context.
- **Languages:** All. **Install path [UNVERIFIED]**: the new repo's README was not read this session.

### 29. snarktank/ralph: the loop pattern
- **Verified:** MIT · 22,083★ · pushed 2026-02-02 (9 months ago).
- **Worth taking:** iterate an agent over PRD items until all pass, with fresh context each iteration. For Claude
  Code, prefer Anthropic's maintained `ralph-loop` plugin in claude-plugins-official.
- **Languages:** All.

### 30. davila7/claude-code-templates: component picker
- **Verified:** MIT · 32,964★ · pushed 2026-10-29.
- **Worth taking:** a browsable catalog of agents, commands, hooks and settings. The quoted install form is
  `npx claude-code-templates@latest --agent <category>/<name> --yes`, which writes into `.claude/`.
- **Languages:** mixed. **Caveat:** these are aggregated components of uneven quality, so read each one.

### 31. SuperClaude-Org/SuperClaude_Framework
- **Verified:** MIT · 23,916★ · pushed 2026-09-27.
- **Worth taking:** persona or mode switching and its command set. `pipx install superclaude`, then
  `superclaude install`, writes 30 slash commands. The README says the plugin system is "planned for v5.0".
- **Languages:** All.

### 32. ruvnet/ruflo (formerly claude-flow)
- **Verified:** MIT · 80,044★ · pushed 2026-10-29.
- **Worth taking:** concepts only (swarm router → agents → shared memory). It is a large runtime with an MCP server
  (`npx ruflo@latest mcp start`), so the MCP part belongs to C1.
- **Install:** `/plugin marketplace add ruvnet/ruflo`, then `/plugin install ruflo-core@ruflo`.
- **Caveat:** heavy and opinionated. Not recommended as a dependency for the language pack.

### 33. trailofbits/claude-code-config
- **Verified:** no license · 2,143★ · pushed 2026-08-24.
- **Worth taking (paraphrase):** sandboxing, permissions and hook defaults, and usage patterns from a security firm.
  This is a good checklist for the pack's `permissionMode` and hooks choices. Setup runs `/trailofbits:config` from
  a clone.

### 34. trailofbits/skills-curated
- **Verified:** CC-BY-SA-4.0 · 522★ · pushed 2026-07-14.
- **Worth taking:** use it as a **trust allowlist**. Every listed plugin was "code-reviewed by Trail of Bits staff".
  `/plugin marketplace add trailofbits/skills-curated`.

### 35. multica-ai/andrej-karpathy-skills
- **Verified:** no license · 226,164★ · pushed 2026-04-20. Repo moved from `forrestchang/andrej-karpathy-skills`.
- **Worth taking (paraphrase only):** one CLAUDE.md with 4 principles answering Karpathy's complaints about wrong
  silent assumptions, overcomplicated code, and side-effect edits. These are useful framing for the pack's
  Anti-patterns sections.

### 36. vercel-labs/skills: the `npx skills` installer
- **Verified:** MIT · 37,084★ · pushed 2026-10-29.
- **Worth taking:** the de facto cross-agent skill installer. It needs Node ≥ 22.20 (README). It also offers
  `skills use <repo>@<skill>`, which prints a one-off prompt without installing. Target paths are verified in §0.

### 37. VoltAgent/awesome-agent-skills
- **Verified:** MIT · 36,542★ · pushed 2026-10-29.
- **Worth taking:** discovery of **vendor-official** skills. The README says it focuses on skills "created and used
  by actual engineering teams, not mass AI-generated stuff".

### 38. github/awesome-copilot
- **Verified:** MIT · 40,541★ · pushed 2026-10-29.
- **Worth taking:** per-language Copilot instructions and agents. Its `llms.txt` is a machine-readable index. Formats
  are Copilot's (`*.agent.md`, `*.instructions.md`), so convert them before use in Claude Code or OpenCode.

### 39. hesreallyhim/awesome-claude-code
- **Verified:** license file is **CC BY-NC-ND 4.0** (API reports `NOASSERTION`) · 56,798★ · pushed 2026-10-29.
- **Worth taking:** discovery only. NoDerivatives means nothing may be adapted; link to it.

---

## 3. Per-language quick map (what each language agent should pull from)

| Lang | Best skill sources | Best agent templates | Code intelligence |
|---|---|---|---|
| python | trailofbits `modern-python` (CC-BY-SA, link), wshobson `python-development` 16 skills, getsentry django reviews | wshobson `python-pro`, ECC `python-reviewer`, VoltAgent `python-pro` | official `pyright-lsp` |
| cpp | trailofbits `modern-cpp`, `c-review`, `zeroize-audit` (link) | wshobson `cpp-pro`, ECC `cpp-reviewer` + `cpp-build-resolver` | official `clangd-lsp` |
| csharp | **dotnet/skills** (official, 17 plugins) | wshobson `csharp-pro`, `dotnet-architect`; ECC `csharp-reviewer` | official `csharp-lsp`; dotnet `lsp.json` |
| rust | leonardomso/rust-skills, trailofbits `rust-review` (link) | wshobson `rust-pro`, ECC `rust-reviewer` + `rust-build-resolver`, VoltAgent `rust-engineer` | official `rust-analyzer-lsp` |
| javascript | vercel `react-best-practices` (link), anthropics `webapp-testing` | wshobson `javascript-pro`, VoltAgent `javascript-pro`/`node-specialist` | official `typescript-lsp` |
| typescript | vercel skills (link), addyosmani `frontend-ui-engineering` | wshobson `typescript-pro`, ECC `typescript-reviewer` | official `typescript-lsp` |
| go | **samber/cc-skills-golang** (46 skills) | wshobson `golang-pro`, ECC `go-reviewer` + `go-build-resolver` | official `gopls-lsp`; samber `golang-gopls` |
| java | microsoft/skills Java (Azure only), Jeffallan `spring-boot-engineer` | wshobson `java-pro`, ECC `java-reviewer` + `java-build-resolver`, VoltAgent `java-architect` | official `jdtls-lsp` |
| kotlin | **Kotlin/kotlin-agent-skills** (official) | ECC `kotlin-reviewer` + `kotlin-build-resolver`, VoltAgent `kotlin-specialist` | official `kotlin-lsp` |
| web | vercel `web-design-guidelines` (link), anthropics `webapp-testing`, addyosmani `/webperf` | addyosmani `web-performance-auditor`, VoltAgent `frontend-developer`/`accessibility-tester` | `typescript-lsp` for scripts |

Process skills that every language agent should reference: superpowers TDD, debugging and verification;
mattpocock `tdd`, `diagnosing-bugs` and `code-review`; addyosmani anti-rationalization; the official `code-review`
confidence gate; and trailofbits `differential-review` and `fp-check` for the security seat.

---

## 4. Agent-team design patterns worth copying

Each pattern below gives what to copy, why, and where it was seen. "Seen in" means the file or README was read this
session.

### 4.1 Orchestrator / router seat
- **Orchestrator-workers.** A lead decomposes the task at runtime, delegates to workers and synthesizes. Subtasks
  are not predefined, which separates this pattern from fixed parallelization.
  Source: [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
  (routing, parallelization with sectioning or voting, orchestrator-workers, evaluator-optimizer).
- **Teach the orchestrator to delegate.** Each worker brief needs an objective, an output format, tool guidance and
  task boundaries. Scale effort to complexity. Early systems spawned "50 subagents for simple queries".
  Multi-agent runs used about 15× the tokens of chat, and token usage alone explained 80% of the variance on
  BrowseComp.
  Source: [Anthropic, How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system).
  **Implication for the pack:** the prefix router that picks about 10 of about 40 agents should send *disjoint*
  briefs. Parallelize only independent work, because that post notes most coding tasks have fewer parallel parts
  than research.
- **"Personas do not invoke personas"; the user or a slash command orchestrates.** Endorsed patterns are direct
  invocation, a single-persona command, parallel fan-out with merge (`/ship` → reviewer + security + test → go/no-go),
  a user-driven sequential pipeline, and research isolation via the built-in `Explore` subagent.
  Source: [addyosmani/agent-skills `references/orchestration-patterns.md`](https://github.com/addyosmani/agent-skills/blob/main/references/orchestration-patterns.md) (MIT).
- **Staged team pipeline with a fix loop:** `plan → prd → exec → verify → fix (loop)`.
  Source: [oh-my-claudecode README, Team Mode](https://github.com/Yeachan-Heo/oh-my-claudecode).
- **Task-graph frontier scheduling.** Implementers run on every ticket whose blockers are done, and the run closes
  with a review. Source: [mattpocock `implement-spec`](https://github.com/mattpocock/skills).
- **OpenCode routing control.** `permission.task` globs decide which subagents an orchestrator may call, and the
  last matching rule wins. Source: [OpenCode agents docs, "Task permissions"](https://opencode.ai/docs/agents/).
  Claude Code's equivalent is the depth limit (3 by default) and the `Agent` tool in a subagent's `tools`.
  Source: [Claude Code sub-agents](https://code.claude.com/docs/en/sub-agents).
- **Lead plus teammates with a shared task list**, when workers must talk to each other.
  Source: [Claude Code agent teams](https://code.claude.com/docs/en/agent-teams). Prefer subagents when results only
  need to flow back to the caller; teams cost more tokens.

### 4.2 Implementer seat
- **File-ownership boundaries for parallel implementers**, so no two workers edit one file.
  Source: [wshobson `agent-teams`](https://github.com/wshobson/agents/tree/main/plugins/agent-teams)
  (`team-implementer`, `/team-feature`).
- **Implementer prompt → spec-compliance review → code-quality review → re-review.**
  Source: [superpowers `subagent-driven-development`](https://github.com/obra/superpowers/tree/main/skills/subagent-driven-development)
  (`implementer-prompt.md`, `task-reviewer-prompt.md`, `re-review-prompt.md`).
- **Fresh-context executors per phase**, so the orchestrator keeps its context small.
  Source: open-gsd/gsd-core (successor of GSD). Detail **[UNVERIFIED]**, README not read.

### 4.3 Reviewer seat
- **Parallel independent reviewers plus a confidence threshold.** 4 agents each score issues 0–100 and anything
  below 80 is dropped. Pre-existing issues and nitpicks are filtered out.
  Source: [claude-plugins-official `code-review`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-review) (Apache-2.0).
- **Single-dimension reviewers:** silent-failure hunter, type-design, test coverage, comments, simplifier.
  Source: [claude-plugins-official `pr-review-toolkit`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/pr-review-toolkit).
- **Persona catalog plus routing plus a findings JSON schema plus a validator batch.**
  Source: [compound-engineering `skills/ce-code-review/references/`](https://github.com/EveryInc/compound-engineering-plugin/tree/main/skills/ce-code-review) (MIT).
- **Two axes kept apart** (Standards vs Spec), run as separate subagents "so neither pollutes the other".
  Source: [mattpocock `code-review`](https://github.com/mattpocock/skills).
- **A per-language reviewer paired with a per-language build-error resolver.**
  Source: [ECC `agents/`](https://github.com/affaan-m/ECC/tree/main/agents) (`*-reviewer`, `*-build-resolver`).
- **Adversarial fresh-context doubt pass** (CLAIM → EXTRACT → DOUBT → RECONCILE → STOP).
  Source: addyosmani `doubt-driven-development`.

### 4.4 Security seat
- **Refute before reporting.** Run a verifier per candidate finding and a false-positive gate.
  Source: [trailofbits/skills](https://github.com/trailofbits/skills) `insecure-defaults` ("a refuting verifier per
  candidate file") and `fp-check` (CC-BY-SA, paraphrased here).
- **Differential review:** a security review of the diff plus its git history.
  Source: trailofbits `differential-review`; the official `code-review` blame-history agent is the same idea.
- **Language-specific security reviewers** (C/C++ with parse-verified coverage; Rust unsafe, FFI and async with
  SARIF output). Source: trailofbits `c-review`, `rust-review`.
- **Supply-chain seat:** npm/PyPI/Go advisories, abandoned upstreams, install scripts.
  Source: trailofbits `supply-chain-risk-auditor`.
- **Treat skills and plugins themselves as untrusted.** Use a vetted marketplace and a skill scanner.
  Sources: [trailofbits/skills-curated](https://github.com/trailofbits/skills-curated) and getsentry `skill-scanner`.
- **CI security review action.** [anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review)
  (MIT, 6,637★, last pushed 2026-02-11) runs a PR security review as a GitHub Action. It is excluded as a catalog
  entry because it is CI, not a skill or agent.

### 4.5 Research seat
- **Research isolation.** A subagent reads a lot and returns a digest. On Claude Code, use the built-in `Explore`
  subagent; per addyosmani, it is read-only and runs on Haiku. Sources: addyosmani `orchestration-patterns.md`
  (pattern 5) and Claude Code sub-agents docs (a user or project `Explore` overrides the built-in).
- **Parallel explorers on different angles before design.** 2–3 `code-explorer` agents look at similar features,
  architecture and the current implementation, then a `code-architect` designs.
  Source: [claude-plugins-official `feature-dev`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/feature-dev).
- **Lead researcher plus parallel subagents plus a CitationAgent**, with the plan saved to memory before context
  limits. Source: Anthropic multi-agent research post.
- **Cited research written to the repo** as a Markdown file. Source: mattpocock `research`.

### 4.6 Debugger and test seats
- **Competing-hypothesis debugging.** One teammate per hypothesis gathers evidence to confirm or falsify it.
  Sources: wshobson `team-debugger` / `/team-debug`; Claude Code agent-teams docs list it among the strongest use
  cases.
- **Red-first diagnosis loop:** reproduce until red → minimise → hypothesise → instrument → fix → regression test.
  Sources: mattpocock `diagnosing-bugs`; superpowers `systematic-debugging`.
- **Test engineer persona using the "Prove-It" pattern.** Source: addyosmani `agents/test-engineer.md`.

### 4.7 Memory and long-run seats
- **File-based plan, findings and progress**, re-read after compaction. Source: planning-with-files.
- **Dependency graph of tasks** instead of TODO markdown. Source: beads.
- **Compound step:** write what each change taught you. Source: compound-engineering `ce-compound`.

---

## 5. Considered and excluded (with the reason)

| Repo | Fields (verified) | Why excluded |
|---|---|---|
| code-yeongyu/oh-my-openagent (was oh-my-opencode) | 70,458★ · 2026-10-29 · NOASSERTION (LICENSE.md = Sustainable Use License) | Now its own `omo` harness, not an OpenCode skill/agent pack. Source-available license. oh-my-opencode-slim (#26) covers the OpenCode role pattern |
| gsd-build/get-shit-done | 64,188★ · 2026-05-31 · MIT · **archived** | Moved to open-gsd/gsd-core (#28) |
| openai/skills | 28,383★ · 2026-10-28 · null | README: "This repository is deprecated", replaced by openai/plugins. Codex-oriented |
| ComposioHQ/awesome-claude-skills | 78,235★ · 2026-09-18 · null | Mostly SaaS-integration skills; no license |
| travisvn/awesome-claude-skills | 15,617★ · 2026-04-28 · null | List only; covered by VoltAgent/awesome-agent-skills |
| sickn33/agentic-awesome-skills (was antigravity-awesome-skills) | 48,700★ · 2026-10-29 · MIT | Bulk aggregation; no curation evidence found |
| alirezarezvani/claude-skills | 28,941★ · 2026-10-29 · MIT | Broad (marketing, C-level, compliance); engineering subset overlaps #6/#21 |
| contains-studio/agents | 12,419★ · 2025-07-28 · null | Stale (15 months) and unlicensed |
| iannuttall/claude-agents | 2,039★ · 2025-07-25 · MIT · **archived** | Archived |
| 0xfurai/claude-code-subagents | 1,020★ · 2025-10-15 · MIT | Stale (12 months); superseded by #6/#9 |
| lst97/claude-code-sub-agents | 1,703★ · 2025-08-15 · MIT | Stale |
| vijaythecoder/awesome-claude-agents | 4,402★ · 2025-10-30 · MIT | Stale |
| JetBrains/skills | 385★ · 2026-10-21 · null | Mirror of upstream skills (keeps `metadata.source`). Use the upstreams, e.g. #16 |
| actionbook/rust-skills | 1,553★ · 2026-08-23 · null | No license; #20 is MIT |
| rohitg00/awesome-claude-code-toolkit | 2,786★ · 2026-05-12 · Apache-2.0 | Aggregator; low signal |
| NeoLabHQ/context-engineering-kit | 1,792★ · 2026-08-26 · GPL-3.0 | GPL is incompatible with adapting into an MIT pack; #25 covers the topic under MIT |
| disler/claude-code-hooks-mastery | 3,968★ · 2026-03-04 · null | Hooks tutorial; unlicensed |
| coleam00/context-engineering-intro | 13,896★ · 2026-03-16 · MIT | Intro template; superseded by spec-kit/OpenSpec |
| buildermethods/agent-os | 5,561★ · 2026-10-07 · MIT | Overlaps spec-kit/OpenSpec; lower adoption |
| kdcokenny/opencode-background-agents | 384★ · 2026-09-16 · MIT · **archived** | Archived |
| anthropics/claude-code-security-review | 6,637★ · 2026-02-11 · MIT | CI action, not a skill or agent (cited in §4.4) |

---

## 6. Verification log (raw `ghapi.sh repos/<owner>/<repo>` fields, 2026-10-29)

Command: `ghapi.sh repos/<owner>/<repo>`, projected to the fields below with `python3 -I`. Renamed repos were
followed through the API's `Moved Permanently` → `repositories/<id>` URL.

Included (40 lines: 39 entries plus anomalyco/opencode as reference):
```json
{"full_name":"obra/superpowers","stargazers_count":307818,"pushed_at":"2026-10-23T03:48:57Z","license":"MIT","archived":false}
{"full_name":"anthropics/claude-plugins-official","stargazers_count":45193,"pushed_at":"2026-10-29T07:31:04Z","license":"Apache-2.0","archived":false}
{"full_name":"anthropics/skills","stargazers_count":184622,"pushed_at":"2026-10-28T19:20:39Z","license":null,"archived":false}
{"full_name":"mattpocock/skills","stargazers_count":306088,"pushed_at":"2026-10-27T07:44:25Z","license":"MIT","archived":false}
{"full_name":"addyosmani/agent-skills","stargazers_count":111565,"pushed_at":"2026-10-29T05:06:58Z","license":"MIT","archived":false}
{"full_name":"wshobson/agents","stargazers_count":41968,"pushed_at":"2026-10-26T01:08:14Z","license":"MIT","archived":false}
{"full_name":"trailofbits/skills","stargazers_count":7872,"pushed_at":"2026-10-28T19:41:17Z","license":"CC-BY-SA-4.0","archived":false}
{"full_name":"affaan-m/ECC","stargazers_count":292109,"pushed_at":"2026-10-26T04:56:56Z","license":"MIT","archived":false}
{"full_name":"VoltAgent/awesome-claude-code-subagents","stargazers_count":26164,"pushed_at":"2026-10-11T08:20:37Z","license":"MIT","archived":false}
{"full_name":"EveryInc/compound-engineering-plugin","stargazers_count":25762,"pushed_at":"2026-10-29T02:33:16Z","license":"MIT","archived":false}
{"full_name":"Yeachan-Heo/oh-my-claudecode","stargazers_count":40382,"pushed_at":"2026-10-29T07:41:36Z","license":"MIT","archived":false}
{"full_name":"github/spec-kit","stargazers_count":143778,"pushed_at":"2026-10-28T20:37:09Z","license":"MIT","archived":false}
{"full_name":"Fission-AI/OpenSpec","stargazers_count":73307,"pushed_at":"2026-10-28T20:03:36Z","license":"MIT","archived":false}
{"full_name":"bmad-code-org/BMAD-METHOD","stargazers_count":54721,"pushed_at":"2026-10-27T18:57:00Z","license":"NOASSERTION","archived":false}
{"full_name":"dotnet/skills","stargazers_count":5762,"pushed_at":"2026-10-29T08:56:30Z","license":"MIT","archived":false}
{"full_name":"Kotlin/kotlin-agent-skills","stargazers_count":1100,"pushed_at":"2026-10-28T16:08:31Z","license":"Apache-2.0","archived":false}
{"full_name":"samber/cc-skills-golang","stargazers_count":3719,"pushed_at":"2026-10-23T07:50:53Z","license":"MIT","archived":false}
{"full_name":"leonardomso/rust-skills","stargazers_count":654,"pushed_at":"2026-06-14T22:51:13Z","license":"MIT","archived":false}
{"full_name":"vercel-labs/agent-skills","stargazers_count":33186,"pushed_at":"2026-10-28T19:17:28Z","license":null,"archived":false}
{"full_name":"Jeffallan/claude-skills","stargazers_count":12124,"pushed_at":"2026-10-29T01:36:45Z","license":"MIT","archived":false}
{"full_name":"microsoft/skills","stargazers_count":3155,"pushed_at":"2026-10-28T16:37:16Z","license":"MIT","archived":false}
{"full_name":"getsentry/skills","stargazers_count":1098,"pushed_at":"2026-10-26T12:26:36Z","license":"Apache-2.0","archived":false}
{"full_name":"OthmanAdi/planning-with-files","stargazers_count":27747,"pushed_at":"2026-10-28T17:42:45Z","license":"MIT","archived":false}
{"full_name":"gastownhall/beads","stargazers_count":28281,"pushed_at":"2026-10-29T04:51:03Z","license":"MIT","archived":false}
{"full_name":"muratcankoylan/Agent-Skills-for-Context-Engineering","stargazers_count":18237,"pushed_at":"2026-10-12T02:06:40Z","license":"MIT","archived":false}
{"full_name":"humanlayer/humanlayer","stargazers_count":12694,"pushed_at":"2026-10-29T03:05:46Z","license":"Apache-2.0","archived":false}
{"full_name":"alvinunreal/oh-my-opencode-slim","stargazers_count":9844,"pushed_at":"2026-10-29T09:28:20Z","license":"MIT","archived":false}
{"full_name":"ruvnet/ruflo","stargazers_count":80044,"pushed_at":"2026-10-29T06:31:16Z","license":"MIT","archived":false}
{"full_name":"davila7/claude-code-templates","stargazers_count":32964,"pushed_at":"2026-10-29T03:12:46Z","license":"MIT","archived":false}
{"full_name":"SuperClaude-Org/SuperClaude_Framework","stargazers_count":23916,"pushed_at":"2026-09-27T12:50:32Z","license":"MIT","archived":false}
{"full_name":"multica-ai/andrej-karpathy-skills","stargazers_count":226164,"pushed_at":"2026-04-20T10:05:04Z","license":null,"archived":false}
{"full_name":"trailofbits/claude-code-config","stargazers_count":2143,"pushed_at":"2026-08-24T19:47:25Z","license":null,"archived":false}
{"full_name":"trailofbits/skills-curated","stargazers_count":522,"pushed_at":"2026-07-14T17:53:18Z","license":"CC-BY-SA-4.0","archived":false}
{"full_name":"vercel-labs/skills","stargazers_count":37084,"pushed_at":"2026-10-29T00:49:36Z","license":"MIT","archived":false}
{"full_name":"VoltAgent/awesome-agent-skills","stargazers_count":36542,"pushed_at":"2026-10-29T09:33:34Z","license":"MIT","archived":false}
{"full_name":"hesreallyhim/awesome-claude-code","stargazers_count":56798,"pushed_at":"2026-10-29T09:08:35Z","license":"NOASSERTION","archived":false}
{"full_name":"github/awesome-copilot","stargazers_count":40541,"pushed_at":"2026-10-29T00:07:04Z","license":"MIT","archived":false}
{"full_name":"snarktank/ralph","stargazers_count":22083,"pushed_at":"2026-02-02T01:46:21Z","license":"MIT","archived":false}
{"full_name":"open-gsd/gsd-core","stargazers_count":10988,"pushed_at":"2026-10-29T07:25:44Z","license":"MIT","archived":false}
{"full_name":"anomalyco/opencode","stargazers_count":222892,"pushed_at":"2026-10-29T08:58:28Z","license":"MIT","archived":false}
```

Excluded (21):
```json
{"full_name":"code-yeongyu/oh-my-openagent","stargazers_count":70458,"pushed_at":"2026-10-29T09:31:33Z","license":"NOASSERTION","archived":false}
{"full_name":"gsd-build/get-shit-done","stargazers_count":64188,"pushed_at":"2026-05-31T17:46:54Z","license":"MIT","archived":true}
{"full_name":"openai/skills","stargazers_count":28383,"pushed_at":"2026-10-28T17:31:41Z","license":null,"archived":false}
{"full_name":"iannuttall/claude-agents","stargazers_count":2039,"pushed_at":"2025-07-25T11:08:48Z","license":"MIT","archived":true}
{"full_name":"contains-studio/agents","stargazers_count":12419,"pushed_at":"2025-07-28T16:13:43Z","license":null,"archived":false}
{"full_name":"0xfurai/claude-code-subagents","stargazers_count":1020,"pushed_at":"2025-10-15T19:50:24Z","license":"MIT","archived":false}
{"full_name":"lst97/claude-code-sub-agents","stargazers_count":1703,"pushed_at":"2025-08-15T11:02:46Z","license":"MIT","archived":false}
{"full_name":"vijaythecoder/awesome-claude-agents","stargazers_count":4402,"pushed_at":"2025-10-30T00:06:52Z","license":"MIT","archived":false}
{"full_name":"ComposioHQ/awesome-claude-skills","stargazers_count":78235,"pushed_at":"2026-09-18T07:16:11Z","license":null,"archived":false}
{"full_name":"travisvn/awesome-claude-skills","stargazers_count":15617,"pushed_at":"2026-04-28T19:30:24Z","license":null,"archived":false}
{"full_name":"JetBrains/skills","stargazers_count":385,"pushed_at":"2026-10-21T19:05:26Z","license":null,"archived":false}
{"full_name":"actionbook/rust-skills","stargazers_count":1553,"pushed_at":"2026-08-23T11:09:39Z","license":null,"archived":false}
{"full_name":"alirezarezvani/claude-skills","stargazers_count":28941,"pushed_at":"2026-10-29T07:44:34Z","license":"MIT","archived":false}
{"full_name":"sickn33/agentic-awesome-skills","stargazers_count":48700,"pushed_at":"2026-10-29T09:32:21Z","license":"MIT","archived":false}
{"full_name":"kdcokenny/opencode-background-agents","stargazers_count":384,"pushed_at":"2026-09-16T03:53:30Z","license":"MIT","archived":true}
{"full_name":"rohitg00/awesome-claude-code-toolkit","stargazers_count":2786,"pushed_at":"2026-05-12T07:18:34Z","license":"Apache-2.0","archived":false}
{"full_name":"NeoLabHQ/context-engineering-kit","stargazers_count":1792,"pushed_at":"2026-08-26T21:08:01Z","license":"GPL-3.0","archived":false}
{"full_name":"disler/claude-code-hooks-mastery","stargazers_count":3968,"pushed_at":"2026-03-04T18:16:25Z","license":null,"archived":false}
{"full_name":"coleam00/context-engineering-intro","stargazers_count":13896,"pushed_at":"2026-03-16T12:13:59Z","license":"MIT","archived":false}
{"full_name":"buildermethods/agent-os","stargazers_count":5561,"pushed_at":"2026-10-07T04:18:58Z","license":"MIT","archived":false}
{"full_name":"anthropics/claude-code-security-review","stargazers_count":6637,"pushed_at":"2026-02-11T18:01:23Z","license":"MIT","archived":false}
```

Renames resolved through the API: ruvnet/claude-flow → ruvnet/ruflo; affaan-m/everything-claude-code → affaan-m/ECC;
steveyegge/beads → gastownhall/beads; code-yeongyu/oh-my-opencode → code-yeongyu/oh-my-openagent;
glittercowboy/get-shit-done → gsd-build/get-shit-done (archived) → open-gsd/gsd-core (per its README);
sst/opencode → anomalyco/opencode; forrestchang/andrej-karpathy-skills → multica-ai/andrej-karpathy-skills;
sickn33/antigravity-awesome-skills → sickn33/agentic-awesome-skills;
jeremylongshore/claude-code-plugins-plus → jeremylongshore/tons-of-skills-marketplace (2,884★, not ranked).

Official pages fetched (HTTP 200 on 2026-10-29):
- code.claude.com/docs/en/{sub-agents,skills,agent-teams,plugins}.md
- opencode.ai/docs/{agents,skills,rules}/
- anthropic.com/engineering/{building-effective-agents,multi-agent-research-system,equipping-agents-for-the-real-world-with-agent-skills,claude-code-best-practices}
- agentskills.io/specification
- kotlinlang.org/docs/kotlin-ai-skills.html

## 7. Open items ([UNVERIFIED])
- spec-kit's exact OpenCode integration key, and OpenSpec's OpenCode support (READMEs point to external docs that
  were not fetched).
- open-gsd/gsd-core install path and current workflow (README not read; only the redirect note in the archived repo).
- Whether wshobson/agents has a dedicated Kotlin agent (only the `jvm-languages` agents `csharp-pro`, `java-pro`
  and `scala-pro` were listed).
- Star counts move by the hour. The numbers above are snapshots from the API calls logged in §6.
