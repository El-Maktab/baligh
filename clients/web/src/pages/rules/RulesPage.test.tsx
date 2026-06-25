import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { createAppQueryClient } from "../../app/queryClient";
import { ThemeProvider } from "../../design-system";
import { createMockRulesApi, RulesApiProvider } from "../../features/rules/api";
import { RulesPage } from "./RulesPage";

function renderPage() {
  return render(
    <QueryClientProvider client={createAppQueryClient()}>
      <RulesApiProvider api={createMockRulesApi()}>
        <ThemeProvider>
          <MemoryRouter>
            <RulesPage />
          </MemoryRouter>
        </ThemeProvider>
      </RulesApiProvider>
    </QueryClientProvider>,
  );
}

describe("RulesPage", () => {
  it("filters rules and updates the result count", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "الإملاء" }));

    await waitFor(() => {
      expect(screen.getByText("3 قواعد")).toBeVisible();
      expect(screen.getByText("الألف المقصورة في «على»")).toBeInTheDocument();
      expect(screen.queryByText("اسم إنّ وأخواتها")).not.toBeInTheDocument();
    });
  });

  it("does not expose detector metadata in rule cards", async () => {
    renderPage();
    await screen.findByRole("button", { name: "الكل" });

    expect(
      screen.queryByRole("button", { name: "التفاصيل التقنية" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("SY_LAM_JUSSIVE")).not.toBeInTheDocument();
  });
});
