import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { ThemeProvider } from "../../design-system";
import { Mo3gmPage } from "./Mo3gmPage";

function renderPage() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <Mo3gmPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("Mo3gmPage", () => {
  it("submits from the keyboard and shows an informative empty state", async () => {
    renderPage();
    const input = screen.getByRole("searchbox", { name: "ابحث في المعجم" });

    fireEvent.change(input, { target: { value: "كلمة مجهولة" } });
    fireEvent.submit(input.closest("form")!);

    expect(await screen.findByText(/لم نجد/)).toHaveTextContent("كلمة مجهولة");
  });

  it("selects a recent search and renders its entry", async () => {
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: /استنبط/ }));

    expect(
      await screen.findByRole("heading", { name: "اِسْتَنْبَطَ" }),
    ).toBeInTheDocument();
    expect(screen.getByText("الجذر: ن ب ط")).toBeInTheDocument();
  });
});
