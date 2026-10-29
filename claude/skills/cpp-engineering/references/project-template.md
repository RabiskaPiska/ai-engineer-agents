# Project template (built and run 2026-10-29)

Every file in sections 1 to 5 and the Conan + GoogleTest variant in section 7 was materialized from this
document into an empty directory and run on the author box (GCC 13.3, CMake 3.28.3, Ninja 1.13.2,
clang-format 23.1.3, clang-tidy 23.1.4, gcovr 8.8, Conan 2.34.0, Linux 6.8 x86_64). The files are pasted
verbatim from that run. The vcpkg wiring in section 7 was not run and is marked accordingly.

Layout:

```text
CMakeLists.txt  CMakePresets.json  .clang-format  .clang-tidy  .clangd  conanfile.txt
src/parse.hpp   src/parse.cpp      src/main.cpp
tests/parse_test.cpp               tests/parse_gtest.cpp
```

Adapting it: rename `gate`/`parse`/`app`, keep the `Ninja` generator in the `base` preset (or delete that line
to use the platform default; gate 9's link check then reads `CMakeFiles/app.dir/link.txt` instead of
`ninja -t commands`), and raise `cmake_minimum_required` to the oldest CMake your CI uses (4.4.5 is current).
`tests/parse_test.cpp` is a dependency-free smoke test; the GoogleTest suite in section 7 is the one to grow.

