# Design System

All tokens live on `:root` in `assets/template.html`. Components only reference tokens — never hard-code colors.

## Tokens

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#f7f7f8` | `#0d0f12` | Page background |
| `--surface` | `#ffffff` | `#161a1f` | Cards, tables |
| `--surface-2` | `#f0f1f3` | `#1e232a` | Nested panels, code, hover |
| `--border` | `#e2e4e8` | `#2a3038` | Hairlines |
| `--text` | `#14161a` | `#e8eaed` | Body |
| `--muted` | `#5b6270` | `#9aa3af` | Meta, captions |
| `--accent` | `#3b5bdb` | `#7c94ff` | Links, focus, primary emphasis (one only) |
| `--accent-soft` | accent @ 12% | accent @ 18% | Highlight backgrounds |
| `--ok` | `#2b8a3e` | `#51cf66` | Done / good / added |
| `--warn` | `#b35c00` | `#fcc419` | At risk / caution / changed |
| `--bad` | `#c92a2a` | `#ff6b6b` | Blocked / bad / removed |
| `--info` | `#1971c2` | `#4dabf7` | Neutral info |

Status colors each have a `-soft` variant (`--ok-soft`, …) for pill/row backgrounds.

**Chart series** (categorical, distinguishable in both themes and for common color-vision deficiencies): `--c1 #4263eb`, `--c2 #e8590c`, `--c3 #0ca678`, `--c4 #ae3ec9`, `--c5 #f59f00`, `--c6 #1098ad`. Use ≤ 6; beyond that, group into "Other". Always label series directly or with a legend; never rely on color alone.

## Theme: Light / Auto / Dark (standard, required)

Every report ships the same three-way switch. **Auto is the default** and follows the OS (`prefers-color-scheme`) live, including when the OS flips at sunset. Light and Dark override the OS and are remembered.

| Piece | Where (in `assets/template.html`) | What it does |
|---|---|---|
| Tokens | `:root` (light), `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {…} }`, `:root[data-theme="dark"] {…}` | No attribute means the OS decides. `data-theme="light"` or `"dark"` forces a theme. Dark tokens appear twice on purpose. |
| `<meta name="color-scheme" content="light dark">` | `<head>` | Native form controls and scrollbars match |
| Pre-paint script | `<head>`, right after the viewport meta | Applies a saved Light/Dark before first render, so there's no flash |
| Switch markup | Top bar: `<div class="seg theme-switch" role="radiogroup" data-theme-switch>` with `button[data-mode]` (`light`, `auto`, `dark`) | Segmented control. Labels collapse to icons under 640px. Arrow keys move the selection. |
| Logic | Helpers: `getMode()/setMode()` | Auto removes `data-theme`. Light/Dark set it. Saves `localStorage['report-theme']` and fires `report:theme`. |
| API | `R.theme.get()`, `R.theme.set(mode)` (mode: `'light'`, `'dark'`, `'auto'`), `R.theme.isDark()`, `R.onTheme(fn)` | `R.onTheme` fires on the switch **and** on OS changes while in Auto |

Rules:

- Never hard-code colours in CSS, SVG, d3 or three.js. Read tokens (`var(--x)` in CSS, `R.css('--x')` in JS) and redraw or repaint inside `R.onTheme`.
- Inline SVG may use `fill="var(--c1)"` directly. It re-colours without a redraw.
- three.js: materials take `new THREE.Color(R.css('--x'))`. Re-assign them in a `paint()` registered with `R.onTheme`. Use a transparent renderer (`alpha:true`) so the page background shows through.
- The preference key is shared, so every report opened from disk remembers the same choice.
- Check both themes before delivering. The linter fails if the switch or either dark-token block is missing.

## Using tokens in d3 / three.js

Read tokens at draw time: `R.css('--c1')` in d3, `new THREE.Color(R.css('--c1'))` in three. Register the redraw/repaint with `R.onTheme(fn)` so toggling the theme re-colours charts and scenes. Sequential ramps: `d3.interpolateRgb(R.css('--surface-2'), R.css('--c1'))`.

## Typography

- Stack: `system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`. Mono: `ui-monospace, "Cascadia Code", "SF Mono", Menlo, Consolas, monospace`. **No web fonts** (self-containment).
- Scale (rem): `0.8 meta · 0.9 small · 1 body · 1.15 h4 · 1.35 h3 · 1.7 h2 · 2.3 h1 · 2 KPI value`.
- Line height 1.55 body, 1.2 headings. `font-variant-numeric: tabular-nums` on numbers in tables/KPIs.
- Weight: 400 body, 600 headings/labels, 700 KPI values. No italics for emphasis — use weight or accent.

## Spacing & shape

- 4px grid: `--s1 4px · --s2 8px · --s3 12px · --s4 16px · --s5 24px · --s6 32px · --s7 48px`.
- Radius `--r 10px` cards, `6px` controls, `999px` pills.
- Shadow: one level only (`--shadow`) for cards; dark theme uses border instead.
- Container: `max-width: 1180px`, gutter `16px` mobile / `24px` desktop.
- Grid: `repeat(auto-fit, minmax(220px, 1fr))` for tiles/cards — collapses naturally on phones.

## Iconography

Inline SVG or Unicode only. Recommended glyphs: ✓ done, ✕ removed/blocked, ▲ up, ▼ down, ● status dot, ⚠ risk, ? open question, → flow, ⧉ copy. Always accompany status color with a glyph or word.

## Motion

Transitions ≤ 150ms on color/opacity/transform only. Wrap in `@media (prefers-reduced-motion: no-preference)`.
