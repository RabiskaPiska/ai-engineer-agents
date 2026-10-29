---
name: web-engineering
description: "Rule catalog, recipes and verification gates for production HTML and CSS as of October 2026: semantic markup, forms, WCAG 2.2 AA accessibility, Baseline browser-support policy (web-features 3.44.0), CSS architecture (layers, tokens, nesting, @scope, container queries), layout, motion, Core Web Vitals, and markup-level security (CSP, Trusted Types, SRI). Use when writing, reviewing or debugging HTML/CSS, templates or component markup, or when setting up Stylelint, html-validate, Playwright+axe or Lighthouse gates."
---

# Web engineering (HTML / CSS), October 2026

Companion skill for the `web-engineer` agent. The agent file holds the operating loop and the
headline rules; this skill holds the detail you look up while working. Two references sit next to it:

- `references/baseline-2026-10.md`: Baseline status of about 90 features from web-features 3.44.0,
  plus notes on features that agents most often misjudge, and the Interop 2026 focus list.
- `references/configs.md`: Stylelint, ESLint CSS, html-validate, Playwright + axe, Lighthouse and
  CSS skeleton templates checked against each tool's docs.

## 0. Pre-flight (two minutes, every task)

```sh
cat package.json | head -60                          # build tool, CSS tooling, test runner, browserslist
ls -a | grep -Ei 'browserslist|stylelint|eslint|prettier|biome|htmlvalidate|playwright|vite|tailwind'
npx browserslist                                     # the concrete browsers your targets resolve to
grep -rn "@layer" --include=*.css . | head           # existing layer order
grep -rn -- "--color-\|--space-\|--font-" --include=*.css . | head   # existing tokens
```

Write down: support policy, layer order, token names, how to serve the built site locally. If any is
missing, use the defaults in the agent file and say so in the report.

## 1. Support-policy decision procedure

For each feature you are about to use:

1. Look it up in `references/baseline-2026-10.md` (or query web-features / webstatus.dev).
2. Status at or above the policy level → use it.
3. Below the policy: does the page still work and read correctly without it?
   - Yes (cosmetic: `text-wrap: pretty`, view transitions, exit animations, `scrollbar-color`) →
     use it unguarded; note it in the report.
   - Partly (layout or positioning depends on it) → put it inside `@supports` with a working default
     outside.
   - No (functionality depends on it) → choose another approach, or a small fallback script loaded
     only when `CSS.supports()`/feature detection fails. Add a polyfill only if the repo allows them.
4. Allow-list the deliberate exception in `plugin/use-baseline` / `css/use-baseline` options.

## 2. HTML catalog

| # | Rule | Check |
|---|---|---|
| H1 | Doctype, `lang`, `charset` in first 1024 bytes, viewport without zoom limits, unique `<title>` | html-validate `document` preset; vnu |
| H2 | One `<main>`; labelled duplicate landmarks; no skipped heading levels | html-validate `heading-level`, `unique-landmark`; axe `landmark-*`, `heading-order` |
| H3 | `<a href>` navigates, `<button type>` acts; no click handlers on non-interactive elements | html-validate `prefer-button`, `prefer-native-element`; `@html-eslint` rules |
| H4 | ARIA only where no native element exists, with the APG keyboard pattern | html-validate `no-redundant-role`, `aria-label-misuse`; axe `aria-*` |
| H5 | `<dialog>` + `showModal()` for modals, `popover` for non-modal overlays, `<details name>` for exclusive disclosure | review |
| H6 | Images: `alt`, `width`/`height`, `srcset`/`sizes`, AVIF/WebP via `<picture>`; decorative SVG `aria-hidden="true"` | html-validate `wcag/h37`; Lighthouse `image-delivery-insight` |
| H7 | Tables: `<caption>`, `<th scope>`, no layout tables | html-validate `prefer-tbody`; axe `th-has-data-cells` |
| H8 | Media: captions (`<track kind="captions">`), no unmuted autoplay, controls keyboard-operable | html-validate `no-autoplay` |
| H9 | `<iframe>` has `title`, `sandbox` (minimum tokens), `loading="lazy"` below the fold | axe `frame-title`; review |
| H10 | Third-party `<script>`/`<link>` carry `integrity` + `crossorigin`; inline script/style carry a nonce under CSP | html-validate `require-sri`, `require-csp-nonce` |
| H11 | IDs unique; `for`/`aria-*` references resolve | html-validate `valid-id`, `valid-for`, `no-dup-id` |
| H12 | Web components: autonomous custom elements with a hyphenated name; declarative shadow DOM (Widely since 2026-08) for SSR; form-associated elements use `ElementInternals` | review |

