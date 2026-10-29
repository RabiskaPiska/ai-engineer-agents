# Sources — web (HTML / CSS, web platform)

Author slug: `web`. Fetch date for every source below: **2026-10-29** unless stated. Files covered:

- `claude/agents/web-engineer.md`
- `skills/web-engineering/SKILL.md`
- `skills/web-engineering/references/baseline-2026-10.md`
- `skills/web-engineering/references/configs.md`

Mined repositories were read as text through the GitHub contents API only. No code, install step or
script from them was executed. Text from MIT/Apache-2.0 repos was paraphrased and adapted; nothing
was copied verbatim beyond short rule names.

## The 5 GitHub repositories used

Each was verified with `ghapi.sh repos/<owner>/<repo>` on 2026-10-29. The JSON line is the exact
subset of fields used.

### 1. GoogleChrome/modern-web-guidance

```json
{"full_name": "GoogleChrome/modern-web-guidance", "html_url": "https://github.com/GoogleChrome/modern-web-guidance", "stargazers_count": 2573, "pushed_at": "2026-10-26T15:27:53Z", "license": "Apache-2.0", "archived": false}
```

Read: `skills/modern-web-guidance/SKILL.md` and the guide index under
`skills/modern-web-guidance/guides/` (accessibility, css, forms, html, performance, security,
ui-behaviors, ui-components, visual-design). Took:
- The default support policy "Baseline Widely available without fallback; follow the guide's
  fallback otherwise; a project policy can override", which became the agent's default policy and
  the skill's section 1 decision procedure.
- The search → retrieve → verify workflow of the `modern-web-guidance` CLI (npm 0.0.196,
  Apache-2.0), referenced in "MCP and skills usage".
- The framework-adaptation notes (keep `:root` and `@starting-style` unscoped; per-instance IDs for
  `anchor-name`; call `showModal()` on real DOM nodes).

### 2. vercel-labs/web-interface-guidelines

```json
{"full_name": "vercel-labs/web-interface-guidelines", "html_url": "https://github.com/vercel-labs/web-interface-guidelines", "stargazers_count": 1060, "pushed_at": "2026-10-05T20:49:17Z", "license": "MIT", "archived": false}
```

Read: `AGENTS.md`, `README.md`. Took (paraphrased): keyboard/focus rules (visible
`:focus-visible`, sticky elements never cover focus), target sizes, never disabling zoom, forms rules
(no paste blocking, inline errors, focus first error on submit, `autocomplete` + `name`, keep submit
enabled until the request starts), animation rules (no `transition: all`, compositor-only
properties, honour reduced motion), content-handling rules (long/empty content, `min-width: 0` on
flex children), dark-mode rules (`color-scheme`, `theme-color`). Not adopted: its "prefer APCA over
WCAG 2" contrast rule, because WCAG 2.2 AA (4.5:1 / 3:1) is the conformance and legal target; APCA is
mentioned nowhere as a replacement.

### 3. addyosmani/web-quality-skills

```json
{"full_name": "addyosmani/web-quality-skills", "html_url": "https://github.com/addyosmani/web-quality-skills", "stargazers_count": 3006, "pushed_at": "2026-08-24T21:07:36Z", "license": "MIT", "archived": false}
```

Read: `skills/core-web-vitals/SKILL.md`, `skills/accessibility/SKILL.md`,
`skills/best-practices/SKILL.md`. Took: the measure-first sequence (CrUX p75 → trace → insight for
the failing metric → re-measure; never claim a field improvement from a lab run), the CWV thresholds
(LCP 2.5 s, INP 200 ms, CLS 0.1 at p75), "preload the LCP image only when the trace shows late
discovery", the ~14 KB critical-CSS heuristic, and the speculation-rules caveats (Chromium-only,
side effects fire at prerender time).

### 4. vojtaholik/good-css

```json
{"full_name": "vojtaholik/good-css", "html_url": "https://github.com/vojtaholik/good-css", "stargazers_count": 395, "pushed_at": "2026-10-10T19:57:59Z", "license": "MIT", "archived": false}
```

