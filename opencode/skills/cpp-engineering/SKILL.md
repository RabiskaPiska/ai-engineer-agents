---
name: cpp-engineering
description: "Production C++ engineering rules and verification gates (October 2026: GCC 16.2, Clang/LLVM 23.1, MSVC 14.51/14.52, CMake 4.4). Use when writing, reviewing, refactoring, debugging or hardening C++ code, or when setting up CMake presets, clang-tidy, clang-format, sanitizers, coverage, fuzzing, benchmarks, vcpkg or Conan for a C++ project. Contains a rule catalog with the tool that enforces each rule and tested gate commands."
---

# C++ engineering (October 2026)

This skill is the working manual for the `cpp-engineer` agent. It has three parts: a rule catalog (what good
code looks like and which tool proves it), the gate procedure (commands and how to read their output), and
tested configuration files. Longer material lives in `references/`:

- `references/project-template.md`: a complete CMake + presets + clang-tidy + clang-format setup that was built
  and run on 2026-10-29, with its real output, plus vcpkg and Conan 2 wiring.
- `references/standards-status-2026-10.md`: what C++23/C++26 features each compiler ships, and the state of the
  C++26 ballot.

Rule IDs in square brackets (for example [R.11]) refer to the C++ Core Guidelines. The text here paraphrases
them; read the guideline itself when a case is borderline.

## 1. Rule catalog

Each rule says what to do, why, and how it is checked. "tidy:" names clang-tidy checks, "warn:" compiler
warnings, "san:" sanitizers.

### Ownership and lifetime (OWN)

| ID | Rule | Why | Checked by |
|---|---|---|---|
| OWN-1 | One owner per resource, expressed in the type: value, container, `unique_ptr`, or `shared_ptr` only for real shared ownership [R.1, R.20, R.21]. | Leaks and double frees come from ownership that lives only in comments. | tidy: `cppcoreguidelines-owning-memory`, `cppcoreguidelines-no-malloc`; san: ASan leak check |
| OWN-2 | No naked `new`/`delete`; use `std::make_unique`/`std::make_shared` [R.11, R.23]. | Exception-safe construction, single place to audit. | tidy: `cppcoreguidelines-owning-memory`, `modernize-make-unique`, `modernize-make-shared` |
| OWN-3 | Raw `T*`/`T&` are non-owning and must not outlive the pointee [R.3, I.11]. | Dangling is the top C++ memory-safety bug class. | san: ASan (`heap-use-after-free`, `stack-use-after-return`); warn: Clang `-Wdangling*`, `-Wlifetime-safety` (Clang 23, opt-in) |
| OWN-4 | Never return or store a `string_view`/`span`/reference to a local or temporary [F.43]. Annotate view-returning accessors with `[[clang::lifetimebound]]`. | The compiler can then flag the dangling call site. | warn: `-Wdangling`, `-Wreturn-stack-address`; tidy: `bugprone-dangling-handle`, `bugprone-return-const-ref-from-parameter` |
| OWN-5 | Rule of zero by default [C.20]; if one special member is user-declared, declare all five [C.21]. | Half-defined copy/move semantics cause double frees and silent copies. | tidy: `cppcoreguidelines-special-member-functions` |
| OWN-6 | Move operations, destructors and `swap` are `noexcept` [E.16, C.66]. | `std::vector` copies instead of moving when the move constructor may throw. | tidy: `performance-noexcept-move-constructor`, `performance-noexcept-swap` |
| OWN-7 | After `std::move(x)`, only assign to or destroy `x`. | Moved-from state is valid but unspecified. | tidy: `bugprone-use-after-move` |
| OWN-8 | No reference/pointer/iterator into a vector/string/deque across an operation that may reallocate. | Reallocation invalidates them; ASan sees it only if the test hits the reallocation. | san: ASan; review |
| OWN-9 | Escaping lambdas and coroutines capture/take by value [F.53, CP.51, CP.53]; no lock across `co_await` [CP.52]. | The frame outlives the caller's stack. | tidy: `cppcoreguidelines-avoid-capturing-lambda-coroutines`, `cppcoreguidelines-avoid-reference-coroutine-parameters` |

### Types and interfaces (TYP)

