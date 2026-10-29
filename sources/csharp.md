# Sources: C# / .NET (slug `csharp`)

Provenance for `claude/agents/csharp-engineer.md` and `skills/csharp-engineering/` (SKILL.md plus
`references/project-baseline.md`, `references/test-commands.md`, `references/diagnostics.md`).
All fetches on 2026-10-29. Mined repositories were read as text only; no code or install step from
them was run.

## 1. GitHub repositories used (exactly 5)

Metadata from `ghapi.sh repos/<owner>/<repo>` on 2026-10-29 (fields pasted verbatim from the JSON).

### 1.1 dotnet/skills
- Link: https://github.com/dotnet/skills
- `{"full_name": "dotnet/skills", "stargazers_count": 5762, "pushed_at": "2026-10-29T08:56:30Z", "archived": false, "license": "MIT"}`
- Read: `README.md`, `plugins/dotnet/skills/csharp-expert/SKILL.md`,
  `plugins/dotnet-test/skills/run-tests/SKILL.md`,
  `plugins/dotnet-diag/skills/analyzing-dotnet-performance/references/critical-patterns.md`,
  `plugins/dotnet-upgrade/skills/migrate-dotnet10-to-dotnet11/SKILL.md`,
  `plugins/dotnet-nuget/skills/convert-to-cpm/SKILL.md`, `plugins/dotnet/.lsp.json`,
  `plugins/dotnet-msbuild/.claude-plugin/plugin.json`,
  `plugins/dotnet-msbuild/skills/troubleshoot-binlog-mcp/SKILL.md`.
- Taken (MIT, adapted with attribution): the VSTest vs native-MTP vs bridge decision table and the
  report/dump/coverage option mapping (condensed into `references/test-commands.md`); the
  "do not raise SDK/TFM/LangVersion to make an edit compile" and "use `leaveOpen` instead of leaking
  wrappers" fallback rules; hot-path patterns (span slicing, `ArrayPool`, `[GeneratedRegex]`,
  `TryGetValue`, ordinal comparison, single-await `ValueTask`); the .NET 10 to 11 breaking-change
  inventory (OpenAPI v3, EF Design package, x86-64-v2 baseline); the Roslyn LSP and binlog MCP
  launch commands mentioned as optional extras.
- Correction found while cross-checking: its migration skill summarizes the .NET 11
  BackgroundService change as "exceptions now crash the host". The official breaking-change page
  (`docs/core/compatibility/extensions/11/ihost-runasync-stopasync-throw-backgroundservice-failure.md`)
  says `IHost.RunAsync`/`StopAsync` now rethrow the failure (non-zero exit) when the behavior is
  `StopHost`. The agent uses the official wording.

### 1.2 Aaronontheweb/dotnet-skills
- Link: https://github.com/Aaronontheweb/dotnet-skills
- `{"full_name": "Aaronontheweb/dotnet-skills", "stargazers_count": 1242, "pushed_at": "2026-10-28T18:27:36Z", "archived": false, "license": "MIT"}`
- Read: repository tree, `skills/csharp-coding-standards/SKILL.md`,
  `skills/csharp-concurrency-patterns/SKILL.md`, `skills/project-structure/SKILL.md`,
  `skills/package-management/SKILL.md`, `skills/slopwatch/SKILL.md`,
  `skills/efcore-patterns/SKILL.md`.
- Taken (MIT, paraphrased): `readonly record struct` value objects with no implicit conversions;
  the concurrency escalation ladder (async/await, then `Parallel.ForEachAsync`, then `Channel<T>`,
  locks last); "manage packages through the CLI, never hand-edit XML" with CPM; `.slnx` as the
  .NET 10 default and one solution format per repo; the "LLM slop" list (skipped tests,
  `#pragma`/`<NoWarn>` suppression, empty catches, `Task.Delay` in tests, inline versions under
  CPM) that became the agent's Anti-patterns; EF Core no-tracking by default and CLI-only
  migrations.
