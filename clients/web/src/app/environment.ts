export type EditorDataSource = "mock" | "api" | "auto";

export function isShowcaseEnabled(isDevelopment: boolean, flag?: string) {
  return isDevelopment || flag === "true";
}

export function resolveEditorDataSource(
  mode?: string,
  baseUrl?: string,
): EditorDataSource {
  if (mode === "mock" || mode === "api" || mode === "auto") {
    return mode;
  }

  return baseUrl ? "auto" : "mock";
}
