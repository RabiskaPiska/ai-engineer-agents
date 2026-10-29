# Baseline status snapshot — web-features 3.44.0 (published 2026-10-22, read 2026-10-29)

Generated from `data.json` of the npm package `web-features@3.44.0` (Apache-2.0,
github.com/web-platform-dx/web-features) with a read-only Python script; no package code was run.

- **Widely** = supported in every core browser (Chrome, Chrome Android, Edge, Firefox, Firefox
  Android, Safari, Safari iOS) for at least 30 months. Use without fallback.
- **Newly** = supported in every core browser, for less than 30 months. Use when the failure mode is
  harmless or behind `@supports`, unless the project policy allows Newly.
- **Limited** = not yet in every core browser. Progressive enhancement only.
- Browser columns show the first version web-features counts as full support. A dash means
  web-features does not count that browser yet; the feature may still be partial, flagged, or
  shipped after this data release (for example Safari 27 for `sizes="auto"`, reported by web.dev
  on 2026-10-02 but not yet in this data). Recheck at https://webstatus.dev before relying on a dash.
- This file is a snapshot. Re-generate it, or query the package directly, when it is more than a
  month old:

```sh
npm pack web-features@latest && tar xzf web-features-*.tgz
python3 -I -c 'import json;f=json.load(open("package/data.json"))["features"];print(f["anchor-positioning"]["status"])'
```

