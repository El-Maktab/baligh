import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { ThemeProvider } from "../../design-system";
import { RulesPage } from "./RulesPage";

function renderPage() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <RulesPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("RulesPage", () => {
  it("filters rules and updates the result count", () => {
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "الإملاء" }));

    expect(screen.getByText("3 قواعد")).toBeVisible();
    expect(screen.getByText("الألف المقصورة في «على»")).toBeInTheDocument();
    expect(screen.queryByText("اسم إنّ وأخواتها")).not.toBeInTheDocument();
  });

  it("does not expose detector metadata in rule cards", () => {
    renderPage();

    expect(
      screen.queryByRole("button", { name: "التفاصيل التقنية" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("SY_LAM_JUSSIVE")).not.toBeInTheDocument();
  });
});