## 3. Forms catalog

- Label: visible `<label>`; placeholder is a hint, never the label. Required fields marked in text
  (not color alone) and with `required`.
- Types and tokens: `type="email|tel|url|number|date"`, `inputmode` for numeric text,
  `autocomplete` from the HTML token list (`given-name`, `email`, `street-address`, `postal-code`,
  `cc-number`, `one-time-code`, `current-password`, `new-password`). html-validate checks tokens with
  `valid-autocomplete`.
- Validation timing: style with `:user-invalid` (Widely) so errors appear after the user interacts;
  on submit, show all errors, put a summary at the top for long forms, and focus the first invalid
  field. Link messages with `aria-describedby`; announce async results through a polite live region.
- WCAG 2.2 additions: 3.3.7 Redundant Entry (do not ask twice for data already given in the same
  process; prefill or offer "same as billing"), 3.3.8 Accessible Authentication (allow paste and
  password managers; no cognitive puzzle without an alternative).
- Size: `field-sizing: content` (Newly, 2026-06) for auto-growing inputs; set `min-block-size` and
  `max-block-size` so it neither collapses nor grows unbounded.
- Selects: native `<select>` by default. Customizable select (`appearance: base-select`) is Limited
  (Chrome 135, Safari 27); opt in under `@supports (appearance: base-select)` and keep `<option>`
  text meaningful because it is the fallback.
- Submit buttons stay enabled until submission starts; then show progress and keep the label.

## 4. Accessibility checklist (WCAG 2.2 AA)

Automated (axe with `wcag2a, wcag2aa, wcag21a, wcag21aa, wcag22aa` tags) plus these manual checks:

| SC | What to verify by hand |
|---|---|
| 1.1.1 | Alt text says what the image means in context; decorative images silent |
| 1.3.1 / 1.3.2 | Structure in markup, not just visuals; DOM order equals visual order (grid/flex `order` and `reading-flow` do not fix screen-reader order everywhere) |
| 1.4.3 / 1.4.11 | Text 4.5:1 (large 3:1); UI parts and focus indicator 3:1, including hover/disabled states you keep operable |
| 1.4.4 / 1.4.10 | 200% text zoom without loss; 320 px wide / 400% zoom without 2-D scrolling |
| 1.4.12 | Text spacing override (line-height 1.5, paragraph 2×, letter 0.12em, word 0.16em) does not clip |
| 1.4.13 | Hover/focus content dismissible with Esc, hoverable, persistent |
| 2.1.1 / 2.1.2 | Everything works by keyboard; no traps (except a modal `<dialog>` which releases on close) |
| 2.4.3 / 2.4.7 | Focus order logical; focus always visible |
| 2.4.11 (new in 2.2) | Focused element not fully hidden by sticky headers, cookie bars or chat widgets |
| 2.5.7 (new) | Every drag has a single-pointer alternative |
| 2.5.8 (new) | Targets at least 24×24 CSS px or spaced so a 24 px circle does not overlap another target |
| 3.2.6 (new) | Help mechanisms appear in the same relative order on every page |
| 3.3.7 / 3.3.8 (new) | See Forms |
| 4.1.2 | Every control has a name, role and state exposed (check in the browser accessibility tree) |
| 4.1.3 | Status messages announced without moving focus (`role="status"`, `aria-live="polite"`) |

