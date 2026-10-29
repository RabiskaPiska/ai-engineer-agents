# Config templates (checked against tool docs and run on 2026-10-29)

Copy what the project lacks; merge into what it has. Versions are the current stable releases on
2026-10-29 (see `sources/web.md`). `vite.config.js`, both CSS lint configs, `.htmlvalidate.json` and
the entry stylesheet skeleton were run together on 2026-10-29 against a Vite 8.3.5 build: the
`fmt:check`, `lint:css`, ESLint, `build` and `lint:html` steps exited 0, twice (the second time with
`dist/` present). The Playwright tests and the `links` step were not part of that run; the
Playwright and Lighthouse snippets were checked against their docs, and Lighthouse was run once with
the flags below. The output is in `sources/web.md`.

## package.json (scripts and targets)

```jsonc
{
  "type": "module",
  "browserslist": ["baseline widely available"],      // browserslist >= 4.25 Baseline query
  "scripts": {
    "build": "vite build",
    "preview": "vite preview",                         // serves dist/ on http://localhost:4173
    "fmt:check": "prettier --check \"**/*.{html,css,scss}\"",   // skips files in .gitignore (dist/)
    "lint:css": "stylelint \"**/*.{css,scss}\" --max-warnings 0",
    "lint:html": "html-validate \"dist/**/*.html\"",
    "test": "playwright test",
    "links": "linkinator ./dist --recurse",
    "gate": "npm run fmt:check && npm run lint:css && npm run build && npm run lint:html && npm test && npm run links"
  },
  "devDependencies": {
    "@axe-core/playwright": "4.14.0",
    "@playwright/test": "1.64.1",
    "browserslist": "4.29.5",                          // read by vite.config.js below
    "html-validate": "11.17.0",
    "linkinator": "8.1.0",
    "prettier": "3.9.10",
    "stylelint": "17.16.0",
    "stylelint-config-standard": "40.0.0",
    "stylelint-plugin-use-baseline": "1.4.8",
    "vite": "8.3.5"
  }
}
```

Other Baseline queries browserslist understands: `baseline newly available`,
`baseline widely available on 2026-01-01`, `baseline 2024`, and `… with downstream` for
Chromium/Gecko-based browsers outside the core set. Pin exact versions for reproducible gates and
update them deliberately. Keep `dist/` and `node_modules/` in `.gitignore`: Prettier 3 skips ignored
files, and both lint configs below ignore `dist/` themselves, so a leftover build never fails the gate.

## vite.config.js (one source of browser targets)

Vite does not read `browserslist`. Its default `build.target: 'baseline-widely-available'` is a
snapshot frozen at "Baseline Widely available on 2025-05-01" (`chrome111`, `edge111`, `firefox114`,
`safari16.4`, `ios16.4`; Vite bumps it only in a major release), while
`browserslist "baseline widely available"` resolves on 2026-10-29 to Chrome/Edge 124+, Firefox 125+
and Safari/iOS 17.4+. The Lightning CSS minifier takes its targets from `build.cssTarget`, which
defaults to `build.target`; it overrides `css.lightningcss.targets`. Derive `build.target` from
browserslist so JS, CSS and the lint `available` level describe the same browsers:

```js
import browserslist from "browserslist";
import { defineConfig } from "vite";

// One source of targets: the oldest browserslist version per engine, as esbuild-style strings.
const engines = {
  chrome: "chrome",
  edge: "edge",
  firefox: "firefox",
  safari: "safari",
  ios_saf: "ios",
};
const oldest = {};
for (const entry of browserslist()) {
  const [name, range] = entry.split(" ");
  const engine = engines[name];
  const version = range.split("-")[0];
  const [major, minor = 0] = version.split(".").map(Number);
  const rank = major * 1000 + minor;
  if (engine && !(oldest[engine]?.rank <= rank))
    oldest[engine] = { rank, version };
}
const target = Object.entries(oldest).map(
  ([engine, { version }]) => engine + version,
);

export default defineConfig({
  // build.cssTarget defaults to build.target and is what the Lightning CSS minifier reads.
  build: { target },
});
```

Measured with a nested rule `.card { & .title { … } }`: the default build flattened it to
`.card .title{…}`; with this config (`["chrome124","edge124","firefox125","ios17.4","safari17.4"]`)
the nesting was kept. Setting only `css.lightningcss.targets = browserslistToTargets(browserslist())`
did not change the minified output, with or without `css.transformer: "lightningcss"`; that option
affects only the Lightning CSS transform step, so add it as well when you use that transformer.

## stylelint.config.js (Stylelint 17 is ESM-only, Node >= 20.19)

```js
/** @type {import("stylelint").Config} */
export default {
  extends: ["stylelint-config-standard"],
  plugins: ["stylelint-plugin-use-baseline"],
  ignoreFiles: ["dist/**", "**/vendor/**"], // build output and third-party CSS
  rules: {
    // "widely" | "newly" | <year>; match the project's support policy.
    // Each allow-listed feature is Newly available and degrades harmlessly (see SKILL section 1).
    "plugin/use-baseline": [
      true,
      {
        available: "widely",
        ignoreFunctions: ["light-dark"],
        ignoreProperties: { "text-wrap": ["balance"] },
      },
    ],
    "declaration-no-important": true,
    "selector-max-id": 0,
  },
};
```

