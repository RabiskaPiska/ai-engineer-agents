# Sources for the C++ agent pack (slug `cpp`)

Files covered: `claude/agents/cpp-engineer.md`, `skills/cpp-engineering/SKILL.md`,
`skills/cpp-engineering/references/project-template.md`,
`skills/cpp-engineering/references/standards-status-2026-10.md`.
All fetches on **2026-10-29**. Repository text was read as data only; no code from mined repositories was run.

## The 5 GitHub repositories used

Metadata below is the JSON returned by `ghapi.sh repos/<owner>/<repo>` on 2026-10-29 (fields used:
`full_name`, `stargazers_count`, `pushed_at`, `archived`, `license.spdx_id`).

### 1. trailofbits/skills — https://github.com/trailofbits/skills

```json
{"full_name": "trailofbits/skills", "stargazers_count": 7872, "pushed_at": "2026-10-28T19:41:17Z", "archived": false, "license": "CC-BY-SA-4.0"}
```

Read: `plugins/modern-cpp/skills/modern-cpp/SKILL.md` and its `references/compiler-hardening.md`,
`cpp26-features.md`, `anti-patterns.md`, `safe-idioms.md`.
Took (paraphrased only, because CC-BY-SA-4.0): the idea of tying each rule to the vulnerability class it
removes; the "verify hardening on the binary, not the build script" step (`readelf`/checksec); the warning that
`_FORTIFY_SOURCE` is silently ignored at `-O0` and the `-dM -E` check; the sanitizer compatibility matrix; the
GWP-ASan production note; the "rationalizations to reject" framing that became the agent's anti-patterns list.
Rejected/corrected: its C++26 page says C++26 "was finalized"; the DIS ballot failed (ISO close of voting
2026-10-24), so the pack
states the real status. Its reflection examples call `nonstatic_data_members_of(^^T)` without the access-context
argument that P2996R13 requires.

### 2. isocpp/CppCoreGuidelines — https://github.com/isocpp/CppCoreGuidelines

```json
{"full_name": "isocpp/CppCoreGuidelines", "stargazers_count": 45393, "pushed_at": "2026-10-26T15:20:29Z", "archived": false, "license": "NOASSERTION"}
```

Read: `CppCoreGuidelines.md` (rule headings for P, I, F, C, R, ES, Per, CP, E, Con, T sections were extracted
and checked by ID). License is a Standard C++ Foundation license limited to personal or internal business use,
so the pack cites rule IDs and paraphrases; no guideline text is copied.
Took: the rule IDs attached to every engineering rule (R.1, R.3, R.11, R.20, R.21, R.23, R.30, I.11, F.16,
F.20, F.21, F.43, F.53, C.20, C.21, C.41, C.46, E.2, E.15, E.16, ES.20, ES.23, ES.48, ES.49, ES.100, ES.102,
Con.1, Con.5, T.10, T.11, CP.20, CP.21, CP.26, CP.42, CP.50 to CP.53, CP.100, CP.110, Per.4, Per.19).

### 3. cpp-best-practices/cmake_template — https://github.com/cpp-best-practices/cmake_template

```json
{"full_name": "cpp-best-practices/cmake_template", "stargazers_count": 1818, "pushed_at": "2026-08-17T11:06:39Z", "archived": false, "license": "Unlicense"}
```

Read: `cmake/CompilerWarnings.cmake`, `cmake/Hardening.cmake`, `cmake/Sanitizers.cmake`,
`cmake/StaticAnalyzers.cmake`, `.clang-tidy`, `.clang-format`, `CMakePresets.json`, `ProjectOptions.cmake`.
Took (Unlicense, adaptation allowed): the GCC/Clang warning set (`-Wshadow -Wnon-virtual-dtor -Wold-style-cast
-Woverloaded-virtual -Wnull-dereference -Wformat=2 -Wimplicit-fallthrough`, GCC extras), MSVC `/W4 /permissive-`,
the warnings-on-an-INTERFACE-target pattern, the MSVC hardening flags (`/sdl /guard:cf /DYNAMICBASE`,
`/NXCOMPAT /CETCOMPAT`), and the `-U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3` ordering. Its `.clang-tidy` enables
`*` minus a list; the pack instead starts from `-*` and enables named families, which kept the tested run
readable.

