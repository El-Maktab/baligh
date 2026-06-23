import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Button } from "react-aria-components";
import { describe, expect, it } from "vitest";

import { ThemeProvider } from "./ThemeProvider";
import { useTheme } from "./useTheme";

function ThemeProbe() {
  const { preference, resolvedTheme, setPreference } = useTheme();

  return (
    <div>
      <output aria-label="preference">{preference}</output>
      <output aria-label="resolved theme">{resolvedTheme}</output>
      <Button onPress={() => setPreference("dark")}>dark</Button>
      <Button onPress={() => setPreference("light")}>light</Button>
    </div>
  );
}

describe("ThemeProvider", () => {
  it("uses light mode when no override is stored", async () => {
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>,
    );

    expect(screen.getByLabelText("preference")).toHaveTextContent("light");
    expect(screen.getByLabelText("resolved theme")).toHaveTextContent("light");
    await waitFor(() =>
      expect(document.documentElement).toHaveAttribute("data-theme", "light"),
    );
  });

  it("persists explicit light and dark choices", () => {
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "dark" }));
    expect(localStorage.getItem("baligh-theme")).toBe("dark");
    expect(screen.getByLabelText("resolved theme")).toHaveTextContent("dark");

    fireEvent.click(screen.getByRole("button", { name: "light" }));
    expect(localStorage.getItem("baligh-theme")).toBe("light");
    expect(screen.getByLabelText("resolved theme")).toHaveTextContent("light");
  });
});
