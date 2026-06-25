import { QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { createAppQueryClient } from "../../app/queryClient";
import {
  createMockEditorApi,
  EditorApiError,
  EditorApiProvider,
  type EditorApi,
} from "./api";
import { useEditorController } from "./useEditorController";

function TestHarness() {
  const controller = useEditorController();

  return (
    <div>
      <span data-testid="draft-count">{controller.drafts.length}</span>
      <span data-testid="active-title">{controller.activeDraft?.title ?? ""}</span>
      <span data-testid="active-body">{controller.activeDraft?.body ?? ""}</span>
      <span data-testid="save-state">{controller.saveState}</span>
      <span data-testid="suggestion-open">
        {String(controller.suggestionState.isOpen)}
      </span>
      <span data-testid="suggestion-mode">{controller.suggestionState.mode ?? ""}</span>
      <span data-testid="highlighted-index">
        {controller.suggestionState.highlightedIndex}
      </span>
      <button onClick={() => controller.updateTitle("عنوان جديد")} type="button">
        edit-title
      </button>
      <button onClick={() => controller.updateBody("الم")} type="button">
        word-body
      </button>
      <button onClick={() => controller.updateSelection([3, 3])} type="button">
        caret-3
      </button>
      <button onClick={() => controller.cycleSuggestion(1)} type="button">
        cycle-next
      </button>
      <button onClick={() => controller.applySuggestion()} type="button">
        apply-suggestion
      </button>
      <button onClick={() => controller.closeSuggestions()} type="button">
        close-suggestions
      </button>
    </div>
  );
}

function renderHarness(api: EditorApi) {
  const queryClient = createAppQueryClient();

  return render(
    <QueryClientProvider client={queryClient}>
      <EditorApiProvider api={api}>
        <TestHarness />
      </EditorApiProvider>
    </QueryClientProvider>,
  );
}

describe("useEditorController", () => {
  it("hydrates the draft list and active draft from the API", async () => {
    renderHarness(createMockEditorApi());

    await waitFor(() => {
      expect(screen.getByTestId("draft-count")).toHaveTextContent("2");
      expect(screen.getByTestId("active-title")).toHaveTextContent("عن المحبة");
    });
  });

  it("debounces autosave and reaches the saved state", async () => {
    renderHarness(createMockEditorApi());

    await screen.findByText("edit-title");
    await waitFor(() => {
      expect(screen.getByTestId("active-title")).toHaveTextContent("عن المحبة");
    });

    fireEvent.click(screen.getByText("edit-title"));
    expect(screen.getByTestId("save-state")).toHaveTextContent("idle");

    await waitFor(
      () => {
        expect(screen.getByTestId("save-state")).toHaveTextContent("saved");
      },
      { timeout: 2_500 },
    );
  });

  it("loads word suggestions, cycles them, applies one, and can close the menu", async () => {
    renderHarness(createMockEditorApi());

    await waitFor(() => {
      expect(screen.getByTestId("active-title")).toHaveTextContent("عن المحبة");
    });

    fireEvent.click(screen.getByText("word-body"));
    fireEvent.click(screen.getByText("caret-3"));

    await waitFor(
      () => {
        expect(screen.getByTestId("suggestion-open")).toHaveTextContent("true");
      },
      { timeout: 1_500 },
    );
    expect(screen.getByTestId("suggestion-mode")).toHaveTextContent("word");

    fireEvent.click(screen.getByText("cycle-next"));
    expect(screen.getByTestId("highlighted-index")).toHaveTextContent("1");

    fireEvent.click(screen.getByText("apply-suggestion"));
    expect(screen.getByTestId("active-body").textContent).not.toBe("الم");

    fireEvent.click(screen.getByText("close-suggestions"));
    expect(screen.getByTestId("suggestion-open")).toHaveTextContent("false");
  });

  it("recovers from a 409 save conflict by hydrating the latest server draft", async () => {
    const baseApi = createMockEditorApi();
    const conflictApi: EditorApi = {
      ...baseApi,
      updateDraft: async (draftId) => {
        const latestDraft = await baseApi.getDraft(draftId);
        throw new EditorApiError("Revision conflict", 409, {
          latestDraft: {
            ...latestDraft,
            title: "عنوان من الخادم",
          },
        });
      },
    };

    renderHarness(conflictApi);

    await waitFor(() => {
      expect(screen.getByTestId("active-title")).toHaveTextContent("عن المحبة");
    });

    fireEvent.click(screen.getByText("edit-title"));

    await waitFor(
      () => {
        expect(screen.getByTestId("save-state")).toHaveTextContent("error");
      },
      { timeout: 2_500 },
    );
    expect(screen.getByTestId("active-title")).toHaveTextContent("عنوان من الخادم");
  });
});
