/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, type PropsWithChildren } from "react";

import { type ApiDataSource } from "../../app/environment";
import { rulesContract } from "./contract";
import { grammarRules, ruleCategories } from "./mockData";
import type { GrammarRule, RuleCategoryOption } from "./types";

export class RulesApiError extends Error {
  status: number;
  payload?: unknown;

  constructor(message: string, status: number, payload?: unknown) {
    super(message);
    this.name = "RulesApiError";
    this.status = status;
    this.payload = payload;
  }
}

export type RulesApi = {
  listRules: (signal?: AbortSignal) => Promise<GrammarRule[]>;
  listCategories: (signal?: AbortSignal) => Promise<RuleCategoryOption[]>;
};

const RulesApiContext = createContext<RulesApi | null>(null);

function delay(signal?: AbortSignal, ms = 10) {
  return new Promise<void>((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("The request was aborted", "AbortError"));
      return;
    }
    const timeoutId = window.setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        window.clearTimeout(timeoutId);
        reject(new DOMException("The request was aborted", "AbortError"));
      },
      { once: true },
    );
  });
}

async function requestJson<TResponse>(
  baseUrl: string,
  path: string,
  init: RequestInit,
  signal?: AbortSignal,
) {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    signal,
  });
  const data = (await response.json().catch(() => undefined)) as TResponse;
  if (!response.ok) {
    throw new RulesApiError(response.statusText, response.status, data);
  }
  return data;
}

function isFallbackWorthy(error: unknown) {
  if (error instanceof RulesApiError) {
    return error.status >= 500 || error.status === 0;
  }
  if (error instanceof TypeError) {
    return true;
  }
  if (error instanceof DOMException && error.name !== "AbortError") {
    return true;
  }
  return false;
}

export function createMockRulesApi(): RulesApi {
  return {
    async listRules(signal?: AbortSignal) {
      await delay(signal);
      return structuredClone(grammarRules);
    },
    async listCategories(signal?: AbortSignal) {
      await delay(signal);
      return structuredClone(ruleCategories);
    },
  };
}

export function createHttpRulesApi(baseUrl: string): RulesApi {
  return {
    listRules: (signal) =>
      requestJson<GrammarRule[]>(
        baseUrl,
        rulesContract.rules,
        { method: "GET" },
        signal,
      ),
    listCategories: (signal) =>
      requestJson<RuleCategoryOption[]>(
        baseUrl,
        rulesContract.categories,
        { method: "GET" },
        signal,
      ),
  };
}

export function createRulesApi(
  baseUrl: string | undefined,
  dataSource: ApiDataSource,
) {
  if (dataSource === "mock" || !baseUrl) {
    return createMockRulesApi();
  }

  const httpApi = createHttpRulesApi(baseUrl);
  if (dataSource === "api") {
    return httpApi;
  }

  const mockApi = createMockRulesApi();

  return {
    async listRules(signal?: AbortSignal) {
      try {
        return await httpApi.listRules(signal);
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.listRules(signal);
      }
    },
    async listCategories(signal?: AbortSignal) {
      try {
        return await httpApi.listCategories(signal);
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.listCategories(signal);
      }
    },
  };
}

export function RulesApiProvider({
  api,
  children,
}: PropsWithChildren<{ api: RulesApi }>) {
  return (
    <RulesApiContext.Provider value={api}>{children}</RulesApiContext.Provider>
  );
}

export function useRulesApi() {
  const api = useContext(RulesApiContext);
  if (!api) throw new Error("RulesApiProvider is required");
  return api;
}