Also test forced-colors mode (`forced-colors: active`): focus rings use `outline`, icons use
`currentColor`, and anything drawn with `background-image` or `box-shadow` alone has a fallback.

## 5. CSS architecture catalog

- **Layers:** one `@layer` order statement; vendor CSS imported into a layer; utilities last.
  Unlayered styles beat all layered ones, so keep page CSS inside layers too.
- **Tokens:** primitives (`--blue-60`) feed semantic tokens (`--color-accent`); components read only
  semantic tokens. Themes swap semantic tokens, not component rules.
- **Selectors:** component root class + element/state selectors; state via attributes
  (`[aria-expanded="true"]`, `[data-state="open"]`, `:open`) rather than extra classes, so the
  accessible state and the visual state cannot drift apart.
- **Scoping:** `@scope (.card) to (.card__slot) { … }` (Newly 2026-03) limits reach without BEM
  ceremony; under a Widely policy keep BEM-style class prefixes as the fallback.
- **Nesting:** native nesting (Widely 2026-06) up to three levels; `&` for compound selectors.
- **Container queries:** `container: card / inline-size` on the wrapper; component rules use
  `@container card (width >= 30rem)`; size with `cqi` units inside. Style queries
  (`@container style(--variant: compact)`) are Newly (2026-05).
- **Parent/state selection:** `:has()` (Widely) for "form has an invalid field", "card has an image",
  `body:has(dialog[open])` to lock scroll. Keep `:has()` arguments simple; complex `:has()` on large
  DOMs costs style recalculation.
- **Tailwind 4 projects:** tokens live in `@theme { … }` in CSS; extend with `@utility`/`@variant`
  rather than arbitrary values repeated in markup; the same accessibility and Baseline rules apply to
  the generated CSS.
- **Sass:** use `@use`/`@forward` (the module system), never `@import`; prefer native custom
  properties for anything that must change at runtime.

## 6. Layout recipes

```css
/* Content grid with full-bleed breakouts */
.page { display: grid; grid-template-columns: [full-start] minmax(1rem, 1fr) [content-start] min(65ch, 100% - 2rem) [content-end] minmax(1rem, 1fr) [full-end]; }
.page > * { grid-column: content; }
.page > .full-bleed { grid-column: full; }

/* Intrinsic card grid, no breakpoints */
.cards { display: grid; gap: var(--space-4); grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr)); }

/* Cards whose header/body/footer rows line up across the row */
.cards > .card { display: grid; grid-row: span 3; grid-template-rows: subgrid; }

/* Sidebar that wraps when there is no room */
.with-sidebar { display: flex; flex-wrap: wrap; gap: var(--space-4); }
.with-sidebar > :first-child { flex-basis: 16rem; flex-grow: 1; }
.with-sidebar > :last-child { flex-basis: 0; flex-grow: 999; min-inline-size: 60%; }
```

## 7. Component recipes

**Popover anchored to its trigger (enhancement):**

```html
<button popovertarget="menu" type="button">Options</button>
<div id="menu" popover><button type="button">Rename</button><button type="button">Delete</button></div>
```
```css
@supports (position-area: block-end) {
  #menu { margin: 0; margin-block-start: 0.5rem; position-area: block-end span-inline-end;
          position-try-fallbacks: flip-block, flip-inline; }
}
```
Without support the popover opens centered; a popover shown from script needs
`showPopover({ source: button })` to get an implicit anchor.

**Dialog with entry animation:**

```css
dialog { opacity: 0; transition: opacity .2s, display .2s allow-discrete, overlay .2s allow-discrete; }
dialog[open] { opacity: 1; }
@starting-style { dialog[open] { opacity: 0; } }
dialog::backdrop { background: oklch(0% 0 0 / 40%); }
body:has(dialog[open]) { overflow: hidden; }
```