### 4. github/awesome-copilot — https://github.com/github/awesome-copilot

```json
{"full_name": "github/awesome-copilot", "stargazers_count": 40541, "pushed_at": "2026-10-29T00:07:04Z", "archived": false, "license": "MIT"}
```

Read: `agents/expert-cpp-software-engineer.agent.md`, `instructions/cpp-language-service-tools.instructions.md`,
`instructions/cmake-vcpkg.instructions.md`.
Took: the rule that symbol references and call hierarchies come from a C++ language service, not text search,
before any signature change (overloads, template instantiations, macros); this became the `cpp-lsp` MCP usage
rule. From the vcpkg instructions: manifest mode only (no `vcpkg install <pkg>` advice) and cache variables in
`CMakePresets.json`. From the agent: legacy-code seams and characterization tests before refactoring.

### 5. wshobson/agents — https://github.com/wshobson/agents

```json
{"full_name": "wshobson/agents", "stargazers_count": 41969, "pushed_at": "2026-10-26T01:08:14Z", "archived": false, "license": "MIT"}
```

Read: `plugins/systems-programming/agents/cpp-pro.md`,
`plugins/systems-programming/skills/memory-safety-patterns/SKILL.md`.
Took: the output expectations "sanitizer-clean output" and "benchmarks with Google Benchmark" as explicit
deliverables, and the memory-bug-category table that shaped the OWN rules. Noted gap: the agent lists C++
features but no versions, gates or commands, which is what this pack adds.

## MCP servers declared in the agent (verified 2026-10-29)

| Server | Source | Evidence |
|---|---|---|
| `github` (by name) | https://github.com/github/github-mcp-server | `{"full_name": "github/github-mcp-server", "stargazers_count": 34054, "pushed_at": "2026-10-29T05:42:25Z", "license": "MIT"}`; referenced by name as the spec requires. |
| `context7` (http) | https://github.com/upstash/context7 | `{"stargazers_count": 63882, "pushed_at": "2026-10-28T20:26:24Z", "license": "MIT"}`. README: "use the Context7 server URL `https://mcp.context7.com/mcp` ... pass your API key via the `Authorization: Bearer YOUR_API_KEY` header"; "API Key Recommended ... for higher rate limits". |
| `lldb` (stdio, `lldb-mcp`) | https://github.com/llvm/llvm-project (`lldb/tools/lldb-mcp`, docs `lldb/docs/use/mcp.md`) | `{"full_name": "llvm/llvm-project", "stargazers_count": 41243, "pushed_at": "2026-10-29T09:43:48Z", "license": "NOASSERTION"}` (Apache-2.0 WITH LLVM-exception per the project). `contents/lldb/tools/lldb-mcp` exists at tags `llvmorg-22.1.0`, `llvmorg-23.1.0`, `llvmorg-23.1.4`; absent at `llvmorg-21.1.0`. The 23.1.4 doc: "LLDB ships with `lldb-mcp`, a small helper that bridges stdio to LLDB's MCP server socket ... If no server is running, it will launch `lldb` in the background"; one tool `lldb_command`. Install = install LLDB 22+ (distro or apt.llvm.org packages may suffix the binary with the version; adjust `command`); this install line and the caveat are now also in the agent's "MCP and skills usage" prerequisites. |
| `cpp-lsp` (stdio, `mcp-language-server` + clangd) | https://github.com/isaacphi/mcp-language-server | `{"full_name": "isaacphi/mcp-language-server", "stargazers_count": 1611, "pushed_at": "2026-03-01T23:27:09Z", "license": "BSD-3-Clause"}`; latest release v0.1.1 (2025-05-16). Install from README: `go install github.com/isaacphi/mcp-language-server@latest`; clangd config `--workspace <dir> --lsp <clangd> -- --compile-commands-dir=<dir>`. `main.go` resolves `--workspace` with `filepath.Abs`, so `.` means the session's working directory. clangd itself searches parent directories and `build/` subdirectories for `compile_commands.json` (clangd.llvm.org/installation), so the agent omits `--compile-commands-dir`. Re-checked 2026-10-29 with `ghapi.sh repos/isaacphi/mcp-language-server/releases`: v0.1.1 (2025-05-16) and v0.1.0 (2025-05-02) are the only releases; the agent states this maintenance status next to the install command. Tools: `definition`, `references`, `diagnostics`, `hover`, `rename_symbol`, `edit_file`. |