## 1. CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.25)
project(gate LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
option(GATE_WERROR "Treat warnings as errors" ON)
option(GATE_HARDENING "OpenSSF hardening flags and standard-library assertions (UB-3, UB-4)" ON)
option(GATE_GTEST "Build the GoogleTest suite (GTest from Conan or vcpkg)" OFF)

add_library(gate_warnings INTERFACE)
if(MSVC)
  target_compile_options(gate_warnings INTERFACE /W4 /permissive- $<$<BOOL:${GATE_WERROR}>:/WX>)
else()
  target_compile_options(gate_warnings INTERFACE -Wall -Wextra -Wpedantic -Wshadow -Wconversion
    -Wsign-conversion -Wnon-virtual-dtor -Wold-style-cast -Woverloaded-virtual -Wnull-dereference
    -Wformat=2 -Wimplicit-fallthrough -Werror=format-security
    $<$<CXX_COMPILER_ID:GNU>:-Wtrampolines> $<$<CXX_COMPILER_ID:GNU>:-Wbidi-chars=any>
    $<$<BOOL:${GATE_WERROR}>:-Werror>)
endif()

# OpenSSF Compiler Options Hardening Guide for C and C++ (2026-08-20); see SKILL.md section 3.
add_library(gate_hardening INTERFACE)
if(GATE_HARDENING)
  set(CMAKE_POSITION_INDEPENDENT_CODE ON)
  include(CheckPIESupported)
  check_pie_supported()
  if(MSVC)
    target_compile_options(gate_hardening INTERFACE /sdl /guard:cf)
    target_link_options(gate_hardening INTERFACE /guard:cf /DYNAMICBASE /NXCOMPAT /CETCOMPAT)
  else()
    target_compile_options(gate_hardening INTERFACE
      "$<$<NOT:$<CONFIG:Debug>>:-U_FORTIFY_SOURCE;-D_FORTIFY_SOURCE=3>"
      -D_GLIBCXX_ASSERTIONS -D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_FAST
      -fstrict-flex-arrays=3 -fstack-clash-protection -fstack-protector-strong
      -fno-delete-null-pointer-checks -fno-strict-overflow -fno-strict-aliasing
      -ftrivial-auto-var-init=zero)
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64")
      target_compile_options(gate_hardening INTERFACE -fcf-protection=full -fzero-call-used-regs=used-gpr)
    elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64|arm64")
      target_compile_options(gate_hardening INTERFACE -mbranch-protection=standard
        -fzero-call-used-regs=used-gpr)
    endif()
    if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" AND CMAKE_CXX_COMPILER_VERSION VERSION_GREATER_EQUAL 15)
      target_compile_options(gate_hardening INTERFACE -fzero-init-padding-bits=all)
    endif()
    if(NOT APPLE)
      target_link_options(gate_hardening INTERFACE -Wl,-z,noexecstack -Wl,-z,relro -Wl,-z,now
        -Wl,--as-needed -Wl,--no-copy-dt-needed-entries)
    endif()
  endif()
endif()

add_library(parse src/parse.cpp)
target_include_directories(parse PUBLIC src)
target_link_libraries(parse PRIVATE gate_warnings gate_hardening)
add_executable(app src/main.cpp)
target_link_libraries(app PRIVATE parse gate_warnings gate_hardening)

enable_testing()
add_executable(parse_test tests/parse_test.cpp)
target_link_libraries(parse_test PRIVATE parse gate_warnings gate_hardening)
add_test(NAME parse_test COMMAND parse_test)
add_test(NAME app_sums COMMAND app 1 2 3)
set_tests_properties(app_sums PROPERTIES PASS_REGULAR_EXPRESSION "^6\n$")
add_test(NAME app_rejects_junk COMMAND app 4x)
add_test(NAME app_rejects_overflow COMMAND app 4000000000 400000000)
set_tests_properties(app_rejects_junk app_rejects_overflow PROPERTIES WILL_FAIL TRUE)

if(GATE_GTEST)
  find_package(GTest CONFIG REQUIRED)
  include(GoogleTest)
  add_executable(parse_gtest tests/parse_gtest.cpp)
  target_link_libraries(parse_gtest PRIVATE parse gate_warnings gate_hardening GTest::gtest_main)
  gtest_discover_tests(parse_gtest)
endif()
```

Notes:
- Warnings and hardening live on `INTERFACE` targets linked `PRIVATE`, so they apply to your code and never
  leak to consumers. `GATE_WERROR` is ON for development and OFF in the `release` preset, following BLD-6.
- `gate_hardening` carries the OpenSSF set from SKILL.md section 3 plus standard-library assertions (UB-3,
  UB-4). It is ON by default and in `release`, OFF in `dev`/`asan`/`tsan`/`cov`: `_FORTIFY_SOURCE` overlaps
  with sanitizer interceptors, and `-ftrivial-auto-var-init=zero` hides the uninitialized reads that MSan and
  `-Wmaybe-uninitialized` should find. `_FORTIFY_SOURCE` is skipped in Debug because it needs optimization.
- Hardening is set in CMake, not left to the compiler's defaults. Ubuntu's GCC enables `-fPIE`,
  `-fstack-protector-strong` and `-fstack-clash-protection` and links with `-z relro -z now` on its own, so
  a `readelf` check passes there even when the project sets nothing; on another distro, on Clang, or on a
  cross toolchain it does not. Gate 9 therefore checks the compile and link commands as well as the binary.
- `-Wtrampolines` and `-Wbidi-chars=any` are GCC-only. Clang-based tools reading a GCC compile database
  report them as unknown, which is why the clang-tidy gates pass `--extra-arg=-Wno-unknown-warning-option`.
- The three `app_*` tests run the executable itself, so `src/main.cpp` is covered and gate 9 has a real
  binary to inspect.

## 2. CMakePresets.json

```json
{
  "version": 6,
  "cmakeMinimumRequired": { "major": 3, "minor": 25, "patch": 0 },
  "configurePresets": [
    {
      "name": "base", "hidden": true, "generator": "Ninja",
      "binaryDir": "${sourceDir}/out/${presetName}",
      "cacheVariables": { "CMAKE_EXPORT_COMPILE_COMMANDS": "ON", "CMAKE_CXX_STANDARD": "23" }
    },
    { "name": "dev", "inherits": "base",
      "cacheVariables": { "CMAKE_BUILD_TYPE": "Debug", "CMAKE_CXX_FLAGS": "-D_GLIBCXX_ASSERTIONS",
                          "GATE_HARDENING": "OFF" } },
    { "name": "asan", "inherits": "base",
      "cacheVariables": { "CMAKE_BUILD_TYPE": "RelWithDebInfo", "GATE_HARDENING": "OFF",
        "CMAKE_CXX_FLAGS": "-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -D_GLIBCXX_ASSERTIONS" } },
    { "name": "tsan", "inherits": "base",
      "cacheVariables": { "CMAKE_BUILD_TYPE": "RelWithDebInfo", "GATE_HARDENING": "OFF",
                          "CMAKE_CXX_FLAGS": "-fsanitize=thread -fno-omit-frame-pointer" } },
    { "name": "cov", "inherits": "base",
      "cacheVariables": { "CMAKE_BUILD_TYPE": "Debug", "GATE_HARDENING": "OFF", "CMAKE_CXX_FLAGS": "--coverage" } },
    { "name": "release", "inherits": "base",
      "cacheVariables": { "CMAKE_BUILD_TYPE": "Release", "CMAKE_INTERPROCEDURAL_OPTIMIZATION": "ON",
                          "GATE_WERROR": "OFF", "GATE_HARDENING": "ON" } },
    { "name": "gtest", "inherits": "dev",
      "toolchainFile": "${sourceDir}/out/conan/conan_toolchain.cmake",
      "cacheVariables": { "GATE_GTEST": "ON" } }
  ],
  "buildPresets": [
    { "name": "dev", "configurePreset": "dev" }, { "name": "asan", "configurePreset": "asan" },
    { "name": "tsan", "configurePreset": "tsan" }, { "name": "cov", "configurePreset": "cov" },
    { "name": "release", "configurePreset": "release" }, { "name": "gtest", "configurePreset": "gtest" }
  ],
  "testPresets": [
    { "name": "base", "hidden": true, "output": { "outputOnFailure": true }, "execution": { "noTestsAction": "error" } },
    { "name": "dev", "inherits": "base", "configurePreset": "dev" },
    { "name": "cov", "inherits": "base", "configurePreset": "cov" },
    { "name": "gtest", "inherits": "base", "configurePreset": "gtest" },
    { "name": "asan", "inherits": "base", "configurePreset": "asan",
      "environment": { "ASAN_OPTIONS": "detect_leaks=1:abort_on_error=1:detect_stack_use_after_return=1",
                       "UBSAN_OPTIONS": "print_stacktrace=1:halt_on_error=1" } },
    { "name": "tsan", "inherits": "base", "configurePreset": "tsan",
      "environment": { "TSAN_OPTIONS": "halt_on_error=1:second_deadlock_stack=1" } }
  ],
  "workflowPresets": [
    { "name": "ci", "steps": [
      { "type": "configure", "name": "asan" }, { "type": "build", "name": "asan" }, { "type": "test", "name": "asan" } ] }
  ]
}
```

`version 6` is needed for workflow presets (CMake 3.25+). `noTestsAction: error` makes `ctest` fail when no
tests were registered, which otherwise reports success. Sanitizer flags go in `CMAKE_CXX_FLAGS` from presets so
that every target, including tests, is instrumented consistently. The `gtest` preset expects
`out/conan/conan_toolchain.cmake` from the `conan install` in section 7.

For clangd (and the `cpp-lsp` MCP server), which only searches parent directories and their `build/`
subdirectories for `compile_commands.json`, add a `.clangd` file at the repo root:

```yaml
CompileFlags:
  CompilationDatabase: out/dev
```

## 3. .clang-format

```yaml
---
BasedOnStyle: Google
ColumnLimit: 110
IncludeBlocks: Regroup
DerivePointerAlignment: false
PointerAlignment: Left
AllowShortIfStatementsOnASingleLine: WithoutElse
InsertBraces: false
```

## 4. .clang-tidy

```yaml
---
Checks: >
  -*,
  bugprone-*,
  cert-*,
  clang-analyzer-*,
  concurrency-*,
  cppcoreguidelines-*,
  misc-*,
  modernize-*,
  performance-*,
  portability-*,
  readability-*,
  -bugprone-easily-swappable-parameters,
  -cppcoreguidelines-avoid-magic-numbers,
  -readability-magic-numbers,
  -misc-include-cleaner,
  -modernize-use-trailing-return-type,
  -readability-identifier-length,
  -cppcoreguidelines-pro-bounds-pointer-arithmetic,
  -portability-avoid-pragma-once
WarningsAsErrors: '*'
HeaderFilterRegex: '/(src|include|tests)/'
FormatStyle: file
CheckOptions:
  - key: readability-function-cognitive-complexity.Threshold
    value: '25'
  - key: misc-non-private-member-variables-in-classes.IgnoreClassesWithAllMemberVariablesBeingPublic
    value: 'true'
```

Disabled checks and why: `bugprone-easily-swappable-parameters` and the magic-number checks are noisy on
ordinary code; `misc-include-cleaner` is replaced by IWYU where wanted; `readability-identifier-length` and
`modernize-use-trailing-return-type` are style preferences; pointer arithmetic is allowed because the code
under test calls `std::from_chars(first, last, ...)`; `portability-avoid-pragma-once` contradicts TYP-8, which
allows `#pragma once`. Every other enabled finding is an error.

`HeaderFilterRegex` is matched against the header path as the compiler sees it, which is absolute when CMake
passes `-I/abs/path/src`. An anchored pattern such as `'^(src|include|tests)/'` therefore matches nothing and
silently drops every diagnostic in your headers; this was measured on this template (a C-style cast added to
`parse.hpp` was not reported through `parse.cpp` until the pattern was unanchored). Third-party headers stay
out because CMake passes imported targets' include directories as `-isystem`.

## 5. Source

```cpp
// src/parse.hpp
#pragma once
#include <cstdint>
#include <expected>
#include <span>
#include <string_view>

namespace gate {
enum class ParseError : std::uint8_t { empty, not_a_number, overflow };

// Parses a non-negative decimal integer. Never throws.
[[nodiscard]] std::expected<std::uint32_t, ParseError> parse_u32(std::string_view text) noexcept;

// Sums a span; returns overflow instead of wrapping.
[[nodiscard]] std::expected<std::uint32_t, ParseError> checked_sum(
    std::span<const std::uint32_t> values) noexcept;
}  // namespace gate

// src/parse.cpp
#include "parse.hpp"

#include <charconv>
#include <limits>
#include <system_error>

namespace gate {
std::expected<std::uint32_t, ParseError> parse_u32(std::string_view text) noexcept {
  if (text.empty()) {
    return std::unexpected(ParseError::empty);
  }
  std::uint32_t value{};
  const auto* first = text.data();
  const auto* last = first + text.size();
  const auto [ptr, ec] = std::from_chars(first, last, value);
  if (ec == std::errc::result_out_of_range) {
    return std::unexpected(ParseError::overflow);
  }
  if (ec != std::errc{} || ptr != last) {
    return std::unexpected(ParseError::not_a_number);
  }
  return value;
}

std::expected<std::uint32_t, ParseError> checked_sum(std::span<const std::uint32_t> values) noexcept {
  std::uint32_t total{};
  for (const auto v : values) {
    if (v > std::numeric_limits<std::uint32_t>::max() - total) {
      return std::unexpected(ParseError::overflow);
    }
    total += v;
  }
  return total;
}
}  // namespace gate

// src/main.cpp
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <span>
#include <vector>

#include "parse.hpp"

int main(int argc, char** argv) {
  const std::span<char*> args(argv, static_cast<std::size_t>(argc));
  std::vector<std::uint32_t> values;
  values.reserve(args.size());
  for (const char* arg : args.subspan(1)) {
    const auto value = gate::parse_u32(arg);
    if (!value.has_value()) {
      std::cerr << "not a u32: " << arg << '\n';
      return EXIT_FAILURE;
    }
    values.push_back(*value);
  }
  const auto sum = gate::checked_sum(values);
  if (!sum.has_value()) {
    std::cerr << "sum overflows u32\n";
    return EXIT_FAILURE;
  }
  std::cout << *sum << '\n';
  return EXIT_SUCCESS;
}

// tests/parse_test.cpp
#include "parse.hpp"

#include <array>
#include <cstdlib>
#include <iostream>

int main() {
  using gate::ParseError;
  int failures = 0;
  const auto check = [&failures](bool ok, const char* what) {
    if (!ok) {
      std::cerr << "FAIL: " << what << '\n';
      ++failures;
    }
  };
  const auto ok42 = gate::parse_u32("42");
  check(ok42.has_value() && *ok42 == 42U, "parses 42");
  check(gate::parse_u32("") == std::unexpected(ParseError::empty), "empty input");
  check(gate::parse_u32("4x") == std::unexpected(ParseError::not_a_number), "trailing junk");
  check(gate::parse_u32("4294967296") == std::unexpected(ParseError::overflow), "u32 overflow");
  constexpr std::array<std::uint32_t, 2> big{4'000'000'000U, 400'000'000U};
  check(gate::checked_sum(big) == std::unexpected(ParseError::overflow), "sum overflow detected");
  std::cerr << failures << " failure(s)\n";
  return failures == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
```

## 6. Commands that were run, with output

Run on a fresh copy materialized from this file. `<gate 3a>` and `<gate 9>` are the exact blocks from the
agent's "Verification gates" (and SKILL.md section 2). The copy was a new `git init` with no remote, so gate 3a
used its root-commit fallback; the second and third commands add and then remove a C-style cast in a header to
show that header changes are analyzed.

```text
$ git init -q -b main . && git add -A && git -c user.name=t -c user.email=t@t commit -qm template
  (exit 0)
$ git ls-files '*.cpp' '*.cc' '*.cxx' '*.hpp' '*.hh' '*.h' '*.ixx' '*.cppm' | xargs clang-format --dry-run --Werror
  (exit 0)
$ cmake --preset dev && cmake --build --preset dev && ctest --preset dev
  100% tests passed, 0 tests failed out of 4
  (exit 0)
$ run-clang-tidy.py -p out/dev -quiet -extra-arg=-Wno-unknown-warning-option
  (exit 0)
$ printf 'inline long widen(int v) { return (long)v; }\n' >> src/parse.hpp && <gate 3a>
  ./src/parse.hpp:17:35: error: C-style casts are discouraged; use static_cast [modernize-avoid-c-style-cast,-warnings-as-errors]
  (exit 1)
$ git checkout src/parse.hpp && <gate 3a>
  No relevant changes found.
  (exit 0)
$ cmake --workflow --preset ci
  100% tests passed, 0 tests failed out of 4
  (exit 0)
$ cmake --preset tsan && cmake --build --preset tsan && setarch "$(uname -m)" -R ctest --preset tsan
  100% tests passed, 0 tests failed out of 4
  (exit 0)
$ cmake --preset cov && cmake --build --preset cov && ctest --preset cov && gcovr -r . --filter 'src/' --fail-under-line 80 --fail-under-branch 60 out/cov
  src/main.cpp                                    17       17   100%
  src/parse.cpp                                   19       19   100%
  TOTAL                                           36       36   100%
  (exit 0)
$ cmake --preset release && cmake --build --preset release && ctest --test-dir out/release
  100% tests passed, 0 tests failed out of 4
  (exit 0)
$ <gate 9>
    GNU_RELRO      0x002d40 0x0000000000003d40 0x0000000000003d40 0x0002c0 0x0002c0 R   0x1
   0x000000000000001e (FLAGS)              BIND_NOW
   0x000000006ffffffb (FLAGS_1)            Flags: NOW PIE
      11: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND __stack_chk_fail@GLIBC_2.4 (9)
  (exit 0)
```

The first clang-tidy run on an earlier draft of these files failed with `readability-braces-around-statements`,
`cppcoreguidelines-avoid-non-const-global-variables`, `cppcoreguidelines-pro-type-vararg`, `cert-err33-c` and
`modernize-use-std-print`; the files above are the fixed versions.

Negative control for gate 9 (same copy, `cmake --preset release -DGATE_HARDENING=OFF`): it prints
`FAIL: -D_FORTIFY_SOURCE=3 in 0 of 3 compile commands`, while the `readelf` lines stay exactly as above
(`GNU_RELRO`, `BIND_NOW`, `NOW PIE`, `__stack_chk_fail`) because they come from Ubuntu's GCC defaults.

## 7. Dependencies, GoogleTest and supply chain

### Conan 2 + GoogleTest (run on the author box)

Conan 2.34.0 with a `conanfile.txt` and the CMake toolchain generator. GoogleTest is a test-only dependency:

```ini
[test_requires]
gtest/1.18.0

[generators]
CMakeDeps
CMakeToolchain
```

```cpp
// tests/parse_gtest.cpp
#include <gtest/gtest.h>

#include <array>
#include <cstdint>
#include <expected>

#include "parse.hpp"

namespace {
using gate::ParseError;

TEST(ParseU32, ParsesDecimal) { EXPECT_EQ(gate::parse_u32("42"), 42U); }

TEST(ParseU32, RejectsEmpty) { EXPECT_EQ(gate::parse_u32(""), std::unexpected(ParseError::empty)); }

TEST(ParseU32, RejectsTrailingJunk) {
  EXPECT_EQ(gate::parse_u32("4x"), std::unexpected(ParseError::not_a_number));
}

TEST(ParseU32, ReportsOverflow) {
  EXPECT_EQ(gate::parse_u32("4294967296"), std::unexpected(ParseError::overflow));
}

TEST(CheckedSum, DetectsOverflow) {
  constexpr std::array<std::uint32_t, 2> big{4'000'000'000U, 400'000'000U};
  EXPECT_EQ(gate::checked_sum(big), std::unexpected(ParseError::overflow));
}
}  // namespace
```

The `gtest` preset (section 2) points CMake at the generated toolchain, and `GATE_GTEST=ON` adds the
`find_package(GTest CONFIG REQUIRED)` / `gtest_discover_tests` block from section 1. The Conan `build_type`
must match the preset's `CMAKE_BUILD_TYPE`: CMakeDeps writes per-configuration generator expressions, so a
Debug build against Release-only packages configures cleanly and then fails with
`fatal error: gtest/gtest.h: No such file or directory` (measured).

```text
$ conan install . --output-folder=out/conan --build=missing -s build_type=Debug -s compiler.cppstd=23
      gtest/1.18.0#e2507fc4efe2ec9e2db9e5c91eefab9f - Cache
      gtest/1.18.0#e2507fc4efe2ec9e2db9e5c91eefab9f:2d8ad73e11d9fdd52609588cdb0990d56778c96a#15ab652c41df3bad839d34ecc4c336a8 - Cache
  gtest/1.18.0: Already installed! (1 of 1)
  CycloneDX SBOM written to ./out/conan/sbom.cdx.json
  Install finished successfully
  (exit 0)
$ cmake --preset gtest && cmake --build --preset gtest && ctest --preset gtest
  1/9 Test #1: ParseU32.ParsesDecimal ...........   Passed    0.01 sec
  2/9 Test #2: ParseU32.RejectsEmpty ............   Passed    0.01 sec
  3/9 Test #3: ParseU32.RejectsTrailingJunk .....   Passed    0.00 sec
  4/9 Test #4: ParseU32.ReportsOverflow .........   Passed    0.01 sec
  5/9 Test #5: CheckedSum.DetectsOverflow .......   Passed    0.00 sec
  6/9 Test #6: parse_test .......................   Passed    0.00 sec
  7/9 Test #7: app_sums .........................   Passed    0.01 sec
  8/9 Test #8: app_rejects_junk .................   Passed    0.00 sec
  9/9 Test #9: app_rejects_overflow .............   Passed    0.00 sec
  100% tests passed, 0 tests failed out of 9
  (exit 0)
$ clang-tidy -p out/gtest --quiet -extra-arg=-Wno-unknown-warning-option tests/parse_gtest.cpp
  (exit 0)
```

### SBOM, vulnerability audit and license check (BLD-7, gate 11)

Conan writes a CycloneDX SBOM from the resolved graph through a hook. Put this in
`$CONAN_HOME/extensions/hooks/hook_sbom.py` (the API is marked experimental in the Conan docs):

```python
import json
import os

from conan.api.output import ConanOutput
from conan.tools.sbom import cyclonedx_1_6


def post_generate(conanfile, **kwargs):
    sbom = cyclonedx_1_6(conanfile, add_tests=True)
    path = os.path.join(conanfile.generators_folder, "sbom.cdx.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2)
    ConanOutput().success(f"CycloneDX SBOM written to {path}")
```

```text
$ conan lock create . -s build_type=Debug -s compiler.cppstd=23
  Generated lockfile: ./conan.lock
  (exit 0)
$ python3 -c "import json; d=json.load(open('out/conan/sbom.cdx.json')); print(d['bomFormat'], d['specVersion'], [(c['name'], c['version'], [l['license'].get('id') for l in c.get('licenses', [])]) for c in d['components']])"
  CycloneDX 1.6 [('gtest', '1.18.0', ['BSD-3-Clause'])]
  (exit 0)
$ conan audit scan . -s build_type=Debug -s compiler.cppstd=23
  ERROR: Missing authentication token. Please authenticate and retry.
  (exit 1)
$ osv-scanner scan source --lockfile conan.lock
  Scanned ./conan.lock file and found 2 packages
  No issues found
  (exit 0)
```

What was and was not proven:
- SBOM: generated from the real graph; it lists `gtest 1.18.0`, license `BSD-3-Clause`, purl
  `pkg:conan/gtest@1.18.0`.
- `conan audit scan .` is the vulnerability check for Conan graphs. It needs a free token from
  `https://audit.conan.io/register`, passed as `CONAN_AUDIT_PROVIDER_TOKEN_CONANCENTER`; without it the command
  prints `ERROR: Missing authentication token`. [UNVERIFIED: not run with a token.] `conan audit list --sbom
  out/conan/sbom.cdx.json` and `--lockfile conan.lock` take the same token.
- OSV-Scanner reads `conan.lock`, but it is not a substitute: it found the packages yet reported
  `No issues found` for `zlib/1.2.11` (affected by CVE-2018-25032), and `api.osv.dev` returns no records for
  the `ConanCenter` ecosystem. Treat a clean OSV run on a Conan lockfile as "not checked".

### vcpkg [not run on the author box]

vcpkg manifest mode (vcpkg 2026.10.16). Create `vcpkg.json`, then pin the registry with
`vcpkg x-update-baseline --add-initial-baseline`, and point CMake at the toolchain file
(`-DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake`, best placed in the `base` preset).
`gtest` 1.18.0 and `fmt` 12.2.0 are the current versions in `microsoft/vcpkg` `ports/*/vcpkg.json` and in
ConanCenter's `recipes/*/config.yml` (read through the GitHub API on 2026-10-29).

```json
{
  "name": "gate",
  "version": "0.1.0",
  "dependencies": ["fmt", "gtest"]
}
```

```cmake
find_package(fmt CONFIG REQUIRED)
target_link_libraries(parse PRIVATE fmt::fmt)
# GoogleTest: the same GATE_GTEST block as in section 1
```

Supply chain with vcpkg: every installed port gets an SPDX SBOM at
`<installed_dir>/<triplet>/share/<port>/vcpkg.spdx.json` (Microsoft Learn, "Software Bill of Materials in
vcpkg"). vcpkg has no built-in vulnerability audit; convert the SPDX files with the CycloneDX CLI and scan them
with your organization's SCA tool. [UNVERIFIED: not run.]