| ID | Rule | Checked by |
|---|---|---|
| TYP-1 | `enum class`, strong types for IDs/units, `std::chrono` for time, `std::variant` instead of `union`. | tidy: `cppcoreguidelines-pro-type-union-access`, `performance-enum-size` |
| TYP-2 | `const`/`constexpr` by default [Con.1, Con.5]; `explicit` single-argument constructors [C.46]. | tidy: `misc-const-correctness`, `google-explicit-constructor` (opt in) |
| TYP-3 | Every template parameter constrained by a concept [T.10, T.11]; no new `enable_if`. | tidy: `modernize-use-constraints` |
| TYP-4 | In-params: cheap types by value, others by `const&` [F.16]; return values, not out-params [F.20, F.21]. | tidy: `performance-unnecessary-value-param`, `performance-unnecessary-copy-initialization` |
| TYP-5 | `[[nodiscard]]` on status, `expected`, handle and builder returns. | tidy: `modernize-use-nodiscard`, `bugprone-unused-return-value`; warn: `-Wunused-result` |
| TYP-6 | Named casts only [ES.48, ES.49]; `std::bit_cast` for punning; no `memcpy` of non-trivially-copyable types. | warn: `-Wold-style-cast`, `-Wuseless-cast` (GCC); tidy: `cppcoreguidelines-pro-type-cstyle-cast`, `cppcoreguidelines-pro-type-reinterpret-cast`, `bugprone-undefined-memory-manipulation` |
| TYP-7 | No signed/unsigned mixing [ES.100, ES.102]; brace-init to reject narrowing [ES.23]; `std::cmp_less`, `std::ssize`. | warn: `-Wconversion -Wsign-conversion`; tidy: `bugprone-narrowing-conversions` |
| TYP-8 | Headers: `#pragma once` or guards, no `using namespace`, include what you use. | tidy: `google-build-using-namespace` (opt in), `misc-include-cleaner`; IWYU 0.27 |

### Errors (ERR)

| ID | Rule | Checked by |
|---|---|---|
| ERR-1 | One error policy per layer: exceptions for non-local failure and constructors [E.2]; `std::expected<T,E>` for expected failures or `-fno-exceptions` code. | review |
| ERR-2 | Throw by value, catch by `const&` [E.15]; never `catch (...) {}` without rethrow or logging. | tidy: `misc-throw-by-value-catch-by-reference`, `bugprone-empty-catch` |
| ERR-3 | No exception crosses a C ABI, C callback, thread boundary or destructor. Mark C-ABI functions, callbacks and thread entry functions `noexcept` so the check sees them. | tidy: `bugprone-exception-escape` (covers destructors, moves, `main`, `swap` and `noexcept` functions; list others in its `FunctionsThatShouldNotThrow` option); review |
| ERR-4 | Parse untrusted text with `std::from_chars` and check `ec` and `ptr`. | tidy: `cert-err34-c`, `bugprone-unchecked-string-to-number-conversion` |
| ERR-5 | Check `std::expected` before dereference; `.value()` throws `bad_expected_access`, `*e` on an error is UB. | tidy: `bugprone-unchecked-optional-access` (covers `optional`; review for `expected`) |

### Undefined behavior and hardening (UB)