Considered and not declared: `felipeerias/clangd-mcp-server` (last push 2025-12-03, not 2026),
`Ipiano/gdb-mcp` (MIT, pushed 2026-03-11, 52 stars; the official LLDB server covers debugging with an upstream
maintainer), Compiler Explorer MCP servers (`Benestar/godbolt-mcp` last pushed 2025-07-22; the 2026 ones have
fewer than 20 stars).

## Official version sources (fetched 2026-10-29)

| Fact | Source |
|---|---|
| GCC 16.2 (2026-08-07), 16.1 (2026-04-30); "Supported Releases" = 16.2, 15.3, 14.4 | https://gcc.gnu.org/ (news list and "Supported Releases" box) |
| GCC 13 closed: "This release series is no longer supported", 13.5 on 2026-09-11 | https://gcc.gnu.org/gcc-13/ |
| GCC 16 default `gnu++20`, C++26 features, libstdc++ ABI changes and C++26 library list | https://gcc.gnu.org/gcc-16/changes.html |
| GCC 15 assertions default at `-O0`, `std` modules | https://gcc.gnu.org/gcc-15/changes.html |
| GCC 14 `-fhardened`, `std::print` | https://gcc.gnu.org/gcc-14/changes.html |
| LLVM 23.1.0 (2026-08-25) ... 23.1.4 (2026-10-20) | `ghapi.sh repos/llvm/llvm-project/releases` |
| Clang 23 notes (lifetime safety, expansion statements, `-std=c++2d`, UBSan) | https://releases.llvm.org/23.1.0/tools/clang/docs/ReleaseNotes.html |
| libc++ 23 implemented papers | https://releases.llvm.org/23.1.0/projects/libcxx/docs/ReleaseNotes.html |
| LLDB MCP | https://lldb.llvm.org/use/mcp.html and `lldb/docs/use/mcp.md` at `llvmorg-23.1.4` |
| MSVC 14.50 LTS / 14.51 default / lifecycle | https://learn.microsoft.com/en-us/cpp/overview/compiler-versions?view=msvc-170 , https://learn.microsoft.com/en-us/cpp/overview/what-s-new-for-msvc?view=msvc-170 |
| VS 2026 18.11.2 (2026-10-25) | https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-history |
| MSVC 14.52 RC, `/std:c++23`, `/Zc:cmath` (2026-10-15) | https://devblogs.microsoft.com/cppblog/msvc-build-tools-version-14-52-release-candidate-now-available/ |
| C++26 completed at Croydon (2026-03-28) | https://herbsutter.com/2026/03/29/c26-is-done-trip-report-march-2026-iso-c-standards-meeting-london-croydon-uk |
| ISO/IEC DIS 14882 stages (40.20 ballot initiated 2026-07-31, 40.60 close of voting 2026-10-24; re-read 2026-10-29 through the parallel-search fetch tool) | https://www.iso.org/standard/91179.html |
| DIS ballot result (12/20 for, 9/22 against) | https://train-it.eu/blog/cpp26-contracts-the-ballot-result (Mateusz Pusz, 2026-10-25, quoting "Robert Seacord, LinkedIn, 24 October 2026 ... Disapproved"; the article itself says "closed on 23 October", one day before ISO's stage date, which the pack uses) |
| P4388R0 "Ship C++26", P4433R0 | https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4388r0.pdf , https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4433r0.pdf |
| Reflection API with `access_context` | https://isocpp.org/files/papers/P2996R13.html , https://en.cppreference.com/cpp/header/meta |
| CMake 4.4.5 (2026-10-27), 4.5.0-rc2 | `ghapi.sh repos/Kitware/CMake/releases` |
| CMake 4.4 notes, `CMAKE_CXX_MODULE_STD` still experimental; "C++ 20 named modules are now supported with clang-cl, except with the Visual Studio Generators (i.e., the ClangCl toolset)" | https://cmake.org/cmake/help/v4.4/release/4.4.html , https://cmake.org/cmake/help/v4.4/variable/CMAKE_CXX_MODULE_STD.html |
| Ninja 1.13.2, Meson 1.12.1, Conan 2.34.0, vcpkg 2026.10.16, GoogleTest 1.18.0, Catch2 3.16.1, doctest 2.5.3, Google Benchmark 1.10.0, IWYU 0.27, ccache 4.14.2, gcovr 8.8, lcov 2.6, Mull 0.35.0, fmt 12.2.0, Abseil 20260817.0, CPM.cmake 0.43.2, Bazel 9.3.1 | `ghapi.sh repos/<owner>/<repo>/releases` for each upstream project (release `published_at`) |
| Cppcheck 2.22.0 (2026-09-19), repo moved to `cppcheck-opensource/cppcheck` | `ghapi.sh repositories/143131` and `/releases` |
| Valgrind 3.28.0 (2026-10-23) | https://valgrind.org/ |
| GDB 18.1 (2026-09-25) | https://www.sourceware.org/gdb/ |
| OpenSSF hardening flag set (guide dated 2026-08-20), including "using GCC and only left-to-right writing in source code: -Wbidi-chars=any" (GCC 12.0.0) | https://best.openssf.org/Compiler-Hardening-Guides/Compiler-Options-Hardening-Guide-for-C-and-C++.html |
| `std::function_ref` is experimental C++26 library in GCC 16 ("Improved experimental support for C++26 ... std::copyable_function and std::function_ref") | https://gcc.gnu.org/gcc-16/changes.html |
| clang-tidy check semantics: `concurrency-mt-unsafe` (list of thread-unsafe libc functions), `cert-err58-cpp` (alias of `bugprone-throwing-static-initialization`, CERT ERR58-CPP "exceptions thrown before main()"), `bugprone-exception-escape` (destructors, moves, `main`, `swap`, `noexcept` functions, `FunctionsThatShouldNotThrow`) | https://clang.llvm.org/extra/clang-tidy/checks/concurrency/mt-unsafe.html , https://clang.llvm.org/extra/clang-tidy/checks/cert/err58-cpp.html , https://clang.llvm.org/extra/clang-tidy/checks/bugprone/exception-escape.html |
| Google Benchmark `tools/compare.py` (U test, `--alpha` default 0.05, `UTEST_OPTIMAL_REPETITIONS = 9`) at tag v1.10.0 | `ghapi.sh repos/google/benchmark/contents/tools/compare.py?ref=v1.10.0` and the source of that tag |
| Conan `audit` (2.14+, free token from audit.conan.io, `CONAN_AUDIT_PROVIDER_TOKEN_CONANCENTER`, default fails on CVSS >= 9.0) and the CycloneDX SBOM hook | https://docs.conan.io/2/devops/audit.html , https://docs.conan.io/2/reference/commands/audit.html , https://docs.conan.io/2/security/sboms.html |
| vcpkg per-port SPDX SBOM `<installed_dir>/<triplet>/share/<port>/vcpkg.spdx.json`, no CycloneDX out of the box | https://learn.microsoft.com/en-us/vcpkg/reference/software-bill-of-materials |
| OSV-Scanner reads `conan.lock` | https://google.github.io/osv-scanner/supported-languages-and-lockfiles/ |
| GitHub Actions full history for merge-base ("Set `fetch-depth: 0` to fetch all history for all branches and tags") | https://github.com/actions/checkout |
| clangd compile-database lookup | https://clangd.llvm.org/installation |
| Claude Code subagent frontmatter and inline MCP schema | https://code.claude.com/docs/en/sub-agents.md , https://code.claude.com/docs/en/mcp.md |

