export type ApiDataSource = "mock" | "api" | "auto";
export type EditorDataSource = ApiDataSource;
export type Mo3gmDataSource = ApiDataSource;
export type RulesDataSource = ApiDataSource;

export function isShowcaseEnabled(isDevelopment: boolean, flag?: string) {
  return isDevelopment || flag === "true";
}

export function resolveApiDataSource(
  mode?: string,
  baseUrl?: string,
): ApiDataSource {
  if (mode === "mock" || mode === "api" || mode === "auto") {
    return mode;
  }

  return baseUrl ? "auto" : "mock";
}

export const resolveEditorDataSource = resolveApiDataSource;
export const resolveMo3gmDataSource = resolveApiDataSource;
export const resolveRulesDataSource = resolveApiDataSource;
