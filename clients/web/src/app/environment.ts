export function isShowcaseEnabled(isDevelopment: boolean, flag?: string) {
  return isDevelopment || flag === "true";
}
