// Design tokens — mirror the existing Tailwind dark palette as named constants.
// Non-visual refactor + extension point for light mode later.

export const dark = {
  dark950: "#0a0a0a",
  dark900: "#111111",
  dark800: "#1a1a1a",
  dark700: "#2a2a2a",
  dark600: "#404040",
  dark500: "#606060",
  dark400: "#808080",
  dark300: "#a0a0a0",
  dark200: "#c0c0c0",
  dark100: "#e0e0e0",
  dark50: "#f0f0f0",
} as const;

export const primary = {
  primary400: "#60a5fa",
  primary600: "#2563eb",
} as const;

export const semantic = {
  bg: "#0a0a0a",
  surface: "#111111",
  border: "#2a2a2a",
  textPrimary: "#ffffff",
  textMuted: "#808080",
  accent: "#3b82f6",
} as const;

export const tokens = { dark, primary, semantic } as const;
export type Tokens = typeof tokens;
