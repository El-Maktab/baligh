import "@fontsource-variable/alexandria";
import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./app/App";
import {
  resolveEditorDataSource,
  resolveMo3gmDataSource,
  resolveRulesDataSource,
} from "./app/environment";
import { createAppQueryClient } from "./app/queryClient";
import { ThemeProvider } from "./design-system";
import { createEditorApi, EditorApiProvider } from "./features/editor/api";
import { createMo3gmApi, Mo3gmApiProvider } from "./features/mo3gm/api";
import { createRulesApi, RulesApiProvider } from "./features/rules/api";
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
const mo3gmDataSource = resolveMo3gmDataSource(
  import.meta.env.VITE_MO3GM_DATA_SOURCE,
  import.meta.env.VITE_API_BASE_URL,
);
const mo3gmApi = createMo3gmApi(
  import.meta.env.VITE_API_BASE_URL,
  mo3gmDataSource,
);
const rulesDataSource = resolveRulesDataSource(
  import.meta.env.VITE_RULES_DATA_SOURCE,
  import.meta.env.VITE_API_BASE_URL,
);
const rulesApi = createRulesApi(
  import.meta.env.VITE_API_BASE_URL,
  rulesDataSource,
);

if (!root) {
  throw new Error("Unable to find the application root");
}

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <EditorApiProvider api={editorApi}>
        <Mo3gmApiProvider api={mo3gmApi}>
          <RulesApiProvider api={rulesApi}>
            <ThemeProvider>
              <App />
            </ThemeProvider>
          </RulesApiProvider>
        </Mo3gmApiProvider>
      </EditorApiProvider>
    </QueryClientProvider>
  </StrictMode>,
);