- Not adopted: its blanket ban on Mapster (kept as an MIT-licensed option) and its Akka.NET-centric
  escalation levels (out of scope for a general agent).

### 1.3 github/awesome-copilot
- Link: https://github.com/github/awesome-copilot
- `{"full_name": "github/awesome-copilot", "stargazers_count": 40541, "pushed_at": "2026-10-29T00:07:04Z", "archived": false, "license": "MIT"}`
- Read: `agents/CSharpExpert.agent.md`, `instructions/csharp.instructions.md`,
  `instructions/dotnet-architecture-good-practices.instructions.md` (tree listing for the rest).
- Taken (MIT, paraphrased): the "do first" orientation checklist (read TFM, C# version,
  `global.json`, `Directory.*` files before editing); least-exposure visibility rule; "no interfaces
  only for testing"; do not edit generated code; test conventions (behavior names, one behavior per
  test, no branching in tests, test through public API, use the framework already in the
  solution); the async checklist items for timeouts via linked `CancellationTokenSource` and
  `await using`.

### 1.4 davidfowl/AspNetCoreDiagnosticScenarios
- Link: https://github.com/davidfowl/AspNetCoreDiagnosticScenarios
- `{"full_name": "davidfowl/AspNetCoreDiagnosticScenarios", "stargazers_count": 8503, "pushed_at": "2024-05-28T16:50:09Z", "archived": false, "license": null}`
- No license file, so **paraphrase only**; no text copied.
- Read: `AsyncGuidance.md`, `AspNetCoreGuidance.md`, `README.md`.
- Taken (ideas, restated in our own words): sync-over-async and thread-pool starvation, `async void`
  crashes, `TaskCompletionSource` with `RunContinuationsAsynchronously`, disposing timeout
  `CancellationTokenSource`s, flushing writers before dispose, keeping `async`/`await` instead of
  eliding when `using`/`try` are involved, `ConcurrentDictionary.GetOrAdd` running factories more
  than once, `AsyncLocal` leaks, and the `HttpContext` thread-safety and lifetime rules. Older than
  2026 but still the canonical reference; behaviors were not contradicted by current docs.

### 1.5 stryker-mutator/stryker-net
- Link: https://github.com/stryker-mutator/stryker-net
- `{"full_name": "stryker-mutator/stryker-net", "stargazers_count": 2116, "pushed_at": "2026-10-29T07:34:09Z", "archived": false, "license": "Apache-2.0"}`
- Read: releases API (`dotnet-stryker@5.0.0` 2026-09-11, 4.16.0, 4.15.0 notes) and
  `docs/configuration.md` (`test-runner`, `break-at`, `since`, `project`).
- Taken: 5.0.0 targets the .NET 10 runtime; MTP runner via `--test-runner mtp` is in preview;
  `--break-at` fails CI below a score; `--since:<committish>` limits mutants to changed code;
  `--project` selects the project to mutate.

## 2. MCP servers declared by the agent (verified 2026-10-29)

