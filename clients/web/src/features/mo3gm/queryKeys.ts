export const mo3gmQueryKeys = {
  bootstrap: ["mo3gm", "bootstrap"] as const,
  search: (query: string) => ["mo3gm", "search", query] as const,
};
