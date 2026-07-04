import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeAll, describe, expect, it, vi } from "vitest";

import { createAppQueryClient } from "../../app/queryClient";
import { ThemeProvider } from "../../design-system/theme/ThemeProvider";
import {
  createMockEditorApi,
  EditorApiProvider,
} from "../../features/editor/api";
import { EditorPage } from "./EditorPage";

function renderPage() {
  const queryClient = createAppQueryClient();

  return render(
    <MemoryRouter>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <EditorApiProvider api={createMockEditorApi()}>
            <EditorPage />
          </EditorApiProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </MemoryRouter>,
  );
}

describe("EditorPage", () => {
  beforeAll(() => {
    Element.prototype.scrollIntoView = vi.fn();
  });

  it("renders detection-only findings without a fake accept action", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByDisplayValue("عن المحبة")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /نحو/i }));
    fireEvent.click(screen.getByText("رصد نحوي"));

    await waitFor(() => {
      expect(screen.getByText("رصد نحوي")).toBeInTheDocument();
      expect(screen.getByText("رصد فقط")).toBeInTheDocument();
      expect(screen.getByText("النص المرصود:")).toBeInTheDocument();
    });

    expect(
      screen.queryByRole("button", { name: "قبول" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "إخفاء" })).toBeInTheDocument();
  });

  it("keeps corrective findings actionable with accept and ignore controls", async () => {
    const view = renderPage();

    await waitFor(() => {
      expect(screen.getByDisplayValue("عن المحبة")).toBeInTheDocument();
    });

    const correctionHighlight = view.container.querySelector(
      '[data-correction-id="correction-1"]',
    );
    expect(correctionHighlight).not.toBeNull();
    fireEvent.click(correctionHighlight!);

    await waitFor(() => {
      expect(screen.getByText("ضبط الفعل")).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "قبول" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "تجاهل" })).toBeInTheDocument();
  });
});