| Server | How declared | Verification |
|---|---|---|
| `github` | by name (pre-configured in the pack) | `github/github-mcp-server`: `{"stargazers_count": 34054, "pushed_at": "2026-10-29T05:42:25Z", "license": "MIT"}` |
| `context7` | inline `type: http`, `url: https://mcp.context7.com/mcp` | `upstash/context7`: `{"stargazers_count": 63882, "pushed_at": "2026-10-28T20:26:24Z", "license": "MIT"}`; README: "use the Context7 server URL `https://mcp.context7.com/mcp` ... pass your API key via the `Authorization: Bearer` header" (key recommended, not required). MCP `initialize` POST returned HTTP 200 without a key; `tools/list` returned `['resolve-library-id', 'query-docs']`. |
| `microsoft-learn` | inline `type: http`, `url: https://learn.microsoft.com/api/mcp` | `MicrosoftDocs/mcp`: `{"stargazers_count": 1958, "pushed_at": "2026-10-25T04:04:28Z", "license": "CC-BY-4.0"}` (repo license covers docs/samples; the server is a free hosted Microsoft service, "No API keys, no logins"). README standard config is `{"type": "http", "url": "https://learn.microsoft.com/api/mcp"}`; tools `microsoft_docs_search`, `microsoft_docs_fetch`, `microsoft_code_sample_search`. MCP `initialize` POST returned HTTP 200 and `tools/list` returned exactly those three tools. |
| `nuget` | inline `type: stdio`, `command: dnx`, `args: [NuGet.Mcp.Server@1.4.16, --source, https://api.nuget.org/v3/index.json, --yes]` | Package `NuGet.Mcp.Server` 1.4.16 published 2026-06-30 (nuget.org registration API); package `LICENSE.txt` is MIT (read from the .nupkg); nuspec `projectUrl` is https://github.com/NuGet/Home (`{"stargazers_count": 1554, "pushed_at": "2026-10-20T18:19:42Z", "license": "NOASSERTION"}`). Command shape copied from the package README / Microsoft Learn page "Using the NuGet MCP Server" (`"command": "dnx", "args": ["NuGet.Mcp.Server@1.0.0", "--source", "https://api.nuget.org/v3/index.json", "--yes"]`), with the version set to the current 1.4.16. Requires .NET 10 SDK (`dnx`). Telemetry on by default; opt out with `DOTNET_CLI_TELEMETRY_OPTOUT`. Launched in this session with the exact declared args via `dnx` from SDK 10.0.403: `initialize` returned `{'name': 'NuGet.Mcp.Server', 'version': '1.0.0.0'}`, `tools/list` returned the six tools (section 5). |

Considered and not declared: `Microsoft.AITools.BinlogMcp` 3.0.4 (used by dotnet/skills'
`dotnet-msbuild` plugin; source repo `dotnet-microsoft/ai-tools` is not public and the package
license is the proprietary "Microsoft .NET Library" terms), mentioned only as an optional extra;
`baronfel/mcp-binlog-tool` (22 stars, no license, self-described demo).

## 3. Official version and behavior sources (fetched 2026-10-29)