Allow-list a Newly feature only when it degrades harmlessly (SKILL section 1), and name it here so
the rule still catches everything else: `text-wrap: pretty` and `!important` still fail with this
config. Stylelint 17 changed `fix` to `strict` (no autofix when the file has a syntax error) and counts
nested selectors and `:is()/:where()/:has()` per the specs, so `selector-max-*` limits written for
16.x may need raising. Keep `--max-warnings 0` in CI.

## eslint.config.js (ESLint 10 + @eslint/css 2.x, alternative to Stylelint)

```js
import { defineConfig, globalIgnores } from "eslint/config";
import css from "@eslint/css";

export default defineConfig([
  globalIgnores(["dist/", "**/vendor/"]), // build output and third-party CSS
  {
    files: ["**/*.css"],
    language: "css/css",
    plugins: { css },
    extends: ["css/recommended"], // includes use-baseline, no-invalid-properties, no-important
    rules: {
      "css/use-baseline": [
        "error",
        {
          available: "widely",
          allowFunctions: ["light-dark"],
          allowPropertyValues: { "text-wrap": ["balance"] },
        },
      ],
      // tokens are defined in another file, so let var() of an unknown property pass
      "css/no-invalid-properties": ["error", { allowUnknownVariables: true }],
      "css/prefer-logical-properties": "error", // wants svb/dvb, not svh/dvh
      "css/relative-font-units": "error",
      "css/use-layers": "error",
    },
  },
]);
```

Allow a deliberately used newer feature instead of disabling the rule (`allowAtRules: ["scope"]`,
`allowProperties: ["field-sizing"]`, `allowFunctions`, `allowPropertyValues`, `allowUnits`), and
wrap the usage in `@supports` where it matters. Two defaults that break a normal project:
`css/no-invalid-properties` reports `var(--token)` when the token is defined in another file
(hence `allowUnknownVariables`), and `css/prefer-logical-properties` reports `vh`/`svh`/`dvh` and
`vw` (write `vb`/`svb`/`dvb` and `vi`, the logical units, which equal `vh`/`vw` in horizontal
writing modes; both linters accept them under the Widely policy).

## .htmlvalidate.json

```json
{
  "extends": [
    "html-validate:recommended",
    "html-validate:document",
    "html-validate:prettier"
  ],
  "rules": {
    "require-sri": ["error", { "target": "crossorigin" }],
    "require-csp-nonce": "error"
  }
}
```

`recommended` already includes `prefer-native-element`, `no-inline-style`, WCAG rules and standards
validation. `require-sri` and `require-csp-nonce` are off by default. `require-sri` defaults to
`target: "all"`, which also flags Vite's own same-origin `/assets/*.js` and `/assets/*.css` tags;
`target: "crossorigin"` limits it to absolute URLs (`https://…`, `//…`), that is, third-party
resources, and still fails a CDN `<script>` without `integrity`. `html-validate:prettier` turns off
`doctype-style`, `void-style` and `attr-quotes`, which otherwise reject the lowercase
`<!doctype html>` of agent rule 1 and the `<meta />` Prettier writes. Measured on a Vite 8.3.5
build: the two-preset config with `"require-sri": "error"` exited 1 (doctype-style, void-style ×4,
require-sri ×2); this config exited 0. Node `^22.22.0 || >=24.8.0` is required by html-validate 11.

## playwright.config.ts

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "tests",
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  use: { baseURL: "http://localhost:4173", trace: "on-first-retry" },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
    { name: "mobile-webkit", use: { ...devices["iPhone 15"] } },
  ],
  webServer: {
    command: "npm run build && npm run preview",
    url: "http://localhost:4173",
    reuseExistingServer: !process.env.CI,
  },
});
```

Device names change between Playwright releases; list the installed ones with
`node -e "console.log(Object.keys(require('@playwright/test').devices).join('\n'))"` if a name is rejected.

## tests/a11y.spec.ts (axe + keyboard + preference modes + reflow)

```ts
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const WCAG22AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

test("home has no automatically detectable WCAG 2.2 AA violations", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page }).withTags(WCAG22AA).analyze();
  expect(results.violations).toEqual([]);
});

test("dialog state is accessible and traps focus", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Open settings" }).click();
  const dialog = page.getByRole("dialog", { name: "Settings" });
  await expect(dialog).toBeVisible();
  const results = await new AxeBuilder({ page }).include("dialog").withTags(WCAG22AA).analyze();
  expect(results.violations).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(page.getByRole("button", { name: "Open settings" })).toBeFocused();
});

test("skip link is first and moves focus to main", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: /skip to (main )?content/i });
  await expect(skip).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("main")).toBeInViewport();
});

for (const mode of [
  { reducedMotion: "reduce" },
  { colorScheme: "dark" },
  { forcedColors: "active" },
] as const) {
  test(`renders without violations under ${JSON.stringify(mode)}`, async ({ page }) => {
    await page.emulateMedia(mode);
    await page.goto("/");
    const results = await new AxeBuilder({ page }).withTags(WCAG22AA).analyze();
    expect(results.violations).toEqual([]);
  });
}

