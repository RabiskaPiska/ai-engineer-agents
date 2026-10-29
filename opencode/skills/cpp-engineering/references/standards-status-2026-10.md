# C++ standards and compiler status (checked 2026-10-29)

Every line below comes from a primary source fetched on 2026-10-29; the URLs are listed in `sources/cpp.md`.
Re-check before relying on it after October 2026.

## The standard itself

- The current ISO C++ standard is **C++23, ISO/IEC 14882:2024**.
- WG21 finished technical work on C++26 at the March 2026 Croydon meeting and sent a Draft International
  Standard (DIS) to ballot. ISO's project page for ISO/IEC DIS 14882 (edition 8) shows "DIS ballot initiated:
  12 weeks" on 2026-07-31 and "Close of voting" on 2026-10-24. This pack uses 2026-10-24 as the close date;
  the Train IT article writes "closed on 23 October 2026", one day before ISO's stage date.
- The ballot was **disapproved**: 12 of 20 voting P-members approved (two-thirds needed) and 9 of 22 national
  bodies voted no (at most 25% allowed). Reported by the SC22 C convenor on 2026-10-24 and analysed by Mateusz
  Pusz (Train IT, 2026-10-25). It is the first C++ draft to fail a DIS ballot.
- The objections centre on contracts (P2900). Papers in flight: P4388R0 "Ship C++26" (publish as is) and
  P4433R0 "Do not remove Contracts from C++26"; at least one Direction Group member will recommend removing
  contracts while keeping library hardening. WG21 meets in Búzios, Brazil, 2026-11-16 to 21.
- What this means for code: C++26 features you use today come from a draft. Reflection, `std::execution` and
  library hardening are not the subject of the objections and are likely to survive, but the final text can
  still change. Contracts may be removed or redesigned. If the revision slips into 2027, it may be renamed.

## GCC 16 (16.1 on 2026-04-30, 16.2 on 2026-08-07)

- Default dialect changed from `-std=gnu++17` to `-std=gnu++20`. C++20 modules remain experimental and need
  `-fmodules`; new `--compile-std-module` builds `<bits/stdc++.h>`, `std` and `std.compat` up front.
- C++26 language features implemented: reflection P2996R13 (`-std=c++26 -freflection`), annotations for
  reflection P3394R4, splicing base class subobjects P3293R3, function parameter reflection P3096R12,
  `define_static_{string,object,array}` P3491R3, error handling in reflection P3560R2, expansion statements
  P1306R5, contracts P2900R14, erroneous behavior for uninitialized reads P2795R5, structured binding packs
  P1061R10, constexpr exceptions P3068R5, constexpr virtual inheritance P3533R2, partial program correctness
  P1494R5, attaching `main` to the global module P3618R0, "preprocessing is never undefined" P2843R3, partial
  P2686R4 (constexpr structured bindings).
- C++23 additions: P2036R3, P2590R2 (explicit lifetime management), P2246R1.
- libstdc++: C++20 support is no longer experimental, with ABI changes to several C++20 components (atomic
  wait/notify and semaphores, `<syncstream>`, `std::format` args and formatter specializations,
  `std::partial_ordering`, `std::variant` with `jthread`/`stop_token` alternatives, some range adaptors).
  Rebuild all C++20 code when moving to GCC 16.
- libstdc++ experimental C++26 library: `std::simd`, `std::inplace_vector`, `std::optional<T&>`,
  `std::copyable_function`, `std::function_ref`, `std::indirect`, `std::polymorphic`, `<debugging>`,
  `std::constant_wrapper`, `std::submdspan` and padded mdspan layouts, `std::philox_engine`,
  `std::atomic_ref::address()`. `std::execution` (P2300) is not listed.
- Earlier, relevant: GCC 15 enables libstdc++ debug assertions by default for unoptimized builds
  (`-D_GLIBCXX_NO_ASSERTIONS` turns them off) and ships experimental `std`/`std.compat` modules; GCC 14 added
  `-fhardened` and `std::print`/`std::println`.

## Clang / LLVM 23 (23.1.0 on 2026-08-25, 23.1.4 on 2026-10-20)

- C++2c: partial P1306R5 expansion statements (iterating expansion statements are not yet supported);
  `constinit`/`constexpr` propagation in structured bindings with tuple-like initializers. New experimental
  `-std=c++2d`. Reflection is not in mainline Clang (a Bloomberg fork implements P2996).
- C++20: P1857R3 modules dependency discovery.
- Diagnostics: `-Wlifetime-safety` (CFG-based intra-procedural use-after-free analysis, part of
  `-Weverything`), `-Wlifetime-safety-suggestions` (proposes `[[clang::lifetimebound]]`),
  `-Wlifetime-safety-noescape`, `-Wlifetime-safety-dangling-field`. `-Wunused-template` joined `-Wunused`.
- Static analyzer: experimental `alpha.cplusplus.UseAfterLifetimeEnd`.
- Breaking: `break`/`continue` inside a loop's own condition, increment or init-statement (via statement
  expressions) is now ill-formed, matching GCC.
- UBSan now checks aggregate copies (null, alignment, array bounds) for trivial copy/move in C++.
- libc++ 23 implemented papers include `ranges::fold`, `views::enumerate`, `views::concat`, `stride_view`,
  `std::constant_wrapper`, `mdspan::at()`, `text_encoding`, and removal of `span`'s `initializer_list`
  constructor for C++26 (P4144R1).

## MSVC

- Visual Studio 2026 decoupled the compiler from the IDE. Build Tools 14.50 (Nov 2025) is the LTS toolset;
  14.51 (VS 18.6, May 2026) is the default; a new minor ships about every six months.
- 14.51 adds C++23 features such as static `constexpr` variables in `constexpr` functions (P2647R1) and relaxed
  `constexpr` restrictions (P2448R2). Use `/std:c++23preview` or `/std:c++latest`.
- 14.52 (release candidate announced 2026-10-15 on the C++ Team Blog, VS 2026 Insiders channel; expected
  stable in November 2026 with VS 18.12) introduces `/std:c++23` and calls C++23 ready for production. The STL
  is C++23 feature-complete, with `constexpr <cmath>` (P0533R9) opt-in via `/Zc:cmath`. `/std:c++23preview` is
  now a deprecated alias.
- Binary compatibility with code built by VS 2015 and later is preserved.

## CMake 4.4 (4.4.5 on 2026-10-27)

- `import std` is still gated behind `CMAKE_EXPERIMENTAL_CXX_IMPORT_STD`.
- C++20 named modules now also work with clang-cl, except with the Visual Studio generators (the ClangCl
  toolset); targets providing modules can be consumed more flexibly.
- `cmake-instrumentation(7)` (added in 4.3) gained capture options in 4.4.

## Choosing a level

| Situation | Choose |
|---|---|
| New service or app, toolchains you control (GCC 14+, recent Clang, MSVC 14.51+) | C++23 |
| Library consumed by others, or older platform compilers | C++20 (C++17 only if a supported platform requires it) |
| Internal code generation or serialization tools that benefit from reflection | C++26 on GCC 16 with `-freflection`, isolated behind a stable C++23 interface |
| Contracts | Wait for the outcome of the November 2026 meeting before using them in interfaces |