**Accordion:** `<details name="faq"><summary>…</summary>…</details>`. Height animation needs
`::details-content` (Newly: Chrome 131, Firefox 143, Safari 18.4) together with
`interpolate-size: allow-keywords` (Chromium only), so outside Chromium the panel opens instantly;
that is the accepted fallback.

**Visually hidden text (for icon buttons without a visible label):**

```css
.visually-hidden:not(:focus, :active) {
  clip-path: inset(50%); block-size: 1px; inline-size: 1px; overflow: hidden;
  position: absolute; white-space: nowrap;
}
```
Prefer `aria-label` on the button when there is no visible text at all; use the class when the text
should also be translatable and selectable.

## 8. Motion

- Durations 150–300 ms for UI feedback; easing that matches direction (ease-out for entering,
  ease-in for leaving). Define them once as tokens.
- Only `transform`, `opacity`, `filter`, `clip-path` and the individual `translate`/`scale`/`rotate`
  properties animate on the compositor; layout properties trigger layout every frame.
- Movement inside `@media (prefers-reduced-motion: no-preference)`; fades may stay.
- Scroll-driven effects: `@supports (animation-timeline: view()) { … }`, with content fully visible
  and readable when unsupported (no initial `opacity: 0` outside the `@supports`).
- View transitions: give unique `view-transition-name`s only to elements that should morph;
  duplicate names on the page abort the transition. `view-transition-class` (Newly) styles groups
  of them.

## 9. Performance catalog

Diagnose in this order: field data (CrUX via Chrome DevTools MCP trace summary, or the project's
`web-vitals` RUM) → lab trace → the insight for the failing metric → code.

| Symptom | Usual cause | Fix |
|---|---|---|
| Slow LCP, image | LCP image lazy-loaded, discovered late (CSS background), oversized | `<img>` in HTML, `fetchpriority="high"`, right-sized `srcset`, AVIF/WebP |
| Slow LCP, text | Render-blocking CSS chain or font block | Remove `@import` chains, split route CSS, `font-display: swap`, preload one font |
| CLS | Images/embeds without size, injected banners, font swap | `width`/`height` or `aspect-ratio`, reserve slots, fallback font metrics (`size-adjust`) |
| Poor INP from style work | Large DOM, expensive selectors, layout thrash in handlers | `content-visibility: auto`, simpler selectors, batch reads then writes, CSS for hover/open states |
| Heavy CSS | Unused framework CSS, duplicated tokens | Coverage report, purge via build, one token source |

Images: one `srcset` ladder (for example 480/768/1200/1600 w) with `sizes` that matches the layout.
Fonts: subset, WOFF2, at most two preloaded files. Third parties: load after interaction or with
`loading="lazy"` facades you build yourself (Lighthouse 13 removed its `third-party-facades` audit,
so do not expect it to flag them).

## 10. Security catalog

- CSP target (the same string as agent rule 39): `default-src 'self'; script-src 'nonce-{random}' 'strict-dynamic'; style-src 'self' 'nonce-{random}'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'; form-action 'self'`, then
  `require-trusted-types-for 'script'` once sinks are clean. Report-only first
  (`Content-Security-Policy-Report-Only` + `report-to`), enforce after a clean week.
- Markup blockers to remove: inline `on*=` handlers, `javascript:` URLs, inline `style=""` under a
  nonce-only `style-src` (html-validate `no-inline-style` already flags these).
