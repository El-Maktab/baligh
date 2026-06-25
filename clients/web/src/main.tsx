import "@fontsource-variable/alexandria";
import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./app/App";
import { resolveEditorDataSource } from "./app/environment";
import { createAppQueryClient } from "./app/queryClient";
import { ThemeProvider } from "./design-system";
import { createEditorApi, EditorApiProvider } from "./features/editor/api";
import "./styles/app.css";

const root = document.getElementById("root");
const queryClient = createAppQueryClient();
const editorDataSource = resolveEditorDataSource(
  import.meta.env.VITE_EDITOR_DATA_SOURCE,
  import.meta.env.VITE_API_BASE_URL,
);
const editorApi = createEditorApi(
  import.meta.env.VITE_API_BASE_URL,
  editorDataSource,
);

if (!root) {
  throw new Error("Unable to find the application root");
}

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <EditorApiProvider api={editorApi}>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </EditorApiProvider>
    </QueryClientProvider>
  </StrictMode>,
);
