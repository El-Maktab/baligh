import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { createAppQueryClient } from "../../app/queryClient";
import { createMockRulesApi, RulesApiProvider } from "./api";
import { useRulesController } from "./useRulesController";

function TestHarness() {
  const controller = useRulesController();

  return (
    <div>
      <span data-testid="visible-count">{controller.visibleRules.length}</span>
      <span data-testid="first-title">
        {controller.visibleRules[0]?.title ?? ""}
      </span>
      <button
        onClick={() => controller.setCategory("orthography")}
        type="button"
      >
        filter-orthography
      </button>
      <button onClick={() => controller.setQuery("مؤخرًا")} type="button">
        search-semantic
      </button>
    </div>
  );
}

function renderHarness() {
  return render(
    <QueryClientProvider client={createAppQueryClient()}>
      <RulesApiProvider api={createMockRulesApi()}>
        <TestHarness />
      </RulesApiProvider>
    </QueryClientProvider>,
  );
}

describe("useRulesController", () => {
  it("hydrates the rules catalog from the API", async () => {
    renderHarness();

    await waitFor(() => {
      expect(screen.getByTestId("visible-count")).toHaveTextContent("8");
      expect(screen.getByTestId("first-title")).toHaveTextContent(
        "جزم المضارع بعد «لم»",
      );
    });
  });

  it("filters by category", async () => {
    renderHarness();

    await waitFor(() => {
      expect(screen.getByTestId("visible-count")).toHaveTextContent("8");
    });

    fireEvent.click(screen.getByText("filter-orthography"));

    expect(screen.getByTestId("visible-count")).toHaveTextContent("3");
    expect(screen.getByTestId("first-title")).toHaveTextContent(
      "الألف المقصورة في «على»",
    );
  });

  it("filters by search query", async () => {
    renderHarness();

    await waitFor(() => {
      expect(screen.getByTestId("visible-count")).toHaveTextContent("8");
    });

    fireEvent.click(screen.getByText("search-semantic"));

    expect(screen.getByTestId("visible-count")).toHaveTextContent("1");
    expect(screen.getByTestId("first-title")).toHaveTextContent(
      "بدائل «مؤخرًا» الزمنية",
    );
  });
});