| ID | Rule | Checked by |
|---|---|---|
| UB-1 | Initialize every variable at declaration [ES.20]. | warn: `-Wuninitialized -Wmaybe-uninitialized`; tidy: `cppcoreguidelines-init-variables`; san: MSan (Clang) |
| UB-2 | No signed overflow, bad shifts, misaligned access, OOB, null deref. | san: UBSan with `-fno-sanitize-recover=all` |
| UB-3 | Standard-library hardening on in every non-benchmark build: `-D_GLIBCXX_ASSERTIONS` or `-D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_FAST` (`_EXTENSIVE` for security-critical code, `_DEBUG` in tests). GCC 15+ enables libstdc++ assertions at `-O0` by default. | gate 9 (`-D_GLIBCXX_ASSERTIONS` in every release compile command); run-time abort, see gate output below |
| UB-4 | Release binaries carry the OpenSSF hardening set (section 3), set by the project (the template's `gate_hardening` target), not left to distro compiler defaults. | gate 9: compile/link commands, then `readelf` |
| UB-5 | Fuzz parsers of untrusted input (libFuzzer, Clang: `-fsanitize=fuzzer,address`). | fuzz smoke run |

### Concurrency (CON)

| ID | Rule | Checked by |
|---|---|---|
| CON-1 | Mutex declared next to the data it guards [CP.50]; RAII locking only [CP.20]; `std::scoped_lock` for several [CP.21]. | tidy: `cppcoreguidelines-avoid-non-const-global-variables`, `bugprone-unused-raii`; Clang `-Wthread-safety` |
| CON-2 | `std::jthread` + `std::stop_token`; never `detach()` [CP.26]; condition-variable waits take a predicate [CP.42]. | review (no clang-tidy check covers these); san: TSan |
| CON-3 | Default `seq_cst` atomics; weaker orderings need a benchmark and a comment; no hand-rolled lock-free code or double-checked locking [CP.100, CP.110]. | san: TSan |
| CON-4 | Every change touching threads, atomics or coroutines passes the TSan gate. | san: TSan |
| CON-5 | No non-reentrant C library calls in threaded code (`strtok`, `localtime`, `gmtime`, `rand`, `strerror`, `setenv`, `getenv`); use `_r`/`_s` variants, `std::chrono`, `<random>` or a lock. | tidy: `concurrency-mt-unsafe` (flagged all seven on clang-tidy 23.1.4) |

### Performance (PERF)

| ID | Rule | Checked by |
|---|---|---|
| PERF-1 | No optimization without before/after numbers on the same machine [Per.4]. | Google Benchmark 1.10.0, `perf stat` |
| PERF-2 | Contiguous data, reserve capacity, avoid per-element allocation, struct-of-arrays for hot loops [Per.19]. | profiler (perf, VTune, Tracy, heaptrack) |
| PERF-3 | No copies of large objects by accident: `const auto&` in range-for, move into sinks. | tidy: `performance-for-range-copy`, `performance-move-const-arg`, `performance-inefficient-vector-operation` |
| PERF-4 | Release: `-O2`, LTO (`CMAKE_INTERPROCEDURAL_OPTIMIZATION ON`), keep frame pointers if production profiling matters. | build log |

### Build and packaging (BLD)

| ID | Rule | Checked by |
|---|---|---|
| BLD-1 | Explicit standard per target or project; `CMAKE_CXX_EXTENSIONS OFF`. GCC 16 changed its default to `gnu++20`. | configure log |
| BLD-2 | Target-based CMake (`target_*` with correct `PUBLIC/PRIVATE/INTERFACE`), no `file(GLOB)` for sources, third-party includes as `SYSTEM`. | review; `cmake --build` |
| BLD-3 | `CMakePresets.json` defines dev/asan/tsan/cov/release and a `ci` workflow; `compile_commands.json` exported. | `cmake --workflow --preset ci` |
| BLD-4 | Dependencies pinned: vcpkg manifest with `builtin-baseline`, or Conan 2 with a lockfile. | `vcpkg.json` / `conan.lock` present |
| BLD-5 | Do not mix C++20 objects built by GCC 15 or older with GCC 16 builds (libstdc++ ABI changes in atomic wait, semaphores, `<syncstream>`, `std::format` args, `partial_ordering`, some range adaptors). | rebuild everything on toolchain bump |
| BLD-6 | `-Werror` in CI and dev presets only, never forced on downstream builds. | presets |
| BLD-7 | Supply chain on every dependency change: SBOM from the package manager's resolved graph (Conan CycloneDX hook; vcpkg's per-port `vcpkg.spdx.json`), vulnerability audit of the lockfile (`conan audit scan`; vcpkg has none built in), license allow-list check on the SBOM. | gate 10 (audit [UNVERIFIED]: needs a token, not run) |

## 2. Gate procedure

Run gates in this order and stop at the first failure. Read exit codes directly (`set -o pipefail` or
`${PIPESTATUS[0]}`), because `cmd | tail` reports the exit status of `tail`.