## Executed evidence (author box, 2026-10-29)

Toolchain on the box: GCC 13.3.0, CMake 3.28.3, GDB 15.1; clang-format 23.1.3, clang-tidy 23.1.4 and gcovr 8.8
installed into a scratch virtualenv from PyPI. Results:

- Sample project (files in `references/project-template.md`): `cmake --workflow --preset ci` (ASan+UBSan) ->
  `100% tests passed`; TSan preset under `setarch -R` -> pass; coverage preset + gcovr -> 94% lines, exit 0;
  release preset builds; clang-format `--dry-run --Werror` exit 0; clang-tidy with the shipped `.clang-tidy`
  exit 0 after fixes (the pre-fix findings are quoted in the skill).
- Negative controls: ASan heap-buffer-overflow (exit 134); `-Werror=sign-conversion` (exit 1);
  `_GLIBCXX_ASSERTIONS` at `-O2` (exit 134); TSan data race (exit 66) and the `unexpected memory mapping` abort
  without `setarch -R`; `_FORTIFY_SOURCE=3` overflow abort (exit 134); `readelf` shows `GNU_RELRO`, `BIND_NOW`,
  `FLAGS_1: NOW PIE`, `__stack_chk_fail`, `__strcpy_chk` for the OpenSSF flag set (minus GCC 15+ only flags).
