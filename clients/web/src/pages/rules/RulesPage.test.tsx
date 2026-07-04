import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { createAppQueryClient } from "../../app/queryClient";
import { ThemeProvider } from "../../design-system";
import {
  createMockRulesApi,
  RulesApiProvider,
  type RulesApi,
} from "../../features/rules/api";
import { RulesPage } from "./RulesPage";

function renderPage(
  api: RulesApi = {
    ...createMockRulesApi(),
  },
) {
  return render(
    <QueryClientProvider client={createAppQueryClient()}>
      <RulesApiProvider api={api}>
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

  it("shows punctuation as its own filter when the catalog includes it", async () => {
    renderPage();

    await screen.findByRole("button", { name: "الترقيم" });
    fireEvent.click(screen.getByRole("button", { name: "الترقيم" }));

    await waitFor(() => {
      expect(screen.getByText("1 قاعدة")).toBeVisible();
      expect(
        screen.getByText("اتصال علامات الترقيم بما قبلها"),
      ).toBeInTheDocument();
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

  it("hides empty rule fields when the API omits examples and notes", async () => {
    renderPage({
      listRules: () =>
        Promise.resolve([
          {
            id: "SY_LAM_JUSSIVE",
            category: "syntax",
            subtype: "jussive_operator",
            tier: "tier_1_rule_derived",
            title: "الفعل المضارع بعد «لم» يجب أن يكون مجزومًا.",
            explanation: "",
            incorrect: "",
            correct: "",
            note: "",
          },
        ]),
      listCategories: () => Promise.resolve([{ value: "all", label: "الكل" }]),
    });

    await screen.findByText("الفعل المضارع بعد «لم» يجب أن يكون مجزومًا.");

    expect(screen.queryByText("تجنّب")).not.toBeInTheDocument();
    expect(screen.queryByText("الصواب")).not.toBeInTheDocument();
  });
});