- HTML sinks: `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `srcdoc`,
  `Range.createContextualFragment`. Use `textContent` for text; DOMPurify for rich HTML; feature-detect
  `Element.prototype.setHTML`.
- CSS injection: never build `style` strings or `url()` values from user input; a custom property
  set from user data must be validated (for example a color via `CSS.supports('color', value)`).
- Embeds: `<iframe sandbox="allow-scripts allow-same-origin">` only when both are truly needed (that
  pair lets the frame remove its own sandbox when same-origin); add `referrerpolicy` and an `allow`
  permissions list.
- Links: `rel="noopener"` is implied by `target="_blank"` in current browsers; add `noreferrer` for
  privacy and `rel="nofollow ugc"` on user-generated links.

## 11. Gate commands (copy into the report with real output)

```sh
npx prettier --check "**/*.{html,css,scss}"
npx stylelint "**/*.{css,scss}" --max-warnings 0          # or: npx eslint "**/*.css"
npm run build
npx html-validate "dist/**/*.html"
npx --package=vnu-jar vnu --errors-only --skip-non-html dist/   # needs Java
npx playwright test                                       # chromium + firefox + webkit, axe inside
npx linkinator ./dist --recurse
npx lighthouse@13.6.0 http://localhost:4173/ --only-categories=performance,accessibility,best-practices,seo \
  --output=json --output-path=./lh.json --chrome-flags="--headless" --quiet
# "No usable sandbox!" / "waiting for dynamic debugging port": --chrome-flags="--headless --no-sandbox"
```

Reading failures:
- Stylelint `plugin/use-baseline` / `css/use-baseline`: decide per section 1; never silence globally.
- html-validate `element-permitted-content`: invalid nesting (block inside `<p>`, interactive inside
  `<a>`/`<button>`); fix the markup, because browsers repair it differently.
- axe `color-contrast` with "incomplete" results (gradients, images behind text) needs a manual
  check; do not report incomplete as pass.
- Playwright differs between engines: reproduce in that engine with the Playwright MCP before
  changing CSS; check the Baseline table for a partial implementation first.
- Lighthouse variance: run three times and use the median; a single-run regression under 5 points is
  noise unless the trace shows a cause.

## 12. Review checklist (for your own diff or a reviewer subagent)

- [ ] Native elements used; every interactive element reachable and operable by keyboard.
- [ ] Every new control has a name, role and state; images have correct `alt`.
- [ ] Focus visible, not obscured, returns to the trigger when overlays close.
- [ ] Works at 320 px, 400% zoom, forced colors, reduced motion, dark scheme.
- [ ] New CSS sits in the right layer, reads semantic tokens, uses logical properties.
- [ ] Each feature newer than the support policy is guarded or harmless; lint allow-list updated.
- [ ] No layout-property animation; no `transition: all`.
- [ ] LCP element not lazy; images sized; no new render-blocking resource.
- [ ] No HTML/CSS injection sink with untrusted data; CSP-compatible markup; SRI on third-party.
- [ ] All gates in section 11 pasted with real output.

## 13. Debugging quick map

| Symptom | First thing to check |
|---|---|
| Element overflows its grid/flex parent | `min-width: auto` on the child; add `min-width: 0` or `minmax(0, 1fr)` |
| `position: sticky` does nothing | An ancestor with `overflow: hidden/auto`; use `overflow: clip` or move the scroller |
| `z-index` ignored | A new stacking context on an ancestor (`transform`, `filter`, `opacity < 1`, `isolation`) or the element is not positioned; top-layer (`dialog`, `popover`) avoids the fight |
| Style not applying | Cascade layer order (unlayered beats layered), specificity, or an invalid value dropped at parse time (check DevTools computed styles / `get_css_styles`) |
| Rule ignored in one browser only | One unsupported selector in a selector list voids the rule; split it |
| Page jumps when a modal opens | Scrollbar disappearing; `scrollbar-gutter: stable` on the scroller |
| 100vh content hidden under mobile toolbars | Use `svb`/`dvb` (logical `svh`/`dvh`) |
| Focus lost after closing a custom overlay | Not using `<dialog>`/`popover`, or the trigger was re-rendered; restore focus explicitly |
| CSP errors in console after a change | Inline handler or un-nonced inline style/script introduced |