test("no horizontal overflow at 320 CSS px (WCAG 1.4.10)", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 640 });
  await page.goto("/");
  const overflows = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(overflows).toBe(false);
});
```

axe finds a subset of WCAG failures. Keep the manual checks (screen reader names, zoom 400%,
reading order, meaningful alt text) in the report.

## Lighthouse 13 gate (CLI, then a Node assertion)

```sh
npx lighthouse@13.6.0 http://localhost:4173/ \
  --only-categories=performance,accessibility,best-practices,seo \
  --output=json --output-path=./lh.json --chrome-flags="--headless" --quiet
node -e '
const r = require("./lh.json");
const min = { performance: 0.9, accessibility: 1, "best-practices": 0.95, seo: 0.9 };
let ok = true;
for (const [k, v] of Object.entries(min)) {
  const s = r.categories[k].score;
  console.log(k, s);
  if (s < v) ok = false;
}
process.exit(ok ? 0 : 1);
'
```

On Linux hosts that block unprivileged user namespaces (the AppArmor default on Ubuntu 23.10+;
check `cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns` → `1`) and in most containers,
Chrome aborts with `No usable sandbox!` and Lighthouse fails with
`waiting for dynamic debugging port`. Add `--no-sandbox` there, and only for pages you trust (your
own build): `--chrome-flags="--headless --no-sandbox"`. Playwright's Chromium needs no flag because
Playwright launches it with the sandbox off by default. Run three times and gate on the median. Lighthouse 13 removed the legacy performance audits in favour
of insight audits (`cls-culprits-insight`, `document-latency-insight`, `image-delivery-insight`, …);
scripts that read old audit IDs such as `layout-shifts` or `uses-long-cache-ttl` must be updated.
`@lhci/cli` 0.15.1 still bundles Lighthouse 12.6.1, so its audit IDs differ from the 13.x CLI.

## Nu Html Checker (stricter conformance than html-validate)

```sh
npx --package=vnu-jar vnu --errors-only --skip-non-html dist/
```

Needs a `java` command. If none is present, `vnu-jar`'s postinstall downloads a local JRE into
`node_modules/.cache/vnu-jar/java/`; in locked-down CI install Java explicitly instead.

## Entry stylesheet skeleton

Passes Prettier, the Stylelint config and the ESLint config above as written.

```css
@layer reset, tokens, base, layouts, components, utilities, overrides;

@import url("vendor/some-widget.css") layer(components.vendor);

@layer tokens {
  :root {
    color-scheme: light dark;

    /* light-dark() is Newly available; allow-listed in both lint configs because an older
       browser still gets readable system colors from color-scheme. */
    --color-bg: light-dark(oklch(99% 0.005 250deg), oklch(18% 0.01 250deg));
    --color-fg: light-dark(oklch(22% 0.02 250deg), oklch(94% 0.01 250deg));
    --color-accent: oklch(55% 0.18 255deg);
    --color-accent-hover: color-mix(in oklch, var(--color-accent), black 15%);
    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-4: 1rem;
    --step-0: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
    --step-2: clamp(1.5rem, 1.3rem + 1vw, 2.25rem);
    --focus-ring: 2px solid var(--color-accent);
  }
}

@layer reset {
  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }

  body {
    margin: 0;
    min-block-size: 100svb; /* svb = svh in horizontal writing modes */
  }

  img,
  svg,
  video {
    display: block;
    max-inline-size: 100%;
    block-size: auto;
  }

  input,
  textarea,
  select,
  button {
    font: inherit;
  }
}

@layer base {
  html {
    scroll-padding-block-start: 5rem; /* clears a sticky header (WCAG 2.4.11) */
  }

  body {
    background: var(--color-bg);
    color: var(--color-fg);
    font-size: var(--step-0);
  }

  :where(h1, h2, h3) {
    text-wrap: balance; /* Newly; allow-listed: unsupported browsers wrap normally */
  }

  :focus-visible {
    outline: var(--focus-ring);
    outline-offset: 2px;
  }

  @media (prefers-reduced-motion: no-preference) {
    html {
      scroll-behavior: smooth; /* motion is opt-in, never opt-out */
    }
  }
}

@layer utilities {
  .visually-hidden:not(:focus, :active) {
    position: absolute;
    overflow: hidden;
    clip-path: inset(50%);
    block-size: 1px;
    inline-size: 1px;
    white-space: nowrap;
  }

  .flow-none {
    display: none !important; /* stylelint-disable-line declaration-no-important -- must beat components */ /* eslint-disable-line css/no-important -- must beat components */
  }
}
```

Components follow the same pattern: fades may run for everyone, movement goes inside
`@media (prefers-reduced-motion: no-preference)`. `!important` appears only in the utilities or
overrides layer, each time with an inline disable and a reason, as in `.flow-none` above; both
comments sit on the declaration's line so that one linter's comment does not consume the other's
`disable-next-line`. A project that runs only one of the two linters keeps only its comment.
