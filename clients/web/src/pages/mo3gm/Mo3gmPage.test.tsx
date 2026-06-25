import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { createAppQueryClient } from "../../app/queryClient";
import { ThemeProvider } from "../../design-system";
import { createMockMo3gmApi, Mo3gmApiProvider } from "../../features/mo3gm/api";
import { Mo3gmPage } from "./Mo3gmPage";

function renderPage() {
  return render(
    <QueryClientProvider client={createAppQueryClient()}>
      <Mo3gmApiProvider api={createMockMo3gmApi()}>
        <ThemeProvider>
          <MemoryRouter>
            <Mo3gmPage />
          </MemoryRouter>
        </ThemeProvider>
      </Mo3gmApiProvider>
    </QueryClientProvider>,
  );
}

describe("Mo3gmPage", () => {
  it("submits from the keyboard and shows an informative empty state", async () => {
    renderPage();
    const input = screen.getByRole("searchbox", { name: "ابحث في المعجم" });
    await waitFor(() => {
      expect(input).toHaveValue("بليغ");
    });

    fireEvent.change(input, { target: { value: "كلمة مجهولة" } });
    fireEvent.submit(input.closest("form")!);

    expect(await screen.findByText(/لم نجد/)).toHaveTextContent("كلمة مجهولة");
  });

  it("selects a recent search and renders its entry", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /استنبط/ }));

    expect(await screen.findByText("اِسْتَنْبَطَ")).toBeInTheDocument();
    expect(screen.getByText("الجذر: ن ب ط")).toBeInTheDocument();
  });
});