| # | Gate | Command (fallback when no presets) | Pass looks like |
|---|---|---|---|
| 0 | Configure | `cmake --preset dev` (`cmake -S . -B out/dev -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`) | `-- Build files have been written to` |
| 1 | Format | block below (`clang-format --dry-run --Werror` on the shared glob list) | exit 0, no output |
| 2 | Build, warnings as errors | `cmake --build --preset dev` | exit 0 |
| 3a | clang-tidy (changed sources and headers) | block below (`clang-tidy-diff.py` against the merge base) | exit 0 or `No relevant changes found.` |
| 3b | clang-tidy (whole tree) | `run-clang-tidy.py -p out/dev -quiet -extra-arg=-Wno-unknown-warning-option` | exit 0 |
| 3c | Cppcheck | `cppcheck --project=out/dev/compile_commands.json --enable=warning,performance,portability --inline-suppr --suppress=missingIncludeSystem --error-exitcode=1 --quiet` | exit 0 |
| 4 | Unit tests | `ctest --preset dev` | `100% tests passed` |
| 5 | ASan + UBSan | `cmake --workflow --preset ci` | tests pass, no `ERROR: AddressSanitizer`, no `runtime error:` |
| 6 | TSan | `cmake --preset tsan && cmake --build --preset tsan && ctest --preset tsan` | no `WARNING: ThreadSanitizer` |
| 7 | Coverage | `cmake --preset cov && cmake --build --preset cov && ctest --preset cov && gcovr -r . --filter 'src/' --fail-under-line 80 --fail-under-branch 60 out/cov` | exit 0 |
| 8 | Benchmarks | block below (two JSON runs + `compare.py`) | `*_pvalue` below 0.05 and the median moved the right way |
| 9 | Hardening | block below (compile/link commands, then `readelf`) | no `FAIL` line; RELRO, `BIND_NOW`, `PIE`, `__stack_chk_fail` |
| 10 | Supply chain (dependency changed) | block below (lockfile, SBOM licenses, `conan audit scan`) | exit 0; audit without a token is NOT RUN |
| 11 | Optional | Valgrind 3.28 (`valgrind --error-exitcode=1 --leak-check=full ./app`), MSan (Clang, all deps instrumented), libFuzzer smoke run (`./fuzz_target -max_total_time=60`), IWYU, Mull mutation testing | as documented |

Commands for the rows that need a pipe. They are the same text as the agent's "Verification gates" block,
so the file globs and options are defined once. All five were run on the template on 2026-10-29 (the audit
only up to its missing-token error); outputs are below and in `references/project-template.md`.