Read: `README.md`, `AGENTS.md`, `PRACTICES.md` (entries: the reset, logical properties, OKLCH
tokens, content grid with breakouts, intrinsic grid, subgrid, sidebar, `overflow: clip`, focus ring,
enter/exit from `display: none`, popover anchored to trigger, accordion height, "left out on
purpose"). Took: `min-width: 0` and `flex: none` guidance, `svh` vs `dvh` split, `overflow: clip`
over `hidden`, the `@starting-style`/`allow-discrete` pattern and its browser behaviour as tested by
the author in Safari 27 on 2026-10-01 (entry animates, exit snaps), the anchored-popover recipe with
`position-area` + `position-try-fallbacks` under `@supports`, `showPopover({ source })`, and the
rule to keep new pseudo-classes out of shared selector lists. Its Firefox 147 support note for
anchored popovers is quoted with attribution in `references/baseline-2026-10.md`.

### 5. web-platform-dx/web-features

```json
{"full_name": "web-platform-dx/web-features", "html_url": "https://github.com/web-platform-dx/web-features", "stargazers_count": 952, "pushed_at": "2026-10-29T09:13:22Z", "license": "Apache-2.0", "archived": false}
```

Read: the published npm package `web-features@3.44.0` (2026-10-22) `data.json`, parsed with
`python3 -I` (no package code executed). Took: every Baseline status, date and browser version in
the agent's rule 10 and in `references/baseline-2026-10.md` (generated table of about 90 features),
plus browser release data as of this data release (Chrome 156 on 2026-10-20, Edge 155 on 2026-10-08,
Firefox 158 on 2026-10-13, Safari 27 on 2026-09-14). The agent's toolchain table takes Edge from
Microsoft's own release notes instead (Edge 156 on 2026-10-22), because this data lags.

## MCP servers declared in the agent (verified, not counted in the 5)

| Server | Repo JSON (ghapi, 2026-10-29) | Install command source | Notes |
|---|---|---|---|
| chrome-devtools (https://github.com/ChromeDevTools/chrome-devtools-mcp) | `{"full_name": "ChromeDevTools/chrome-devtools-mcp", "stargazers_count": 54397, "pushed_at": "2026-10-29T09:31:38Z", "license": "Apache-2.0", "archived": false}` | README "Getting started": `"command": "npx", "args": ["-y", "chrome-devtools-mcp@latest"]`; flags `--no-usage-statistics`, `--no-performance-crux`, `--isolated`, `--headless`, `--slim` named in README | npm `chrome-devtools-mcp` 1.12.0 (2026-10-22) pinned in the agent with `--headless` (`--help`: `--headless … [default: false]`). Usage statistics are on by default (opted out in the agent config). Tool names taken from `docs/tool-reference.md` (`compare_heapsnapshots` "requires flag: --memoryDebugging=true"). Launch probe on this box: see "Headless and sandbox probes" below. |
| playwright (https://github.com/microsoft/playwright-mcp) | `{"full_name": "microsoft/playwright-mcp", "stargazers_count": 38797, "pushed_at": "2026-10-22T17:43:26Z", "license": "Apache-2.0", "archived": false}` | README: `claude mcp add playwright npx @playwright/mcp@latest`; options table lists `--headless`, `--isolated` | npm `@playwright/mcp` 0.0.83 (2026-09-28) pinned in the agent. |
| context7 (https://github.com/upstash/context7) | `{"full_name": "upstash/context7", "stargazers_count": 63882, "pushed_at": "2026-10-28T20:26:24Z", "license": "MIT", "archived": false}` | README contains `https://mcp.context7.com/mcp` | Spec-mandated server, remote HTTP. |
| github | by-name reference | spec | Already configured in the host. |

Considered and not declared: `dequelabs/axe-mcp-server-public` (official Deque, 9 stars, license
NOASSERTION, pushed 2026-10-21) because its license is unclear and axe already runs inside
Playwright tests; `priyankark/a11y-mcp` (53 stars, MPL-2.0) because axe via Playwright covers the
same checks with better engine coverage.

## Official version and fact sources (fetched 2026-10-29)

| Fact | Source |
|---|---|
| Edge 156.0.4314.42 stable 2026-10-22; 156.0.4314.50 on 2026-10-26; 155.0.4283.45 on 2026-10-08 | https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-stable-channel ("Contents - October 2026" table) |
| Vite 8.3.5 does not read browserslist; `build.target` default `'baseline-widely-available'` → `ESBUILD_BASELINE_WIDELY_AVAILABLE_TARGET` = `chrome111, edge111, firefox114, safari16.4, ios16.4` ("Baseline Widely Available on 2025-05-01", bumped per major); `cssTarget: merged.cssTarget ?? merged.target`; minifyCSS passes `...config.css.lightningcss, targets: convertTargets(config.build.cssTarget)` | `vite@8.3.5` `dist/node/chunks/node.js` (read with grep; `grep -c browserslist` = 0), https://vite.dev/config/build-options |
| browserslist `baseline widely available` → Chrome/Edge 124+, Firefox 125+, Safari/iOS 17.4+ (2026-10-29) | `npx browserslist "baseline widely available"` with browserslist 4.29.5 |
| html-validate `require-sri` default `target: "all"` ("even on same origin"); `crossorigin` = URLs with `protocol://` or `//`; `html-validate:prettier` turns off `attr-quotes`, `doctype-style`, `void-style` | https://html-validate.org/rules/require-sri.html ; `html-validate@11.17.0` `dist/cjs/core.js` (`defaults$7`, `config$2`) |
| `stylelint-plugin-use-baseline` options `ignoreFunctions`, `ignoreProperties`; `@eslint/css` `use-baseline` options `allowFunctions`, `allowPropertyValues`; `no-invalid-properties` option `allowUnknownVariables` | package READMEs / `dist/rules/*.d.ts` and `.js` of the pinned versions |
| Lighthouse legacy DOM-size thresholds (~800 warn, ~1,400 error); 13.x `dom-size-insight` thresholds (40 ms, 300 elements, 100 layout objects); `long-tasks`, `render-blocking-insight`, `forced-reflow-insight` in the default config | https://developer.chrome.com/docs/lighthouse/performance/dom-size ; `lighthouse@13.6.0` `core/config/default-config.js` and bundled `@paulirish/trace_engine/models/trace/insights/DOMSize.js` |
| `blocking-render` Limited (Chrome 105, Safari 18.2); `scheduler` Limited (Chrome 129, Firefox 142); `anchor-positioning` support `{safari: 27, safari_ios: 27}`, `anchor-positioning-animations` Chrome 125 / Safari 26 | `web-features@3.44.0` `data.json`, read with `python3 -I` |
| Chrome "No usable sandbox!" on Ubuntu 23.10+ AppArmor user-namespace restriction | https://chromium.googlesource.com/chromium/src/+/main/docs/security/apparmor-userns-restrictions.md (linked from the Chrome error itself) |
| Chrome 156 stable 2026-10-20; 157 early stable 2026-10-21, stable 2026-11-03 | https://chromiumdash.appspot.com/fetch_milestone_schedule?mstone=157 and `?mstone=156` |
| Bi-weekly Chrome/Firefox releases since Sept 2026; Safari 27 features; Chrome 155/156 betas | https://web.dev/blog/web-platform-09-2026 |
| Firefox 159.0 (2026-10-27), ESR 153.6.0esr, next release 2026-11-06 | https://product-details.mozilla.org/1.0/firefox_versions.json |
| Safari 27.0 (2026-09-14), 27.1 (2026-10-23), 27.2 (2026-10-26); Safari 27 CSS/accessibility features; 27.2 `flow-tolerance` → `fit-tolerance` rename | https://developer.apple.com/documentation/safari-release-notes (JSON index), `safari-27-release-notes`, `safari-27_2-release-notes` |
| Baseline 2026 feature list | https://web.dev/baseline/2026 |
| Interop 2026 focus areas | https://web.dev/blog/interop-2026 |
| Baseline digests (Feb/Apr/Jun/Jul/Aug 2026) | https://web.dev/blog/baseline-digest-aug-2026 and siblings |
| WCAG 2.2 current; WCAG 3.0 Working Draft 2026-09-10 | https://www.w3.org/TR/WCAG22/ , https://www.w3.org/standards/history/wcag-3.0 , https://www.w3.org/WAI/standards-guidelines/wcag/wcag3-intro/ |
| EN 301 549 v4.1.1 (2026-09) adopts WCAG 2.2, not yet cited in OJEU | https://accessible-eu-centre.ec.europa.eu/content-corner/news/european-accessibility-standard-en-301-549-has-been-updated-2026-09-07_en |
| Node.js 24.22.2 LTS (2026-10-27), 26.13.0 first 26.x LTS (2026-10-28) | https://nodejs.org/dist/index.json |
| npm versions, dates, licenses, engines, peer deps (Prettier, Stylelint, configs, ESLint, @eslint/css, @html-eslint, Biome, html-validate, vnu-jar, Playwright, axe, Lighthouse, @lhci/cli → lighthouse 12.6.1, Vite, Lightning CSS, PostCSS, Autoprefixer, Tailwind, Sass, browserslist, web-vitals, DOMPurify, linkinator, modern-web-guidance) | https://registry.npmjs.org/<package> |
| Stylelint 17 breaking changes (ESM-only, Node 20.19, strict fix, nesting-aware rules); 18.0.0-next.0 prerelease | https://stylelint.io/migration-guide/to-17 , https://github.com/stylelint/stylelint/blob/main/CHANGELOG.md |
| `stylelint-plugin-use-baseline` rule name and `available` option | npm README of `stylelint-plugin-use-baseline` (repo ryo-manba/stylelint-plugin-use-baseline) |
| `@eslint/css` rules and `use-baseline` options | https://github.com/eslint/css (README, `docs/rules/use-baseline.md`) |
| Biome HTML formatting experimental, CSS stable | https://biomejs.dev/internals/language-support/ |
| html-validate presets; `require-sri`/`require-csp-nonce` not in `recommended` | https://html-validate.org/rules/presets.html , `src/config/presets/recommended.ts` in html-validate/html-validate |
| vnu CLI options (`--errors-only`, `--skip-non-html`, …) and Java requirement | https://github.com/validator/validator `docs/vnu.1.md`; vnu-jar README |
| axe tags `wcag22aa`, `EN-301-549` | https://github.com/dequelabs/axe-core/blob/develop/doc/API.md |
| Playwright `AxeBuilder.withTags` pattern | https://playwright.dev/docs/accessibility-testing |
| Lighthouse 13: insight audits replace legacy perf audits, removed audits, Node 22.19 | https://developer.chrome.com/blog/lighthouse-13-0 |
| Lighthouse Baseline Features audit | https://developer.chrome.com/docs/lighthouse/best-practices/baseline-features |
| Lighthouse CLI flags | https://github.com/GoogleChrome/lighthouse README |
| Vite 8: Rolldown, Lightning CSS minify default, `baseline-widely-available` = chrome111/edge111/firefox114/safari16.4 | https://vite.dev/guide/migration , https://vite.dev/config/build-options |
| browserslist Baseline queries | https://github.com/browserslist/browserslist README |
| Claude Code subagent fields, nested-subagent depth (3 layers default) | https://code.claude.com/docs/en/sub-agents.md |

## Marked unverified / judgement calls

- Lighthouse score budgets in the agent (accessibility 100, best-practices ≥ 95, performance ≥ 90)
  are a recommended default, not an external standard.
- (Resolved) The device names `Desktop Chrome`, `Desktop Firefox`, `Desktop Safari` and `iPhone 15`
  used in `references/configs.md` exist in Playwright v1.64.1
  (`packages/isomorphic/deviceDescriptorsSource.json`, 207 descriptors).
- (Resolved 2026-10-29) The package.json scripts, `vite.config.js`, both CSS lint configs,
  `.htmlvalidate.json` and the stylesheet skeleton in `references/configs.md` were executed; see
  "Template gate run". The Playwright test file and the `test`/`links` steps of the `gate` script
  were not re-run in that project.
- The 1,400-element DOM budget in agent rule 52 is Lighthouse's old error threshold, used as a
  default; it is not a standard.

## Template gate run (2026-10-29)

Every code block of `references/configs.md` for `stylelint.config.js`, `eslint.config.js`,
`.htmlvalidate.json`, `vite.config.js` and the entry stylesheet was extracted by script into an
empty project (plus an `index.html` with lowercase `<!doctype html>` and `<meta />`, a vendor CSS
stub, and `.gitignore` with `dist/`), with the pinned versions installed. The project's gate also
ran the ESLint config, which the configs.md `gate` script leaves out because ESLint CSS is the
alternative linter. `npm run gate`, first run:

```text
> gate
> npm run fmt:check && npm run lint:css && npm run lint:css:eslint && npm run build && npm run lint:html
> fmt:check
> prettier --check "**/*.{html,css,scss}"
Checking formatting...
All matched files use Prettier code style!
> lint:css
> stylelint "**/*.{css,scss}" --max-warnings 0
> lint:css:eslint
> eslint "**/*.css"
> build
> vite build
vite v8.3.5 building client environment for production...
transforming...
✓ 5 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                 0.89 kB │ gzip: 0.45 kB
dist/assets/index-D6MVLo1e.css  1.46 kB │ gzip: 0.71 kB
dist/assets/index-CmbmF8SN.js   0.86 kB │ gzip: 0.45 kB
✓ built in 137ms
> lint:html
> html-validate "dist/**/*.html"
GATE_EXIT=0
```

A second `npm run gate` with `dist/` present also printed `GATE_EXIT=0`. Before the fix, the same
build gave: the old `.htmlvalidate.json` exited 1 (doctype-style, void-style ×4, require-sri ×2);
the old skeleton gave Stylelint exit 2 (14 problems), ESLint exit 1 (svh, text-wrap), Prettier
exit 1; with `dist/` present the lint globs also failed on the built CSS until the configs ignored
`dist/`. Negative checks with the new configs: a CDN `<script>` without `integrity` → html-validate
exit 1 (`require-sri`); `100svh`, `text-wrap: pretty` and an undisabled `!important` → Stylelint
exit 2 and ESLint exit 1. A component file that reads a token from another file failed ESLint
(`Can't validate with unknown variable '--color-fg'`) until `allowUnknownVariables: true`.

Vite targets, same nested-rule input (`.card { & .title { … } }`): default build →
`.card{color:#00f}.card .title{color:red}`; `build.target` from browserslist
(`["chrome124","edge124","firefox125","ios17.4","safari17.4"]`) →
`.card{color:#00f;& .title{color:red}}`; only `css.lightningcss.targets =
browserslistToTargets(browserslist())`, with or without `css.transformer: "lightningcss"` →
flattened, as in the default build.

## Headless and sandbox probes (2026-10-29, this VPS: no `DISPLAY`, `apparmor_restrict_unprivileged_userns` = 1)

| Command | Result |
|---|---|
| `lighthouse … --chrome-flags="--headless"` (Chromium from the Playwright cache via `CHROME_PATH`) | exit 1, `waiting for dynamic debugging port`; `chrome-err.log`: `No usable sandbox! If you are running on Ubuntu 23.10+ …` |
| same with `--chrome-flags="--headless --no-sandbox"` | exit 0, accessibility score 1 |
| `chrome-devtools-mcp@1.12.0 --headless --isolated --executablePath <chromium>`, MCP `new_page` | `isError: true`, `Protocol error (Target.setDiscoverTargets): Target closed` |
| same plus `--chrome-arg=--no-sandbox` | page opened: `2: Gate test (http://localhost:4173/) [selected]` |
| same without `--headless` (the default) plus `--chrome-arg=--no-sandbox` | `isError: true`, `Missing X server to start the headful browser` |

## Self-check results

Run on 2026-10-29 with `python3 web-selfcheck.py` (PyYAML `yaml.safe_load`, heading scan, and
`ghapi.sh repos/<owner>/<repo>` for every github.com repo linked in the four files). Exit code 0.

```text
yaml.safe_load(claude/agents/web-engineer.md): OK, keys=['name', 'description', 'model', 'skills', 'mcpServers']
  agent fields all valid: True 
  name=web-engineer model=inherit skills=['web-engineering'] tools-omitted=True
  mcpServers=['github', 'context7', 'chrome-devtools', 'playwright']
    context7: type=http url=https://mcp.context7.com/mcp
    chrome-devtools: type=stdio command=npx args=['-y', 'chrome-devtools-mcp@1.12.0', '--headless', '--isolated', '--no-usage-statistics']
    playwright: type=stdio command=npx args=['@playwright/mcp@0.0.83', '--headless', '--isolated']
  line count: 453
yaml.safe_load(skills/web-engineering/SKILL.md): OK, keys=['name', 'description']
  line count: 294
heading check (agent): missing=[] in_spec_order=True
ALL-CAPS directive words in agent+skill: none
ghapi repos/ChromeDevTools/chrome-devtools-mcp: OK pushed_at=2026-10-29T09:31:38Z archived=False
ghapi repos/GoogleChrome/lighthouse: OK pushed_at=2026-10-28T22:28:35Z archived=False
ghapi repos/GoogleChrome/modern-web-guidance: OK pushed_at=2026-10-26T15:27:53Z archived=False
ghapi repos/addyosmani/web-quality-skills: OK pushed_at=2026-08-24T21:07:36Z archived=False
ghapi repos/browserslist/browserslist: OK pushed_at=2026-10-26T18:47:36Z archived=False
ghapi repos/dequelabs/axe-core: OK pushed_at=2026-10-26T14:48:59Z archived=False
ghapi repos/eslint/css: OK pushed_at=2026-10-29T02:08:35Z archived=False
ghapi repos/microsoft/playwright-mcp: OK pushed_at=2026-10-22T17:43:26Z archived=False
ghapi repos/stylelint/stylelint: OK pushed_at=2026-10-29T06:55:28Z archived=False
ghapi repos/upstash/context7: OK pushed_at=2026-10-28T20:26:24Z archived=False
ghapi repos/validator/validator: OK pushed_at=2026-10-12T17:18:55Z archived=False
ghapi repos/vercel-labs/web-interface-guidelines: OK pushed_at=2026-10-05T20:49:17Z archived=False
ghapi repos/vojtaholik/good-css: OK pushed_at=2026-10-10T19:57:59Z archived=False
ghapi repos/web-platform-dx/web-features: OK pushed_at=2026-10-29T09:13:22Z archived=False
```

HTTP check of official non-GitHub URLs (`curl -s -o /dev/null -L -w '%{http_code}'`, 2026-10-29):
all returned 200 (web.dev ×3, product-details.mozilla.org, developer.apple.com, w3.org ×2,
accessible-eu-centre.ec.europa.eu, nodejs.org, stylelint.io, biomejs.dev, html-validate.org,
playwright.dev, developer.chrome.com ×2, vite.dev ×2, code.claude.com, chromiumdash, webstatus.dev;
added in the fix pass: learn.microsoft.com Edge release notes, developer.chrome.com dom-size,
chromium.googlesource.com apparmor-userns-restrictions, html-validate.org require-sri and presets),
except `https://mcp.context7.com/mcp`, which returned 405 to a plain GET. That is expected for an
MCP Streamable HTTP endpoint (it accepts POST); the URL is the one printed in the upstash/context7
README.

Line counts: agent 453 (target 250–500), skill 294 (target 150–400).
