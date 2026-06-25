/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_EDITOR_DATA_SOURCE?: "mock" | "api" | "auto";
  readonly VITE_MO3GM_DATA_SOURCE?: "mock" | "api" | "auto";
  readonly VITE_RULES_DATA_SOURCE?: "mock" | "api" | "auto";
  readonly VITE_SHOWCASE_ENABLED?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