```bash
set -o pipefail

# 1. Format: pass = exit 0 and no output
git ls-files '*.cpp' '*.cc' '*.cxx' '*.hpp' '*.hh' '*.h' '*.ixx' '*.cppm' | xargs clang-format --dry-run --Werror

# 3. Static analysis on changed sources and headers: pass = exit 0 or "No relevant changes found."
#    Base = merge-base with BASE_REF (default origin/main), else the root commit, so it also works in a repo
#    with no remote. CI needs history for the merge base (GitHub Actions: actions/checkout with fetch-depth: 0).
#    clang-tidy-diff.py ships with clang-tidy (the PyPI clang-tidy wheel installs it under that name).
#    -extra-arg silences GCC-only warning flags (-Wbidi-chars, -Wtrampolines) in a GCC compile database.
base=$(git merge-base HEAD "${BASE_REF:-origin/main}" 2>/dev/null || git rev-list --max-parents=0 HEAD | tail -n 1)
git diff -U0 --no-color "$base" -- '*.cpp' '*.cc' '*.cxx' '*.hpp' '*.hh' '*.h' '*.ixx' '*.cppm' |
  clang-tidy-diff.py -p1 -path out/dev -quiet -extra-arg=-Wno-unknown-warning-option \
    -iregex '.*\.(cpp|cc|cxx|hpp|hh|h|ixx|cppm)'

# 8. Benchmarks when performance was the goal: same machine, 10+ repetitions, one JSON file per side.
#    Keep per-repetition data in the files (no --benchmark_report_aggregates_only: without it compare.py
#    prints no U test). compare.py is google/benchmark's tools/compare.py (needs numpy + scipy from
#    tools/requirements.txt). pass = the *_pvalue row is below 0.05 and the median moved the right way;
#    p >= 0.05 means "no measurable change", whatever the median says.
B='--benchmark_repetitions=10 --benchmark_display_aggregates_only=true --benchmark_out_format=json'
./out/release/bench/my_bench $B --benchmark_out=before.json   # binary built from the base commit
./out/release/bench/my_bench $B --benchmark_out=after.json    # binary built from the change
python3 benchmark/tools/compare.py benchmarks before.json after.json

# 9. Hardening: the build commands first, then the shipped ELF. Ubuntu's GCC defaults to PIE,
#    -fstack-protector-strong and -z now, so readelf alone passes even for a project that sets no flags.
#    pass = no FAIL line, then GNU_RELRO, BIND_NOW, "FLAGS_1 ... NOW PIE" and __stack_chk_fail (__*_chk symbols
#    appear only where the code calls fortifiable libc functions). With libc++, check
#    -D_LIBCPP_HARDENING_MODE instead of -D_GLIBCXX_ASSERTIONS.
(
  cc=out/release/compile_commands.json; n=$(grep -c '"command"' "$cc")
  for flag in -D_FORTIFY_SOURCE=3 -D_GLIBCXX_ASSERTIONS -fstack-protector-strong -fstack-clash-protection; do
    m=$(grep '"command"' "$cc" | grep -c -- "$flag")
    [ "$m" -eq "$n" ] || { echo "FAIL: $flag in $m of $n compile commands"; exit 1; }
  done
  ninja -C out/release -t commands app | tail -n 1 | grep -q -- '-Wl,-z,now' || { echo "FAIL: link lacks -z now"; exit 1; }
)
readelf -lW out/release/app | grep GNU_RELRO; readelf -dW out/release/app | grep -E 'BIND_NOW|FLAGS'
readelf -sW out/release/app | grep -E '__stack_chk_fail|_chk'

# 10. Supply chain, when a dependency was added or bumped (Conan shown; vcpkg: skill template section 7).
#     Use the same -s/-pr options as the conan install. pass = lockfile regenerated, every SBOM component has an
#     allowed license, and conan audit exits 0 (its default fails only on CVSS >= 9.0; -sl 7.0 fails on high).
#     The audit needs a free token in CONAN_AUDIT_PROVIDER_TOKEN_CONANCENTER; without it, report NOT RUN.
#     OSV-Scanner reads conan.lock but has no ConanCenter advisories, so its "No issues found" proves nothing.
conan lock create .
python3 -c "import json; d=json.load(open('out/conan/sbom.cdx.json')); print([(c['name'], c['version'], [l['license'].get('id') for l in c.get('licenses', [])]) for c in d['components']])"
conan audit scan . -sl 7.0
```

With Clang, the coverage alternative is `-fprofile-instr-generate -fcoverage-mapping`, then
`llvm-profdata merge -sparse default.profraw -o app.profdata` and `llvm-cov report ./app -instr-profile=app.profdata`.

### Evidence from a real run (2026-10-29, author box: GCC 13.3, CMake 3.28.3, Ninja 1.13.2, clang-format 23.1.3, clang-tidy 23.1.4, gcovr 8.8, Conan 2.34.0)

These outputs are from the sample project in `references/project-template.md`. They show what each gate
prints when it catches a defect, so you can recognize real failures and real passes.