| Feature id | Status | Newly since | Widely since | Chrome | Firefox | Safari |
|---|---|---|---|---|---|---|
| **HTML elements and attributes** | | | | | | |
| `dialog` | Widely | 2022-03-14 | 2024-09-14 | 37 | 98 | 15.4 |
| `popover` | Newly | 2025-01-27 | – | 116 | 125 | 17 |
| `invoker-commands` | Newly | 2025-12-12 | – | 135 | 144 | 26.2 |
| `details-name` | Newly | 2024-09-03 | – | 120 | 130 | 17.2 |
| `search` | Widely | 2023-10-13 | 2026-04-13 | 118 | 118 | 17 |
| `inert` | Widely | 2023-04-11 | 2025-10-11 | 102 | 112 | 15.5 |
| `loading-lazy` | Widely | 2023-12-19 | 2026-06-19 | 77 | 121 | 16.4 |
| `fetch-priority` | Newly | 2024-10-29 | – | 103 | 132 | 17.2 |
| `modulepreload` | Widely | 2023-09-18 | 2026-03-18 | 66 | 115 | 17 |
| `preloading-responsive-images` | Widely | 2023-12-11 | 2026-06-11 | 73 | 78 | 17.2 |
| `declarative-shadow-dom` | Widely | 2024-02-20 | 2026-08-20 | 111 | 123 | 16.4 |
| `customizable-select` | Limited | – | – | 135 | – | 27 |
| `dialog-closedby` | Limited | – | – | 134 | 141 | – |
| `popover-hint` | Limited | – | – | 151 | 153 | – |
| `interest-invokers` | Limited | – | – | 142 | – | – |
| `hidden-until-found` | Limited | – | – | 102 | 148 | – |
| `sizes-auto` | Limited | – | – | 126 | 150 | – |
| `speculation-rules` | Limited | – | – | 109 | – | – |
| **Selectors** | | | | | | |
| `has` | Widely | 2023-12-19 | 2026-06-19 | 105 | 121 | 15.4 |
| `nesting` | Widely | 2023-12-11 | 2026-06-11 | 120 | 117 | 17.2 |
| `focus-visible` | Widely | 2022-03-14 | 2024-09-14 | 86 | 85 | 15.4 |
| `user-pseudos` | Widely | 2023-11-02 | 2026-05-02 | 119 | 88 | 16.5 |
| `dir-pseudo` | Widely | 2023-12-07 | 2026-06-07 | 120 | 49 | 16.4 |
| `open-pseudo` | Newly | 2026-05-11 | – | 133 | 136 | 26.5 |
| **Cascade and architecture** | | | | | | |
| `cascade-layers` | Widely | 2022-03-14 | 2024-09-14 | 99 | 97 | 15.4 |
| `scope` | Newly | 2026-03-24 | – | 143 | 146 | 26.4 |
| `registered-custom-properties` | Newly | 2024-07-09 | – | 85 | 128 | 16.4 |
| `revert-rule` | Newly | 2026-09-14 | – | 148 | 150 | 27 |
| `container-queries` | Widely | 2023-02-14 | 2025-08-14 | 105 | 110 | 16 |
| `container-style-queries` | Newly | 2026-05-19 | – | 111 | 151 | 18 |
| `container-scroll-state-queries` | Limited | – | – | 133 | – | – |
| `media-query-range-syntax` | Widely | 2023-03-27 | 2025-09-27 | 104 | 102 | 16.4 |
| **Layout and sizing** | | | | | | |
| `subgrid` | Widely | 2023-09-15 | 2026-03-15 | 117 | 71 | 16 |
| `aspect-ratio` | Widely | 2021-09-20 | 2024-03-20 | 88 | 89 | 15 |
| `logical-properties` | Widely | 2021-09-20 | 2024-03-20 | 89 | 66 | 15 |
| `viewport-unit-variants` | Widely | 2022-12-05 | 2025-06-05 | 108 | 101 | 15.4 |
| `min-max-clamp` | Widely | 2020-07-28 | 2023-01-28 | 79 | 75 | 13.1 |
| `field-sizing` | Newly | 2026-06-16 | – | 123 | 152 | 26.2 |
| `interpolate-size` | Limited | – | – | 129 | – | – |
| `calc-size` | Limited | – | – | 129 | – | – |
| `stretch` | Limited | – | – | 138 | – | 27 |
| `anchor-positioning` | Limited | – | – | – | – | 27 |
| `scrollbar-gutter` | Newly | 2024-12-11 | – | 94 | 97 | 18.2 |
| `scrollbar-color` | Newly | 2025-12-12 | – | 121 | 64 | 26.2 |
| `overflow-anchor` | Newly | 2026-09-14 | – | 56 | 66 | 27 |
| `scroll-snap` | Widely | 2020-01-15 | 2022-07-15 | 69 | 68 | 11 |
| `grid-lanes` | Limited | – | – | – | – | – |
| `margin-trim` | Limited | – | – | – | – | 16.4 |
| `reading-flow` | Limited | – | – | 137 | – | – |
| **Color and typography** | | | | | | |
| `oklab` | Widely | 2023-05-09 | 2025-11-09 | 111 | 113 | 15.4 |
| `lab` | Widely | 2023-05-09 | 2025-11-09 | 111 | 113 | 15 |
| `color-mix` | Widely | 2023-05-09 | 2025-11-09 | 111 | 113 | 16.2 |
| `relative-color` | Newly | 2024-09-16 | – | 125 | 128 | 18 |
| `alpha` | Newly | 2026-09-14 | – | 152 | 155 | 27 |
| `light-dark` | Newly | 2024-05-13 | – | 123 | 120 | 17.5 |
| `color-scheme` | Widely | 2022-02-03 | 2024-08-03 | 98 | 96 | 13 |
| `contrast-color` | Newly | 2026-04-10 | – | 147 | 146 | 26 |
| `text-wrap` | Newly | 2024-10-17 | – | 130 | 124 | 17.5 |
| `text-wrap-balance` | Newly | 2024-05-13 | – | 114 | 121 | 17.5 |
| `text-wrap-pretty` | Limited | – | – | 117 | – | 26 |
| `text-box` | Limited | – | – | 133 | – | 18.2 |
| `font-display` | Widely | 2020-01-15 | 2022-07-15 | 60 | 58 | 11.1 |
| `hyphens` | Widely | 2023-09-18 | 2026-03-18 | 88 | 43 | 17 |
| `initial-letter` | Limited | – | – | 110 | – | – |
| `sibling-count` | Newly | 2026-08-18 | – | 138 | 154 | 26.2 |
| `shape-function` | Newly | 2026-02-24 | – | 135 | 148 | 18.4 |
| `if` | Limited | – | – | 137 | – | – |
| `attr` | Limited | – | – | 133 | 155 | – |
| `corner-shape` | Limited | – | – | 139 | – | – |
| **Motion and transitions** | | | | | | |
| `starting-style` | Newly | 2024-08-06 | – | 117 | 129 | 17.5 |
| `transition-behavior` | Newly | 2024-08-06 | – | 117 | 129 | 17.4 |
| `view-transitions` | Newly | 2025-10-14 | – | 111 | 144 | 18 |
| `cross-document-view-transitions` | Limited | – | – | 126 | – | 18.2 |
| `scroll-driven-animations` | Limited | – | – | 115 | – | 26 |
| `prefers-reduced-motion` | Widely | 2020-01-15 | 2022-07-15 | 74 | 63 | 10.1 |
| **Rendering and performance** | | | | | | |
| `content-visibility` | Newly | 2025-09-15 | – | 108 | 130 | 26 |
| `avif` | Widely | 2024-01-25 | 2026-07-25 | 85 | 113 | 16.4 |
| `webp` | Widely | 2020-09-16 | 2023-03-16 | 32 | 65 | 14 |
| `jpegxl` | Limited | – | – | 155 | 158 | 17 |
| `image-set` | Widely | 2023-09-18 | 2026-03-18 | 113 | 89 | 17 |
| **Accessibility and preferences** | | | | | | |
| `forced-colors` | Widely | 2022-09-12 | 2025-03-12 | 89 | 89 | 16 |
| `prefers-color-scheme` | Widely | 2020-01-15 | 2022-07-15 | 76 | 67 | 12.1 |
| `print-color-adjust` | Newly | 2025-05-01 | – | 136 | 97 | 15.4 |
| **Security** | | | | | | |
| `trusted-types` | Newly | 2026-02-24 | – | 83 | 148 | 26 |
| `sanitizer` | Limited | – | – | 146 | 148 | – |