| Fact | Source |
|---|---|
| .NET channel status, latest runtime/SDK, release dates, EOL dates (10.0.14 / SDK 10.0.403 on 2026-10-25, LTS to 2028-11-14; 11.0.0-rc.3 go-live; 8.0 and 9.0 EOL 2026-11-10) | https://builds.dotnet.microsoft.com/dotnet/release-metadata/releases-index.json, https://builds.dotnet.microsoft.com/dotnet/release-metadata/10.0/releases.json, https://builds.dotnet.microsoft.com/dotnet/release-metadata/11.0/releases.json |
| C# 14 feature list | https://learn.microsoft.com/dotnet/csharp/whats-new/csharp-14 (raw: dotnet/docs `docs/csharp/whats-new/csharp-14.md`) |
| C# 15 feature list, default for `net11.0`, memory-safety preview | https://learn.microsoft.com/dotnet/csharp/whats-new/csharp-15 (ms.date 2026-10-19) |
| .NET 10 overview, SDK changes (MTP in `dotnet test`, noun-first CLI, package pruning, console container publish, `dnx`) | https://learn.microsoft.com/dotnet/core/whats-new/dotnet-10/overview, https://learn.microsoft.com/dotnet/core/whats-new/dotnet-10/sdk |
| .NET 11 SDK changes (`--min-publish-age-hours`, test improvements) | https://learn.microsoft.com/dotnet/core/whats-new/dotnet-11/sdk |
| .NET 11 BackgroundService/`RunAsync` breaking change | https://learn.microsoft.com/dotnet/core/compatibility/extensions/11/ihost-runasync-stopasync-throw-backgroundservice-failure |
| ASP.NET Core 10: Minimal API validation (`AddValidation`), OpenAPI 3.1 default, JSON Patch on STJ | https://learn.microsoft.com/aspnet/core/release-notes/aspnetcore-10.0 (raw: dotnet/AspNetCore.Docs `aspnetcore/release-notes/aspnetcore-10/includes/*.md`) |
| NuGet Audit defaults (`NuGetAuditMode` = `all` for net10.0+), `dotnet package update --vulnerable` | https://learn.microsoft.com/nuget/concepts/auditing-packages |
| CPM, `GlobalPackageReference`, transitive pinning | https://learn.microsoft.com/nuget/consume-packages/central-package-management |
| `dotnet format` options (`--verify-no-changes`) | https://learn.microsoft.com/dotnet/core/tools/dotnet-format |
| MSBuild analysis properties (`AnalysisLevel`, `EnforceCodeStyleInBuild`) | https://learn.microsoft.com/dotnet/core/project-sdk/msbuild-props |
| IDE0005 needs XML docs to report on build | https://learn.microsoft.com/dotnet/fundamentals/code-analysis/style-rules/ide0005 |
| MTP code coverage options (`--coverage`, `--coverlet`) | https://learn.microsoft.com/dotnet/core/testing/microsoft-testing-platform-code-coverage |
| `dotnet test` VSTest mode vs MTP mode; MTP v2 drops the VSTest-mode bridge on the .NET 10 SDK | https://learn.microsoft.com/dotnet/core/testing/unit-testing-with-dotnet-test |
| dotnet-trace profiles (`cpu-sampling` removed; `dotnet-common`, `dotnet-sampled-thread-time`, `gc-verbose`; `collect-linux`) | https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-trace |
| dotnet-counters syntax; `dotnet.thread_pool.queue.length` metric | https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-counters, https://learn.microsoft.com/dotnet/core/diagnostics/built-in-metrics-runtime |
| CSharpier `format`/`check` CLI | https://github.com/belav/csharpier (docs `Src/Website/docs/CLI.md`) |
| BenchmarkDotNet console args (`--filter`, `--memory`, `--join`) | https://github.com/dotnet/BenchmarkDotNet (docs `docs/articles/guides/console-args.md`) |
| Claude Code subagent frontmatter, `skills` preloading, nested-subagent depth limit | https://code.claude.com/docs/en/sub-agents.md |
| Package versions and publish dates (all NuGet versions in the agent's baseline table) | https://api.nuget.org/v3-flatcontainer/{id}/index.json and https://api.nuget.org/v3/registration5-gz-semver2/{id}/{version}.json |
| FluentAssertions 8+ license (Xceed community license, non-commercial) | https://xceed.com/fluent-assertions-faq/ and nuspec projectUrl |
| AutoMapper 15+ / MediatR 13+ commercial license | https://luckypennysoftware.com/faq |
| AwesomeAssertions is the Apache-2.0 continuation | https://awesomeassertions.org/about/ and nuspec `licenseExpression` = Apache-2.0 |

## 4. Unverified items (kept and labeled, or left out)

- .NET 11 GA date (expected November 2026) is not stated in the release metadata; labeled
  `[UNVERIFIED date]` in the agent.
- NUnit 5.0.0 with NUnit3TestAdapter 6.3.1 pairing not checked; labeled in `test-commands.md`.
- Native AOT publish gate (`-p:PublishAot=true`) was not executed (needs the native toolchain);
  the command shape comes from the official docs. Hang-dump and benchmark gates were run only in
  the trivial form shown in section 5.

## 5. Execution evidence (gate commands run on a sample solution, 2026-10-29)

.NET SDK installed into the session scratchpad with the official `dotnet-install.sh --channel 10.0`
(`dotnet --version` printed `10.0.403`). Sample solution built from the
`references/project-baseline.md` templates verbatim (global.json with MTP runner,
Directory.Build.props, Directory.Packages.props, nuget.config, .editorconfig), one class library and
one xUnit v3 test project; packages added with `dotnet package add` (CPM wrote bare
`PackageReference`s). Trimmed real output:

```text
$ dotnet new sln -n Sample        -> created Sample.slnx (slnx is the SDK 10 default)
$ dotnet restore --locked-mode    -> Restored ... exit=0
$ dotnet format --verify-no-changes --no-restore   (first run, deliberately unfixed sample)
  SlugTests.cs(1,1): warning IDE0005: Using directive is unnecessary.
  Class1.cs(3,21): warning MA0048: File name must match type name (class Slug)
  format_exit=2
$ dotnet format --verify-no-changes --no-restore   (after fixes)  -> format_exit=0
$ dotnet build -c Release --no-restore -warnaserror -> 0 Warning(s) 0 Error(s) build_exit=0
$ dotnet test --project tests/App.Tests -c Release --no-build
  Test run summary: Passed!  total: 2  failed: 0  succeeded: 2  skipped: 0   test_exit=0
$ dotnet test --project tests/App.Tests -c Release --no-build --coverage --coverage-output-format cobertura
  total: 2 failed: 0 -> ./TestResults/<guid>.cobertura.xml
$ dnx dotnet-reportgenerator-globaltool --yes -- -reports:"**/TestResults/**/*.cobertura.xml" -targetdir:artifacts/coverage -reporttypes:TextSummary
  Line coverage: 100%  Covered lines: 2
$ dotnet test --project tests/App.Tests -c Release --no-build --filter-class "*SlugTests*"  -> total: 2 failed: 0
$ dotnet test ... --hangdump --hangdump-timeout 5min   (before adding the HangDump extension)
  Handshake failures ... Exit code: 5            (after `dotnet package add Microsoft.Testing.Extensions.HangDump`: total: 2 failed: 0)
$ dotnet package list --vulnerable --include-transitive
  The given project `App` has no vulnerable packages given the current sources.
$ (global.json without test.runner) dotnet test tests/App.Tests/App.Tests.csproj -c Release --no-build -- --coverage
  error : Testing with VSTest target is no longer supported by Microsoft.Testing.Platform on .NET 10 SDK and later. ...  bridge_exit=1
$ dnx csharpier@1.3.0 --yes -- check .   -> lists the unformatted file, csharpier_exit=1
$ (added `load().Result` to a source file) dotnet build -c Release -warnaserror
  error VSTHRD002: Synchronously waiting on tasks or awaiters may cause deadlocks.   1 Error(s)
$ dnx dotnet-stryker@5.0.0 --yes -- --test-runner mtp --break-at 60   (in tests/App.Tests)
  Killed: 1 Survived: 0 ... The final mutation score is 100.00 %   stryker_exit=0
$ python3 mcpprobe.py dnx NuGet.Mcp.Server@1.4.16 --source https://api.nuget.org/v3/index.json --yes
  initialize: {'name': 'NuGet.Mcp.Server', 'version': '1.0.0.0'}
  tools: ['review_supply_chain_security', 'get_latest_package_version', 'get_package_context', 'fix_vulnerable_packages', 'update_package_version', 'upgrade_packages_to_latest']
```

What this changed in the deliverables: the VSTest-mode bridge row and all `-- --coverage` examples
were rewritten to native MTP for SDK 10 (the dotnet/skills `run-tests` guidance still shows the
bridge on SDK 10, which fails with MTP v2); the agent's failure list gained the exact bridge error;
the baseline notes MA0048 as an opinionated Meziantou rule.

## 6. Self-check results

Run on 2026-10-29 after the final edits (`python3 -I selfcheck.py`, `bash linkcheck.sh`; GitHub URLs checked with `ghapi.sh repos/<owner>/<repo>`, other URLs with `curl -L` status codes; MCP endpoints checked by JSON-RPC POST in section 2).

```text
yaml.safe_load OK: claude/agents/csharp-engineer.md keys= ['name', 'description', 'model', 'skills', 'mcpServers']
  invalid keys: none | name= csharp-engineer | model= inherit | skills= ['csharp-engineering']
  mcpServers: ['github', {'context7': ('http', 'https://mcp.context7.com/mcp')}, {'microsoft-learn': ('http', 'https://learn.microsoft.com/api/mcp')}, {'nuget': ('stdio', 'dnx')}]
  lines: 451
yaml.safe_load OK: skills/csharp-engineering/SKILL.md keys= ['name', 'description']
  lines: 294
heading check: PASS ['## Role and scope', '## Operating loop', '## Toolchain baseline (October 2026)', '## Engineering rules', '## Verification gates', '## Delegation', '## MCP and skills usage', '## Anti-patterns', '## Output contract']

link check: 38 URLs, 33 OK, 3 placeholder skipped, 2 MCP endpoints, 0 failed
SKIP(placeholder) https://api.nuget.org/v3-flatcontainer/{id}/index.json
200 https://api.nuget.org/v3/index.json
SKIP(placeholder) https://api.nuget.org/v3/registration5-gz-semver2/{id}/{version}.json
200 https://awesomeassertions.org/about/
200 https://builds.dotnet.microsoft.com/dotnet/release-metadata/10.0/releases.json
200 https://builds.dotnet.microsoft.com/dotnet/release-metadata/11.0/releases.json
200 https://builds.dotnet.microsoft.com/dotnet/release-metadata/releases-index.json
200 https://code.claude.com/docs/en/sub-agents.md
ghapi-OK Aaronontheweb/dotnet-skills https://github.com/Aaronontheweb/dotnet-skills
ghapi-OK NuGet/Home https://github.com/NuGet/Home
ghapi-OK belav/csharpier https://github.com/belav/csharpier
ghapi-OK davidfowl/AspNetCoreDiagnosticScenarios https://github.com/davidfowl/AspNetCoreDiagnosticScenarios
ghapi-OK dotnet/BenchmarkDotNet https://github.com/dotnet/BenchmarkDotNet
ghapi-OK dotnet/skills https://github.com/dotnet/skills
ghapi-OK github/awesome-copilot https://github.com/github/awesome-copilot
ghapi-OK stryker-mutator/stryker-net https://github.com/stryker-mutator/stryker-net
MCP(POST-verified separately) https://learn.microsoft.com/api/mcp
200 https://learn.microsoft.com/aspnet/core/release-notes/aspnetcore-10.0
200 https://learn.microsoft.com/dotnet/core/compatibility/extensions/11/ihost-runasync-stopasync-throw-backgroundservice-failure
200 https://learn.microsoft.com/dotnet/core/diagnostics/built-in-metrics-runtime
200 https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-counters
200 https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-trace
200 https://learn.microsoft.com/dotnet/core/project-sdk/msbuild-props
200 https://learn.microsoft.com/dotnet/core/testing/microsoft-testing-platform-code-coverage
200 https://learn.microsoft.com/dotnet/core/testing/unit-testing-with-dotnet-test
200 https://learn.microsoft.com/dotnet/core/tools/dotnet-format
200 https://learn.microsoft.com/dotnet/core/whats-new/dotnet-10/overview
200 https://learn.microsoft.com/dotnet/core/whats-new/dotnet-10/sdk
200 https://learn.microsoft.com/dotnet/core/whats-new/dotnet-11/sdk
200 https://learn.microsoft.com/dotnet/csharp/whats-new/csharp-14
200 https://learn.microsoft.com/dotnet/csharp/whats-new/csharp-15
200 https://learn.microsoft.com/dotnet/fundamentals/code-analysis/style-rules/ide0005
200 https://learn.microsoft.com/nuget/concepts/auditing-packages
200 https://learn.microsoft.com/nuget/consume-packages/central-package-management
200 https://luckypennysoftware.com/faq
MCP(POST-verified separately) https://mcp.context7.com/mcp
SKIP(placeholder) https://pkgs.example.com/nuget/v3/index.json
200 https://xceed.com/fluent-assertions-faq/
```