```text
# ASan + UBSan on an out-of-bounds read through vector::data()
==1092000==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x50200000001c ...
SUMMARY: AddressSanitizer: heap-buffer-overflow neg/oob.cpp:2 in main            (exit 134)

# -Wsign-conversion -Werror on v[i] with int i
error: conversion to 'std::vector<int>::size_type' {aka 'long unsigned int'} from 'int'
       may change the sign of the result [-Werror=sign-conversion]                    (exit 1)

# -O2 -D_GLIBCXX_ASSERTIONS on v[3] for a 3-element vector
Assertion '__n < this->size()' failed.                                                (exit 134)

# TSan on two jthreads incrementing a plain int
FATAL: ThreadSanitizer: unexpected memory mapping ...         (exit 66; kernel ASLR too high for this runtime)
# rerun under: setarch "$(uname -m)" -R ./race
WARNING: ThreadSanitizer: data race (pid=1093125)
SUMMARY: ThreadSanitizer: data race neg/race.cpp:5 in operator()                      (exit 66)

# _FORTIFY_SOURCE=3 + strcpy overflow in a hardened build
*** buffer overflow detected ***: terminated                                          (exit 134)

# clang-tidy 23.1.4 with the .clang-tidy below, before fixes (excerpt)
error: statement should be inside braces [readability-braces-around-statements,-warnings-as-errors]
error: variable 'failures' is non-const and globally accessible ... [cppcoreguidelines-avoid-non-const-global-variables]
error: use 'std::println' instead of 'fprintf' [modernize-use-std-print,-warnings-as-errors]

# after fixes: clang-format exit 0, clang-tidy exit 0, workflow "ci":
100% tests passed, 0 tests failed out of 4

# gcovr 8.8, first template: src/parse.cpp 19 lines, 18 executed, 94%, missing line 33 (an untested success
# path); the app_sums test added later covers it: 19/19, 100%

# gate 9 on a release build without the project's hardening flags (Ubuntu GCC 13 defaults only)
FAIL: -D_FORTIFY_SOURCE=3 in 0 of 3 compile commands
  GNU_RELRO ...   (FLAGS) BIND_NOW   (FLAGS_1) Flags: NOW PIE   __stack_chk_fail@GLIBC_2.4   <- readelf alone passes

# previous gate 3a (git diff ... origin/HEAD...) in a repository with no remote
fatal: bad revision 'origin/HEAD...'                                                  (exit 128)
# current gate 3a after adding a C-style cast to src/parse.hpp only
src/parse.hpp:17:35: error: C-style casts are discouraged; use static_cast [modernize-avoid-c-style-cast,...]  (exit 1)

# gate 8 with compare.py (Google Benchmark 1.10.0): vector::reserve added
BM_fill_pvalue    0.0002   U Test, Repetitions: 10 vs 10      BM_fill_median  -0.2538
# gate 8 on the same binary twice: the median "improved" by 11%, the U test says no change
BM_fill_pvalue    0.1859   U Test, Repetitions: 10 vs 10      BM_fill_median  -0.1096
```

Lessons from those runs: a sanitizer gate must show that the sanitizer actually executed (the first TSan run
did not test anything); coverage reports point at the exact untested path to add a test for; a binary check
can pass on compiler defaults, so check what the project itself passes; and a median difference between two
benchmark runs is not a result until the U test says so.

## 3. Hardening flag sets

From the OpenSSF Compiler Options Hardening Guide for C and C++ (revision dated 2026-08-20). Verified on GCC 13
on 2026-10-29 except where marked. The template's `gate_hardening` INTERFACE target
(`references/project-template.md` section 1) applies this set plus `-D_GLIBCXX_ASSERTIONS` in release builds,
and gate 9 checks that every release compile command carries it.

```text
# All builds (GCC and Clang)
-O2 -Wall -Wformat -Wformat=2 -Wconversion -Wimplicit-fallthrough -Werror=format-security
-U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3
-D_GLIBCXX_ASSERTIONS                                  # libstdc++
-D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_FAST   # libc++
-fstrict-flex-arrays=3 -fstack-clash-protection -fstack-protector-strong
-Wl,-z,nodlopen -Wl,-z,noexecstack -Wl,-z,relro -Wl,-z,now -Wl,--as-needed -Wl,--no-copy-dt-needed-entries

# Executables: -fPIE -pie        Shared libraries: -fPIC -shared
# x86_64: -fcf-protection=full -fzero-call-used-regs=used-gpr
# AArch64: -mbranch-protection=standard -fzero-call-used-regs=used-gpr
# GCC only: -Wtrampolines -fzero-init-padding-bits=all   (the latter needs GCC 15+; not tested here)
# GCC 12+, source written left-to-right only (Trojan Source): -Wbidi-chars=any
# Production: -fno-delete-null-pointer-checks -fno-strict-overflow -fno-strict-aliasing -ftrivial-auto-var-init=zero
# GCC 14+: -fhardened enables a vendor-chosen subset; list it with  g++ --help=hardened
# MSVC: /sdl /guard:cf /DYNAMICBASE, link /NXCOMPAT /CETCOMPAT
```

