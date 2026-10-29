# Project baseline templates (October 2026)

Starting points for a new solution or for aligning an existing one. Adapt, do not paste blindly:
an existing repository's settings win unless the user asked to change them. Package versions are
nuget.org latest-stable as of 2026-10-29; confirm with the NuGet MCP server before committing.

## global.json

```json
{
  "sdk": {
    "version": "10.0.403",
    "rollForward": "latestFeature"
  },
  "test": {
    "runner": "Microsoft.Testing.Platform"
  }
}
```

- `latestFeature` allows newer patch and feature bands of 10.0 (security fixes) but never a new
  major SDK.
- Add the `test.runner` block only when every test project runs on Microsoft.Testing.Platform
  (xUnit v3, MSTest 3.x/4.x with MTP, NUnit with MTP, TUnit). It switches `dotnet test` to native
  MTP command mode on SDK 10+, which changes the command-line syntax (see `test-commands.md`).

## Directory.Build.props (repository root)

```xml
<Project>
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <WarningsAsErrors>$(WarningsAsErrors);nullable</WarningsAsErrors>

    <AnalysisLevel>latest-recommended</AnalysisLevel>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
    <!-- IDE0005 (unused usings) only reports on build when XML docs are generated. -->
    <GenerateDocumentationFile>true</GenerateDocumentationFile>
    <!-- Apps: don't require XML comments on every public member. Libraries: remove this line. -->
    <NoWarn>$(NoWarn);CS1591</NoWarn>

    <RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>
  </PropertyGroup>

  <PropertyGroup Condition="'$(CI)' == 'true' or '$(TF_BUILD)' == 'true' or '$(GITHUB_ACTIONS)' == 'true'">
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <ContinuousIntegrationBuild>true</ContinuousIntegrationBuild>
    <RestoreLockedMode>true</RestoreLockedMode>
  </PropertyGroup>
</Project>
```

Notes:
- Per-project settings (`OutputType`, `IsPackable`, `PublishAot`, `IsAotCompatible`, `UserSecretsId`)
  stay in the `.csproj`.
- Test projects: put `<IsPackable>false</IsPackable>` in a `tests/Directory.Build.props` that
  imports the parent with
  `<Import Project="$([MSBuild]::GetPathOfFileAbove('Directory.Build.props', '$(MSBuildThisFileDirectory)../'))" />`.
- `TreatWarningsAsErrors` everywhere (not only CI) is fine for small repos; CI-only keeps local
  iteration fast while still failing PRs.

## Directory.Packages.props (Central Package Management)

```xml
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
    <CentralPackageTransitivePinningEnabled>true</CentralPackageTransitivePinningEnabled>
  </PropertyGroup>

  <!-- Analyzers applied to every project. -->
  <ItemGroup>
    <GlobalPackageReference Include="Microsoft.VisualStudio.Threading.Analyzers" Version="18.12.1" />
    <GlobalPackageReference Include="Meziantou.Analyzer" Version="3.0.317" />
  </ItemGroup>

  <ItemGroup>
    <!-- Runtime -->
    <PackageVersion Include="Microsoft.Extensions.Http.Resilience" Version="10.11.0" />
    <PackageVersion Include="Microsoft.EntityFrameworkCore" Version="10.0.14" />
    <PackageVersion Include="OpenTelemetry.Extensions.Hosting" Version="1.20.1" />
    <!-- Tests -->
    <PackageVersion Include="xunit.v3" Version="4.0.2" />
    <PackageVersion Include="AwesomeAssertions" Version="9.6.0" />
    <PackageVersion Include="NSubstitute" Version="6.2.0" />
    <PackageVersion Include="Microsoft.AspNetCore.Mvc.Testing" Version="10.0.14" />
    <PackageVersion Include="Testcontainers" Version="4.16.0" />
    <PackageVersion Include="Microsoft.Extensions.TimeProvider.Testing" Version="10.11.0" />
    <PackageVersion Include="Microsoft.Testing.Extensions.CodeCoverage" Version="18.12.0" />
  </ItemGroup>
</Project>
```

