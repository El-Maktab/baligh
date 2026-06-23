import { createContext } from "react";

export type ThemePreference = "light" | "dark";
export type ResolvedTheme = ThemePreference;

export type ThemeContextValue = {
  preference: ThemePreference;
  resolvedTheme: ResolvedTheme;
  setPreference: (preference: ThemePreference) => void;
};

export const ThemeContext = createContext<ThemeContextValue | null>(null);
