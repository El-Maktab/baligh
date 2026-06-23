import { useEffect, useState, type ReactNode } from "react";

import {
  ThemeContext,
  type ResolvedTheme,
  type ThemePreference,
} from "./theme-context";

const STORAGE_KEY = "baligh-theme";
function readStoredPreference(): ThemePreference {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === "dark" ? "dark" : "light";
  } catch {
    return "light";
  }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] =
    useState<ThemePreference>(readStoredPreference);
  const resolvedTheme: ResolvedTheme = preference;

  useEffect(() => {
    document.documentElement.dataset.theme = preference;
    document.documentElement.style.colorScheme = preference;
  }, [preference]);

  const setPreference = (nextPreference: ThemePreference) => {
    setPreferenceState(nextPreference);
    try {
      localStorage.setItem(STORAGE_KEY, nextPreference);
    } catch {
      // Theme state remains functional when storage is unavailable.
    }
  };

  return (
    <ThemeContext value={{ preference, resolvedTheme, setPreference }}>
      {children}
    </ThemeContext>
  );
}
