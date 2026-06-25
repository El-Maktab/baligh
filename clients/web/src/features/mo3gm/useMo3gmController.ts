import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { useMo3gmApi } from "./api";
import { updateRecentSearches } from "./mockData";
import { mo3gmQueryKeys } from "./queryKeys";
import type { DictionaryEntry } from "./types";

export function useMo3gmController() {
  const api = useMo3gmApi();
  const bootstrapQuery = useQuery({
    queryKey: mo3gmQueryKeys.bootstrap,
    queryFn: ({ signal }) => api.getBootstrap(signal),
  });
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [entry, setEntry] = useState<DictionaryEntry | undefined>();
  const [recent, setRecent] = useState<string[]>([]);

  useEffect(() => {
    if (!bootstrapQuery.data) return;
    setQuery((current) => current || bootstrapQuery.data.initialQuery);
    setSubmittedQuery((current) => current || bootstrapQuery.data.initialQuery);
    setEntry((current) => current ?? bootstrapQuery.data.featuredEntry);
    setRecent((current) =>
      current.length > 0 ? current : bootstrapQuery.data.recentSearches,
    );
  }, [bootstrapQuery.data]);

  const searchMutation = useMutation({
    mutationFn: ({
      value,
      signal,
    }: {
      value: string;
      signal?: AbortSignal;
    }) => api.searchEntry({ query: value }, signal),
    onSuccess: (result) => {
      setSubmittedQuery(result.query);
      const entry = result.entry;
      setEntry(entry);
      if (entry) {
        setRecent((items) => updateRecentSearches(items, entry.word));
      }
    },
  });

  const submitSearch = (value = query) => {
    searchMutation.mutate({ value });
  };

  return {
    query,
    setQuery,
    submittedQuery,
    entry,
    recent,
    submitSearch,
    isHydrating: bootstrapQuery.isPending,
    isSearching: searchMutation.isPending,
  };
}