- Every clang-tidy check name in the skill was checked against `clang-tidy --list-checks -checks='*'` (23.1.4);
  one invalid name (`hicpp-explicit-conversions`) was found and removed.

Fix round (2026-10-29, after the review in `_work/fixes/cpp.md`; toolchain additionally: Ninja 1.13.2 and Conan
2.34.0 from PyPI into the scratch virtualenv, numpy 2.5.4 + scipy 1.18.1 for `compare.py`, OSV-Scanner 2.5.0):
- The template in `references/project-template.md` was materialized from the Markdown into fresh directories and
  every gate re-run there: format, dev tests (4), `run-clang-tidy.py`, ASan+UBSan workflow, TSan, coverage
  (100% lines of `src/`), release tests and gate 9 (outputs pasted in its section 6).
- Gate 9 negative control: release built with `-DGATE_HARDENING=OFF` -> `FAIL: -D_FORTIFY_SOURCE=3 in 0 of 3
  compile commands` while `readelf` still shows `GNU_RELRO`, `BIND_NOW`, `NOW PIE`, `__stack_chk_fail`.
- Gate 3a: the old command exits 128 (`fatal: bad revision 'origin/HEAD...'`) in a repo with no remote and
  exits 0 on a header-only violation even with a valid base; the new command reports
  `src/parse.hpp:17:35: error: C-style casts are discouraged` (exit 1), passes on a clean tree, and works with a
  real `origin/main` merge base. The old `HeaderFilterRegex: '^(src|include|tests)/'` matched no header
  (absolute paths); fixed to `'/(src|include|tests)/'`.
- Gate 8: `compare.py` on a `reserve()` change -> `BM_fill_pvalue 0.0002`, median -25%; same binary twice ->
  `BM_fill_pvalue 0.1859` with a -11% median (noise); `--benchmark_report_aggregates_only` JSON -> no U-test row.
