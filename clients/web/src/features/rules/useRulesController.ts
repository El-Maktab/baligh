import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { useRulesApi } from "./api";
import { filterGrammarRules } from "./mockData";
import { rulesQueryKeys } from "./queryKeys";
import type { RuleCategory } from "./types";

export function useRulesController() {
  const api = useRulesApi();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<"all" | RuleCategory>("all");

  const rulesQuery = useQuery({
    queryKey: rulesQueryKeys.rules,
    queryFn: ({ signal }) => api.listRules(signal),
  });
  const categoriesQuery = useQuery({
    queryKey: rulesQueryKeys.categories,
    queryFn: ({ signal }) => api.listCategories(signal),
  });

  const rules = rulesQuery.data ?? [];
  const visibleRules = filterGrammarRules(rules, query, category);

  return {
    query,
    setQuery,
    category,
    setCategory,
    rules,
    visibleRules,
    categories: categoriesQuery.data ?? [],
    isHydrating: rulesQuery.isPending || categoriesQuery.isPending,
  };
}