## Reading notes for features agents get wrong

- **Anchor positioning**: web-features 3.44.0 marks it Limited and counts only Safari 27 / Safari iOS
  27 as full support. Chrome/Edge 125+ and Safari 26 ship implementations that it treats as partial
  (Chrome 125 and Safari 26 appear only on sub-features such as `anchor-positioning-animations`),
  and good-css's support notes list Firefox 147 for popover anchoring. It is an Interop 2026 focus area. Use it inside `@supports (position-area: block-end)`;
  without support a `popover` opens centered, which is an acceptable fallback.
- **Customizable `<select>`** (`appearance: base-select`, `::picker(select)`, `<selectedcontent>`):
  Chrome 135 and Safari 27; Firefox behind a flag. Opt in under `@supports (appearance: base-select)`
  so other browsers keep the native control.
- **`@starting-style` + `transition-behavior: allow-discrete`** are Newly available, but exit
  animations of `<dialog>`/popovers snap closed in Safari 27 and Firefox (entry animates). No
  fallback is needed.
- **View transitions**: same-document is Newly (2025-10-14); cross-document
  (`@view-transition { navigation: auto; }`) is Limited (no Firefox) and safely ignored where
  unsupported.
- **Scroll-driven animations** (`animation-timeline: scroll()/view()`) are Limited (no Firefox).
  Guard with `@supports (animation-timeline: view())` and keep content visible without them.
- **`text-wrap: pretty`** is Limited but harmless (ignored where unsupported). `balance` is Newly.
- **`interpolate-size` / `calc-size()`** are Chromium-only. An accordion that does not animate its
  height elsewhere is an acceptable fallback; content must still open.
- **Sanitizer API** (`Element.setHTML()`) is Limited (Chrome 146, Firefox 148, no Safari). Keep
  DOMPurify as the default and feature-detect `setHTML`.
- **Trusted Types** became Newly available on 2026-02-24 (Firefox 148, Safari 26). A
  `require-trusted-types-for 'script'` CSP is now enforceable in every engine.
- **Container style queries** (`@container style(--x: y)`) became Newly available on 2026-05-19.
- **`field-sizing: content`** became Newly available on 2026-06-16; auto-growing textareas no longer
  need script under a Newly policy.

## Interop 2026 focus areas (web.dev, published 2026-02-12)

Anchor positioning; container style queries; dialogs and popovers (`closedby`, `:open`,
`popover="hint"`); scroll-driven animations; view transitions (including cross-document,
`blocking="render"`, `<link rel="expect">`, `:active-view-transition-type()`); `attr()`;
`contrast-color()`; custom highlights; fetch uploads and ranges; IndexedDB `getAllRecords()`; JSPI
for Wasm; media pseudo-classes (`:playing`, `:paused`, …); Navigation API; scoped custom element
registries; scroll snap; `shape()`; web compat (ESM loading, scroll/animation event timing,
unprefixed `user-select`); WebRTC; WebTransport; CSS `zoom`. Features in this list are the ones most
likely to change status during the year; recheck them first.