- Projects then use `<PackageReference Include="xunit.v3" />` with no `Version`.
- Meziantou.Analyzer is opinionated (for example MA0048 "file name must match type name" fired on
  a default `Class1.cs` when this baseline was tested); tune individual rule severities in
  `.editorconfig` rather than dropping the package.
- `CentralPackageTransitivePinningEnabled` lets a `PackageVersion` entry override a vulnerable
  transitive version; prefer updating the direct dependency first.
- Add packages with `dotnet package add <id> --project <csproj>`; with CPM enabled the CLI writes
  the version to `Directory.Packages.props` and the bare reference to the project.

## nuget.config

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <clear />
    <add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
    <!-- <add key="internal" value="https://pkgs.example.com/nuget/v3/index.json" /> -->
  </packageSources>
  <packageSourceMapping>
    <packageSource key="nuget.org">
      <package pattern="*" />
    </packageSource>
    <!-- <packageSource key="internal"><package pattern="Contoso.*" /></packageSource> -->
  </packageSourceMapping>
</configuration>
```

`<clear/>` stops machine-level feeds from leaking into restores; source mapping prevents a public
package from shadowing an internal one (dependency confusion). Never commit feed credentials; use
a credential provider or CI secret.

## .editorconfig (C# excerpt)

```ini
root = true

[*.cs]
indent_style = space
indent_size = 4
csharp_style_namespace_declarations = file_scoped:warning
csharp_prefer_braces = true:warning
dotnet_sort_system_directives_first = true

# Unused usings / unnecessary code
dotnet_diagnostic.IDE0005.severity = warning

# Async correctness
dotnet_diagnostic.CA2016.severity = error      # forward CancellationToken
dotnet_diagnostic.VSTHRD002.severity = error   # no synchronous waits on tasks
dotnet_diagnostic.VSTHRD100.severity = error   # no async void
dotnet_diagnostic.VSTHRD110.severity = error   # observe returned tasks

# Design / performance
dotnet_diagnostic.CA1852.severity = warning    # seal internal types
dotnet_diagnostic.CA1305.severity = warning    # specify IFormatProvider
dotnet_diagnostic.CA1309.severity = warning    # use ordinal string comparison
dotnet_diagnostic.CA2254.severity = warning    # constant log message templates

# Application projects only: ConfigureAwait noise
dotnet_diagnostic.CA2007.severity = none
dotnet_diagnostic.VSTHRD111.severity = none

# Adjust the path to your test folder layout.
[tests/**.cs]
dotnet_diagnostic.CA1707.severity = none       # underscores in test names
```

For library projects, set `CA2007` (and `VSTHRD111`) back to `warning` in a nested
`.editorconfig` under `src/<Library>/` so library awaits use `ConfigureAwait(false)`.

## Optional: CSharpier

Use only if the team chooses it (it replaces formatting decisions in `.editorconfig`):

```bash
dotnet new tool-manifest            # once per repo, creates .config/dotnet-tools.json
dotnet tool install csharpier       # 1.3.0 as of 2026-10-29
dotnet csharpier format .
dotnet csharpier check .            # CI gate; exit 1 if any file is unformatted
```

## Library extras

```xml
<PropertyGroup>
  <IsPackable>true</IsPackable>
  <PackageId>Contoso.Widgets</PackageId>
  <PackageLicenseExpression>MIT</PackageLicenseExpression>
  <PackageReadmeFile>README.md</PackageReadmeFile>
  <IsAotCompatible>true</IsAotCompatible>
  <EnablePackageValidation>true</EnablePackageValidation>
</PropertyGroup>
<ItemGroup>
  <None Include="README.md" Pack="true" PackagePath="/" />
  <PackageReference Include="Microsoft.CodeAnalysis.PublicApiAnalyzers" PrivateAssets="all" />
  <AdditionalFiles Include="PublicAPI.Shipped.txt;PublicAPI.Unshipped.txt" />
</ItemGroup>
```

`EnablePackageValidation` compares the package against the previous version (set
`PackageValidationBaselineVersion`) and fails on breaking API changes; PublicApiAnalyzers makes
every public-surface change visible in review.