`_FORTIFY_SOURCE` does nothing at `-O0`. Confirm it is active with
`echo '#include <stdio.h>' | g++ -x c++ -E -dM -O2 -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 - | grep FORTIFY`
(expect `#define __USE_FORTIFY_LEVEL 3`). Note that `-Wl,-z,nodlopen` is for executables and libraries that must
never be loaded with `dlopen`; drop it for plugins.

## 4. Sanitizer matrix

| Build | Flags | Catches | Combine with |
|---|---|---|---|
| asan | `-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer` | heap/stack/global overflow, use-after-free/return/scope, leaks (LSan), UB | default CI leg |
| tsan | `-fsanitize=thread` | data races, lock-order inversions | not with ASan or MSan |
| msan | `-fsanitize=memory -fno-omit-frame-pointer` (Clang only) | uninitialized reads | needs every dependency instrumented |
| fuzz | `-fsanitize=fuzzer,address,undefined` (Clang only) | crashes on generated inputs | per parser target |
| MSVC | `/fsanitize=address` | ASan subset | no UBSan/TSan; run those on Clang/GCC |

Runtime options used in the presets: `ASAN_OPTIONS=detect_leaks=1:abort_on_error=1:detect_stack_use_after_return=1`,
`UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1`, `TSAN_OPTIONS=halt_on_error=1:second_deadlock_stack=1`.
For production heap-error sampling, GWP-ASan (enabled in Chrome, Android, Apple platforms) has near-zero overhead.

## 5. Language-level choices for October 2026

- **Standard**: C++23 for new code when the compiler matrix allows it (GCC 14+, Clang 18+ with a C++23 standard
  library, MSVC 14.51 with `/std:c++23preview`; MSVC 14.52 adds `/std:c++23`). C++20 when a supported platform
  is older. See `references/standards-status-2026-10.md` for per-feature detail.
- **C++26**: the DIS failed its ISO ballot (close of voting 2026-10-24), so the current standard remains C++23. Reflection
  (GCC 16 with `-std=c++26 -freflection`) is reasonable for internal tooling and code generation. Contracts are
  the disputed feature and may be removed or changed; do not put them in library interfaces yet.
- **Reflection API shape** (for when it is used): member queries take an access context, and `template for`
  iterates a static array, so the idiom is
  `template for (constexpr auto m : std::define_static_array(std::meta::nonstatic_data_members_of(^^T, std::meta::access_context::current())))`.
  Several 2025-era examples omit the access context and no longer compile. [UNVERIFIED locally: no GCC 16 on
  the author box; signature taken from cppreference `<meta>` and P2996R13.]
- **Modules**: named modules are workable with CMake 4.4 + Ninja on GCC 14+/Clang/MSVC; `import std` is still
  experimental in CMake (`CMAKE_EXPERIMENTAL_CXX_IMPORT_STD`). Libraries for external consumers keep headers.
- **Formatting output**: `std::print`/`std::println` (C++23; libstdc++ since GCC 14) or {fmt} 12.2.0 on older
  standard libraries.

## 6. Debugging and profiling quick reference

- LLDB MCP (`lldb-mcp`, LLDB 22+): in LLDB 23.1 it exposes one tool, `lldb_command`, plus `lldb://debugger/<id>`
  resources; it starts an `lldb` in the background if none is running (override with `LLDB_EXE_PATH`).
  Useful commands: `target create ./app`, `breakpoint set --name fn`, `run`, `bt`, `frame variable`,
  `target create ./app --core core`. Debuggee output is not returned; redirect it to a file.
- GDB 18.1: `gdb -batch -ex run -ex bt --args ./app ...` gives a backtrace in one shot.
- Build for debugging with `-g -Og` (or `-O0`) and `-fno-omit-frame-pointer`.
- Profiling: `perf record -g ./app && perf report`, heaptrack for allocations, Tracy for frame-level timing.

## 7. When to load the references

- Setting up a new project, CI leg or preset: `references/project-template.md`.
- Choosing a standard level or checking whether a feature is available: `references/standards-status-2026-10.md`.
