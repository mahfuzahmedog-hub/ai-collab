# ADR 0003 — Design Tokens & Theming

## Status
Accepted (M1)

## Context
The UI is dark-only with hard-coded Tailwind shades (`dark-950`, `primary-600`, etc.). The AIOS design system needs dark/light/system themes without a rewrite.

## Decision
- Add `frontend/src/design/tokens.ts` exporting named tokens (palette + semantic: bg, surface, border, textPrimary, textMuted, accent).
- Add matching CSS variables to `globals.css` under `:root`/`.dark`, mapped to the **existing** hex values so appearance is unchanged (pure refactor / extension point).
- Ship dark first. Light/system themes become a token/variable swap later; components can migrate from literal Tailwind shades to `rgb(var(--…))` incrementally.

## Consequences
- No visual change in M1.
- Light mode later requires defining a light token set + a theme toggle, not a component rewrite.
- Follow-up (non-blocking): wire the CSS variables into `tailwind.config` so utility classes consume tokens.