- GoogleTest 1.18.0 via Conan 2.34.0: `gtest_discover_tests` registers 5 tests, `100% tests passed, 0 tests
  failed out of 9`; a deliberately wrong expectation fails with `parse_gtest.cpp:13: Failure`. A Debug consumer
  against Release-only Conan packages fails with `fatal error: gtest/gtest.h: No such file or directory`.
- Supply chain: the Conan CycloneDX hook writes `sbom.cdx.json` (CycloneDX 1.6, `gtest 1.18.0`,
  `BSD-3-Clause`); `conan lock create .` writes `conan.lock`; `conan audit scan .` stops at `ERROR: Missing
  authentication token`; OSV-Scanner on a `conan.lock` pinning `zlib/1.2.11` reports `No issues found`, and
  `api.osv.dev` returns `{}` for `zlib` 1.2.11 in the `ConanCenter` ecosystem although CVE-2018-25032 ("zlib
  before 1.2.12") applies.
- `concurrency-mt-unsafe` flagged `strtok`, `localtime`, `gmtime`, `rand`, `strerror`, `setenv` and `getenv` in a
  test file (CON-5).

## Unverified items

- `[UNVERIFIED]` Reflection idiom with `std::define_static_array(... access_context::current())`: taken from
  cppreference `<meta>` and P2996R13; not compiled (no GCC 16 on the author box).
- `[UNVERIFIED]` vcpkg commands in `references/project-template.md` section 7 (not run). The Conan commands
  were run. Package availability is resolved: `gtest` 1.18.0 and `fmt` 12.2.0 are current in
  `microsoft/vcpkg` `ports/*/vcpkg.json` and ConanCenter `recipes/*/config.yml` (GitHub API, 2026-10-29), and
  Conan resolved `gtest/1.18.0` from ConanCenter.
- `[UNVERIFIED]` `conan audit scan` with a real token, and any vulnerability audit for vcpkg graphs.
- `[UNVERIFIED]` Cppcheck, IWYU, Valgrind, Mull, LLDB and `mcp-language-server` were not installed on the author
  box; their commands come from upstream docs, not a local run.
- `[UNVERIFIED]` Whether Claude Code expands `${VAR}` inside agent-frontmatter MCP args; the agent avoids
  relying on it (uses `.` for the workspace).
- `-fzero-init-padding-bits=all` (GCC 15+) and `-fhardened` (GCC 14+) are documented upstream but were not
  exercised on GCC 13.

## Self-checks

Run on 2026-10-29 with `selfcheck.py` (PyYAML `yaml.safe_load` on each frontmatter, allowed-field check,
literal heading check in order, line counts, ALL-CAPS scan) and `linkcheck.sh` (GitHub links through
`ghapi.sh repos/<owner>/<repo>`, the Context7 endpoint through an MCP `initialize` POST, other links with
`curl -L`). Final run after the fix round:

```text
yaml.safe_load(claude/agents/cpp-engineer.md): OK keys=['description', 'mcpServers', 'model', 'name', 'skills']
yaml.safe_load(skills/cpp-engineering/SKILL.md): OK keys=['description', 'name']
agent fields all allowed: True; tools omitted: True; name=cpp-engineer; model=inherit; skills=['cpp-engineering']
agent mcpServers: ["github", {"context7": {"type": "http", "url": "https://mcp.context7.com/mcp"}}, {"lldb": {"type": "stdio", "command": "lldb-mcp"}}, {"cpp-lsp": {"type": "stdio", "command": "mcp-language-server", "args": ["--workspace", ".", "--lsp", "clangd", "--", "--background-index", "--clang-tidy"]}}]
required headings present in order: True; missing=[]
skill name matches dir: True; agent skills ref ok: True
lines claude/agents/cpp-engineer.md: 376
lines skills/cpp-engineering/SKILL.md: 317
ALL-CAPS imperative words in agent+skill: 0
```

```text
200  https://audit.conan.io/register
200  https://best.openssf.org/Compiler-Hardening-Guides/Compiler-Options-Hardening-Guide-for-C-and-C++.html
200  https://clang.llvm.org/extra/clang-tidy/checks/bugprone/exception-escape.html
200  https://clang.llvm.org/extra/clang-tidy/checks/cert/err58-cpp.html
200  https://clang.llvm.org/extra/clang-tidy/checks/concurrency/mt-unsafe.html
200  https://clangd.llvm.org/installation
200  https://cmake.org/cmake/help/v4.4/release/4.4.html
200  https://cmake.org/cmake/help/v4.4/variable/CMAKE_CXX_MODULE_STD.html
200  https://code.claude.com/docs/en/mcp.md
200  https://code.claude.com/docs/en/sub-agents.md
200  https://devblogs.microsoft.com/cppblog/msvc-build-tools-version-14-52-release-candidate-now-available/
200  https://docs.conan.io/2/devops/audit.html
200  https://docs.conan.io/2/reference/commands/audit.html
200  https://docs.conan.io/2/security/sboms.html
200  https://en.cppreference.com/cpp/header/meta
200  https://gcc.gnu.org/
200  https://gcc.gnu.org/gcc-13/
200  https://gcc.gnu.org/gcc-14/changes.html
200  https://gcc.gnu.org/gcc-15/changes.html
200  https://gcc.gnu.org/gcc-16/changes.html
200 ghapi actions/checkout  https://github.com/actions/checkout
200 ghapi cpp-best-practices/cmake_template  https://github.com/cpp-best-practices/cmake_template
200 ghapi github/awesome-copilot  https://github.com/github/awesome-copilot
200 ghapi github/github-mcp-server  https://github.com/github/github-mcp-server
200 ghapi isaacphi/mcp-language-server  https://github.com/isaacphi/mcp-language-server
200 ghapi isocpp/CppCoreGuidelines  https://github.com/isocpp/CppCoreGuidelines
200 ghapi llvm/llvm-project  https://github.com/llvm/llvm-project
200 ghapi trailofbits/skills  https://github.com/trailofbits/skills
200 ghapi upstash/context7  https://github.com/upstash/context7
200 ghapi wshobson/agents  https://github.com/wshobson/agents
200  https://google.github.io/osv-scanner/supported-languages-and-lockfiles/
200  https://herbsutter.com/2026/03/29/c26-is-done-trip-report-march-2026-iso-c-standards-meeting-london-croydon-uk
200  https://isocpp.org/files/papers/P2996R13.html
200  https://learn.microsoft.com/en-us/cpp/overview/compiler-versions?view=msvc-170
200  https://learn.microsoft.com/en-us/cpp/overview/what-s-new-for-msvc?view=msvc-170
200  https://learn.microsoft.com/en-us/vcpkg/reference/software-bill-of-materials
200  https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-history
200  https://lldb.llvm.org/use/mcp.html
200 mcp-initialize  https://mcp.context7.com/mcp
200  https://releases.llvm.org/23.1.0/projects/libcxx/docs/ReleaseNotes.html
200  https://releases.llvm.org/23.1.0/tools/clang/docs/ReleaseNotes.html
200  https://train-it.eu/blog/cpp26-contracts-the-ballot-result
200  https://valgrind.org/
403  https://www.iso.org/standard/91179.html
200  https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4388r0.pdf
200  https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4433r0.pdf
200  https://www.sourceware.org/gdb/
```

Link-check notes: 47 URLs checked, 46 return 200. `https://www.iso.org/standard/91179.html` returns 403 to
curl (bot protection); its content (stages 40.20 on 2026-07-31 and 40.60 on 2026-10-24) was read through
the parallel-search fetch tool on 2026-10-29. The releases.llvm.org libc++ page carries the generic
"in-progress notes for the upcoming 23.0.0" banner but lists the 23.x implemented papers quoted here.
