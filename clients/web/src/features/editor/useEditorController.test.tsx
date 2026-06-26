import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { createAppQueryClient } from "../../app/queryClient";
import {
  createMockEditorApi,
  EditorApiError,
  EditorApiProvider,
  type EditorApi,
} from "./api";
import { DEFAULT_DRAFT_BODY, DEFAULT_DRAFT_TITLE } from "./mockData";
import { useEditorController } from "./useEditorController";

function TestHarness() {
  const controller = useEditorController();

  return (
    <div>
      <span data-testid="draft-count">{controller.drafts.length}</span>
      <span data-testid="active-title">
        {controller.activeDraft?.title ?? ""}
      </span>
      <span data-testid="active-body">
        {controller.activeDraft?.body ?? ""}
      </span>
      <span data-testid="correction-count">
        {controller.activeDraft?.corrections.length ?? 0}
      </span>
      <span data-testid="first-correction-status">
        {controller.activeDraft?.corrections[0]?.status ?? ""}
      </span>
      <span data-testid="save-state">{controller.saveState}</span>
      <span data-testid="suggestion-open">
        {String(controller.suggestionState.isOpen)}
      </span>
      <span data-testid="suggestion-mode">
        {controller.suggestionState.mode ?? ""}
      </span>
      <span data-testid="highlighted-index">
        {controller.suggestionState.highlightedIndex}
      </span>
      <button
        onClick={() => controller.updateTitle("عنوان جديد")}
        type="button"
      >
        edit-title
      </button>
      <button onClick={() => controller.addDraft()} type="button">
        add-draft
      </button>
      <button onClick={() => controller.updateBody("الم")} type="button">
        word-body
      </button>
      <button onClick={() => controller.updateBody("مرحبا ")} type="button">
        sentence-body-space
      </button>
      <button onClick={() => controller.updateSelection([3, 3])} type="button">
        caret-3
      </button>
      <button onClick={() => controller.updateSelection([6, 6])} type="button">
        caret-6
      </button>
      <button
        onClick={() => controller.updateSelection([0, 5])}
        type="button"
      >
        select-0-5
      </button>
      <button onClick={() => controller.toggleStrong([0, 5])} type="button">
        toggle-strong
      </button>
      <button onClick={() => controller.cycleSuggestion(1)} type="button">
        cycle-next
      </button>
      <button onClick={() => controller.applySuggestion()} type="button">
        apply-suggestion
      </button>
      <button
        onClick={() => controller.acceptCorrection("correction-1")}
        type="button"
      >
        accept-correction
      </button>
      <button
        onClick={() => controller.ignoreCorrection("correction-1")}
        type="button"
      >
        ignore-correction
      </button>
      <button onClick={() => controller.closeSuggestions()} type="button">
        close-suggestions
      </button>
      <button onClick={() => controller.applyTashkeel()} type="button">
        apply-tashkeel
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

  it("can create and activate a draft when the API starts empty", async () => {
    renderHarness(createMockEditorApi([]));

    await waitFor(() => {
      expect(screen.getByTestId("draft-count")).toHaveTextContent("0");
      expect(screen.getByTestId("active-title")).toHaveTextContent("");
    });

    fireEvent.click(screen.getByText("add-draft"));

    await waitFor(() => {
      expect(screen.getByTestId("draft-count")).toHaveTextContent("1");
      expect(screen.getByTestId("active-title")).toHaveTextContent(
        DEFAULT_DRAFT_TITLE,
      );
      expect(screen.getByTestId("active-body")).toHaveTextContent(
        DEFAULT_DRAFT_BODY,
      );
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

  it("creates a draft with the default title and body", async () => {
    let createPayload: { title?: string; body?: string } | null = null;
    const baseApi = createMockEditorApi();
    const capturingApi: EditorApi = {
      ...baseApi,
      createDraft: async (payload, signal) => {
        createPayload = payload;
        return baseApi.createDraft(payload, signal);
      },
    };

    renderHarness(capturingApi);

    await waitFor(() => {
      expect(screen.getByTestId("active-title")).toHaveTextContent("عن المحبة");
    });

    fireEvent.click(screen.getByText("add-draft"));

    await waitFor(() => {
      expect(screen.getByTestId("active-title")).toHaveTextContent(
        DEFAULT_DRAFT_TITLE,
      );
      expect(screen.getByTestId("active-body")).toHaveTextContent(
        DEFAULT_DRAFT_BODY,
      );
    });

    expect(createPayload).toEqual({
      title: DEFAULT_DRAFT_TITLE,
      body: DEFAULT_DRAFT_BODY,
    });
  });

  it("includes formatting in the draft save payload", async () => {
    let updatePayload:
      | {
          title?: string;
          body?: string;
          formatting?: unknown;
          clientRevision: number;
        }
      | null = null;
    const baseApi = createMockEditorApi();
    const capturingApi: EditorApi = {
      ...baseApi,
      updateDraft: async (draftId, payload, signal) => {
        updatePayload = payload;
        return baseApi.updateDraft(draftId, payload, signal);
      },
    };

    renderHarness(capturingApi);

    await waitFor(() => {
      expect(screen.getByTestId("active-title")).toHaveTextContent("عن المحبة");
    });

    fireEvent.click(screen.getByText("toggle-strong"));

    await waitFor(
      () => {
        expect(screen.getByTestId("save-state")).toHaveTextContent("saved");
      },
      { timeout: 2_500 },
    );

    expect(updatePayload).toMatchObject({
      formatting: {
        strong: [[0, 5]],
      },
    });
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

  it("requests sentence suggestions after typing a trailing space", async () => {
    renderHarness(createMockEditorApi());

    await waitFor(() => {
      expect(screen.getByTestId("active-title")).toHaveTextContent("عن المحبة");
    });

    fireEvent.click(screen.getByText("sentence-body-space"));
    fireEvent.click(screen.getByText("caret-6"));

    await waitFor(
      () => {
        expect(screen.getByTestId("suggestion-open")).toHaveTextContent("true");
      },
      { timeout: 1_500 },
    );
    expect(screen.getByTestId("suggestion-mode")).toHaveTextContent(
      "sentence",
    );
  });

  it("starts tashkeel before any queued analyze request", async () => {
    const callOrder: string[] = [];
    const baseApi = createMockEditorApi();
    const tracingApi: EditorApi = {
      ...baseApi,
      analyzeDraft: async (draftId, payload, signal) => {
        callOrder.push("analyze");
        return baseApi.analyzeDraft(draftId, payload, signal);
      },
      applyTashkeel: async (draftId, payload, signal) => {
        callOrder.push("tashkeel");
        return baseApi.applyTashkeel(draftId, payload, signal);
      },
    };

    renderHarness(tracingApi);

    await waitFor(() => {
      expect(screen.getByTestId("active-title")).toHaveTextContent("عن المحبة");
    });

    fireEvent.click(screen.getByText("word-body"));
    fireEvent.click(screen.getByText("apply-tashkeel"));

    await waitFor(() => {
      expect(callOrder[0]).toBe("tashkeel");
    });
  });

  it("accepts a correction and hydrates the returned body and statuses", async () => {
    renderHarness(createMockEditorApi());

    await waitFor(() => {
      expect(screen.getByTestId("active-title")).toHaveTextContent("عن المحبة");
    });

    fireEvent.click(screen.getByText("accept-correction"));

    await waitFor(() => {
      expect(screen.getByTestId("active-body")).toHaveTextContent("وترفّق");
      expect(screen.getByTestId("first-correction-status")).toHaveTextContent(
        "accepted",
      );
    });
  });

  it("ignores a correction and keeps the returned correction list in sync", async () => {
    renderHarness(createMockEditorApi());

    await waitFor(() => {
      expect(screen.getByTestId("active-title")).toHaveTextContent("عن المحبة");
    });

    fireEvent.click(screen.getByText("ignore-correction"));

    await waitFor(() => {
      expect(screen.getByTestId("first-correction-status")).toHaveTextContent(
        "ignored",
      );
    });
  });

  it("rebases on a 409 save conflict without overwriting local editor text", async () => {
    const baseApi = createMockEditorApi();
    let attempts = 0;
    const conflictApi: EditorApi = {
      ...baseApi,
      updateDraft: async (draftId, payload) => {
        attempts += 1;
        const latestDraft = await baseApi.getDraft(draftId);
        if (attempts === 1) {
          throw new EditorApiError("Revision conflict", 409, {
            latestDraft: {
              ...latestDraft,
              title: "عنوان من الخادم",
              revision: latestDraft.revision + 1,
            },
          });
        }
        return {
          draft: {
            ...latestDraft,
            title: payload.title ?? latestDraft.title,
            body: payload.body ?? latestDraft.body,
            revision: payload.clientRevision + 1,
            savedAt: new Date().toISOString(),
          },
          persistedRevision: payload.clientRevision + 1,
          savedAt: new Date().toISOString(),
        };
      },
    };

    renderHarness(conflictApi);

    await waitFor(() => {
      expect(screen.getByTestId("active-title")).toHaveTextContent("عن المحبة");
    });

    fireEvent.click(screen.getByText("edit-title"));

    await waitFor(
      () => {
        expect(screen.getByTestId("save-state")).toHaveTextContent("saved");
      },
      { timeout: 4_000 },
    );
    expect(screen.getByTestId("active-title")).toHaveTextContent("عنوان جديد");
  });

  it("supports nested 409 latestDraft payloads without overwriting local text", async () => {
    const baseApi = createMockEditorApi();
    let attempts = 0;
    const conflictApi: EditorApi = {
      ...baseApi,
      updateDraft: async (draftId, payload) => {
        attempts += 1;
        const latestDraft = await baseApi.getDraft(draftId);
        if (attempts === 1) {
          throw new EditorApiError("Revision conflict", 409, {
            detail: {
              latestDraft: {
                ...latestDraft,
                title: "عنوان متداخل من الخادم",
                revision: latestDraft.revision + 1,
              },
            },
          });
        }
        return {
          draft: {
            ...latestDraft,
            title: payload.title ?? latestDraft.title,
            body: payload.body ?? latestDraft.body,
            revision: payload.clientRevision + 1,
            savedAt: new Date().toISOString(),
          },
          persistedRevision: payload.clientRevision + 1,
          savedAt: new Date().toISOString(),
        };
      },
    };

    renderHarness(conflictApi);

    await waitFor(() => {
      expect(screen.getByTestId("active-title")).toHaveTextContent("عن المحبة");
    });

    fireEvent.click(screen.getByText("edit-title"));

    await waitFor(
      () => {
        expect(screen.getByTestId("save-state")).toHaveTextContent("saved");
      },
      { timeout: 4_000 },
    );
    expect(screen.getByTestId("active-title")).toHaveTextContent("عنوان جديد");
  });
});
