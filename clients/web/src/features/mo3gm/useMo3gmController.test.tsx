import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { createAppQueryClient } from "../../app/queryClient";
import { createMockMo3gmApi, Mo3gmApiProvider } from "./api";
import { useMo3gmController } from "./useMo3gmController";

function TestHarness() {
  const controller = useMo3gmController();

  return (
    <div>
      <span data-testid="query">{controller.query}</span>
      <span data-testid="entry-word">{controller.entry?.word ?? ""}</span>
      <span data-testid="submitted-query">{controller.submittedQuery}</span>
      <span data-testid="recent-first">{controller.recent[0] ?? ""}</span>
      <button onClick={() => controller.submitSearch("استنبط")} type="button">
        submit-query
      </button>
      <button
        onClick={() => controller.submitSearch("كلمة مجهولة")}
        type="button"
      >
        submit-miss
      </button>
    </div>
  );
}

function renderHarness() {
  return render(
    <QueryClientProvider client={createAppQueryClient()}>
      <Mo3gmApiProvider api={createMockMo3gmApi()}>
        <TestHarness />
      </Mo3gmApiProvider>
    </QueryClientProvider>,
  );
}

describe("useMo3gmController", () => {
  it("hydrates the featured entry and recent searches from the API", async () => {
    renderHarness();

    await waitFor(() => {
      expect(screen.getByTestId("query")).toHaveTextContent("بليغ");
      expect(screen.getByTestId("entry-word")).toHaveTextContent("بليغ");
      expect(screen.getByTestId("recent-first")).toHaveTextContent("بليغ");
    });
  });

  it("searches entries and moves a successful hit to the top of recents", async () => {
    renderHarness();

    fireEvent.click(screen.getByText("submit-query"));

    await waitFor(() => {
      expect(screen.getByTestId("entry-word")).toHaveTextContent("استنبط");
      expect(screen.getByTestId("submitted-query")).toHaveTextContent("استنبط");
      expect(screen.getByTestId("recent-first")).toHaveTextContent("استنبط");
    });
  });

  it("keeps the submitted query when no entry matches", async () => {
    renderHarness();

    fireEvent.click(screen.getByText("submit-miss"));

    await waitFor(() => {
      expect(screen.getByTestId("submitted-query")).toHaveTextContent(
        "كلمة مجهولة",
      );
      expect(screen.getByTestId("entry-word")).toHaveTextContent("");
    });
  });
});
