# `dotnet test` command matrix (SDK 10, October 2026)

The single most common agent mistake in .NET repositories is using the wrong `dotnet test` syntax
for the test platform in use. Decide the mode first, then build the command.

Adapted (paraphrased and condensed) from the MIT-licensed `run-tests` skill in
[dotnet/skills](https://github.com/dotnet/skills) and the Microsoft.Testing.Platform docs in
dotnet/docs, checked 2026-10-29.

## 1. Detect the mode

| Signal (evaluate `global.json`, the `.csproj`, and imported `Directory.*.props`) | Mode | Command shape |
|---|---|---|
| SDK 10+ and `global.json` has `"test": { "runner": "Microsoft.Testing.Platform" }` | Native MTP | `dotnet test --project <proj> [options]` (no `--` separator, no positional path) |
| VSTest mode + MTP-capable framework + `TestingPlatformDotnetTestSupport=true` + `OutputType=Exe` | VSTest-mode bridge to MTP (SDK 8/9, or MTP v1 only) | `dotnet test <proj> [dotnet options] -- [MTP options]` |
| `Microsoft.NET.Test.Sdk` + adapter (xunit.runner.visualstudio, NUnit3TestAdapter, MSTest.TestAdapter), no MTP signals | VSTest | `dotnet test <proj> [VSTest options]` |
| `TUnit` | MTP only | native mode, bridge, or `dotnet run --project <proj> -- [options]` |
| SDK 8/9 | VSTest command mode only (bridge possible) | as above |

Measured on SDK 10.0.403 with xunit.v3 4.0.2 (MTP v2), 2026-10-29: running the project in VSTest
mode fails at build time with `error : Testing with VSTest target is no longer supported by
Microsoft.Testing.Platform on .NET 10 SDK and later`. The official docs state that MTP v2 drops the
VSTest-mode bridge on the .NET 10 SDK. So on SDK 10, MTP v2 frameworks (xUnit v3 4.x, TUnit, and MSTest 4
with `EnableMSTestRunner`; all depend on Microsoft.Testing.Platform 2.5.2) need the `global.json` `test.runner` block and the `--project` form.

`--project`, `--solution` and `--test-modules` exist only in native MTP mode. In bridge mode,
`dotnet`/MSBuild options (`-c`, `-f`, `--no-build`, `-v`) go before `--` and MTP options after it.

## 2. Packages per framework (versions as of 2026-10-29)

| Framework | Packages | Platform |
|---|---|---|
| xUnit v3 | `xunit.v3` 4.0.2 (depends on `xunit.v3.mtp-v2`, i.e. MTP v2), `xunit.runner.visualstudio` 4.0.1 only if VSTest/IDE discovery is needed | MTP (VSTest via runner package) |
| MSTest | `MSTest` 4.5.2 metapackage | MTP or VSTest |
| NUnit | `NUnit` 5.0.0 + `NUnit3TestAdapter` 6.3.1 + `NUnit.Analyzers` 4.15.0 (adapter/NUnit 5 pairing not checked this session [UNVERIFIED]; read the adapter release notes before upgrading) | VSTest or MTP (adapter's MTP mode) |
| TUnit | `TUnit` 1.76.45 | MTP only |
| Coverage | `Microsoft.Testing.Extensions.CodeCoverage` 18.12.0 (MTP `--coverage`), `coverlet.MTP` 10.1.0 (MTP `--coverlet`), `coverlet.collector` 10.1.0 (VSTest) | |

Never add or upgrade test packages unless the task requires it; mismatched runner packages are a
common cause of "0 tests discovered".

## 3. Commands by intent

```bash
# Run all tests
dotnet test                                                    # VSTest / bridge
dotnet test --project tests/App.Tests                          # native MTP

# One project, Release, no rebuild (after `dotnet build -c Release`)
dotnet test tests/App.Tests -c Release --no-build
dotnet test --project tests/App.Tests -c Release --no-build

# Filter: VSTest with MSTest / NUnit / xUnit v2
dotnet test --filter "FullyQualifiedName~OrderServiceTests&TestCategory=Unit"
# Filter: MTP with MSTest or NUnit (same expression; after -- in bridge mode)
dotnet test --project tests/App.Tests --filter "TestCategory=Unit"
dotnet test tests/App.Tests -- --filter "TestCategory=Unit"          # bridge (SDK 8/9)
# Filter: MTP with xUnit v3 (its own flags; VSTest --filter syntax does not apply)
dotnet test --project tests/App.Tests --filter-class "*ShoppingCartTests*"
dotnet test --project tests/App.Tests --filter-trait "Category=Integration"
dotnet test --project tests/App.Tests --filter-query "/*/*/*Integration*/*[Category=Smoke]"
# Filter: TUnit (tree-node path)
dotnet test --project tests/App.Tests --treenode-filter "/*/*/SmsNotificationTests/*"
dotnet run --project tests/App.Tests -- --treenode-filter "/*/*/SmsNotificationTests/*"
```

| Outcome | VSTest | MTP (native: direct; bridge: after `--`) |
|---|---|---|
| TRX report | `--logger "trx;LogFileName=results.trx"` | `--report-trx` (TrxReport extension) |
| Results dir | `--results-directory <dir>` | `--results-directory <dir>` |
| Diagnostic log | `--diag <file>` | `--diagnostic --diagnostic-output-directory <dir>` |
| Crash dump | `--blame-crash` | `--crashdump` (CrashDump extension) |
| Hang dump | `--blame-hang --blame-hang-timeout 5min` | `--hangdump --hangdump-timeout 5min` (HangDump extension) |
| Coverage | `--collect "XPlat Code Coverage"` (coverlet.collector) or `--collect "Code Coverage"` | `--coverage --coverage-output-format cobertura` (CodeCoverage) or `--coverlet --coverlet-output-format cobertura` (coverlet.MTP) |

An "unknown option" error from MTP means the extension is not referenced or the option is on the
wrong side of `--`. Inspect package references before adding anything.

## 4. Coverage report

```bash
dotnet tool install -g dotnet-reportgenerator-globaltool     # 5.5.12 as of 2026-10-29
reportgenerator -reports:"**/TestResults/**/*.cobertura.xml" -targetdir:artifacts/coverage \
  -reporttypes:"TextSummary;Html"
cat artifacts/coverage/Summary.txt
```

Judge coverage on the files you changed (open the HTML or filter with `-filefilters:`), not the
repository total, which hides untested new code.

## 5. Mutation testing (Stryker.NET 5.0.0)

```bash
dotnet tool install -g dotnet-stryker
dotnet stryker --project src/App/App.csproj --break-at 60          # VSTest runner (default)
dotnet stryker --test-runner mtp --break-at 60                      # MTP runner (preview in 5.0)
dotnet stryker --since:main                                          # only mutants in changed code
```

`--break-at` makes Stryker exit non-zero below the score; use it on critical domain logic, not on
the whole repository on every PR (it is slow).

## 6. Integration tests

- `WebApplicationFactory<Program>` (Microsoft.AspNetCore.Mvc.Testing 10.0.14) for in-memory HTTP
  tests; override services with `WithWebHostBuilder(b => b.ConfigureTestServices(...))`.
- Testcontainers 4.16.0 for real PostgreSQL/SQL Server/Redis/RabbitMQ; requires a running Docker
  (or compatible) engine. If none is available, report the integration gate as `NOT RUN` instead
  of switching to the EF Core InMemory provider.
- Aspire apps: `Aspire.Hosting.Testing` with `DistributedApplicationTestingBuilder` spins up the
  AppHost's resources for end-to-end tests.
