import {
  createContext,
  useContext,
  type PropsWithChildren,
} from "react";

import { type ApiDataSource } from "../../app/environment";
import { mo3gmContract } from "./contract";
import { dictionaryBootstrap, findDictionaryEntry } from "./mockData";
import type {
  DictionaryBootstrap,
  DictionarySearchPayload,
  DictionarySearchResponse,
} from "./types";

export class Mo3gmApiError extends Error {
  status: number;
  payload?: unknown;

  constructor(message: string, status: number, payload?: unknown) {
    super(message);
    this.name = "Mo3gmApiError";
    this.status = status;
    this.payload = payload;
  }
}

export type Mo3gmApi = {
  getBootstrap: (signal?: AbortSignal) => Promise<DictionaryBootstrap>;
  searchEntry: (
    payload: DictionarySearchPayload,
    signal?: AbortSignal,
  ) => Promise<DictionarySearchResponse>;
};

const Mo3gmApiContext = createContext<Mo3gmApi | null>(null);

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
    throw new Mo3gmApiError(response.statusText, response.status, data);
  }
  return data;
}

function isFallbackWorthy(error: unknown) {
  if (error instanceof Mo3gmApiError) {
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

export function createMockMo3gmApi(): Mo3gmApi {
  return {
    async getBootstrap(signal?: AbortSignal) {
      await delay(signal);
      return structuredClone(dictionaryBootstrap);
    },
    async searchEntry(payload, signal) {
      await delay(signal);
      return {
        query: payload.query.trim(),
        entry: findDictionaryEntry(payload.query),
      };
    },
  };
}

export function createHttpMo3gmApi(baseUrl: string): Mo3gmApi {
  return {
    getBootstrap: (signal) =>
      requestJson<DictionaryBootstrap>(
        baseUrl,
        mo3gmContract.bootstrap,
        { method: "GET" },
        signal,
      ),
    searchEntry: (payload, signal) =>
      requestJson<DictionarySearchResponse>(
        baseUrl,
        mo3gmContract.search,
        { method: "POST", body: JSON.stringify(payload) },
        signal,
      ),
  };
}

export function createMo3gmApi(
  baseUrl: string | undefined,
  dataSource: ApiDataSource,
) {
  if (dataSource === "mock" || !baseUrl) {
    return createMockMo3gmApi();
  }

  const httpApi = createHttpMo3gmApi(baseUrl);
  if (dataSource === "api") {
    return httpApi;
  }

  const mockApi = createMockMo3gmApi();

  return {
    async getBootstrap(signal?: AbortSignal) {
      try {
        return await httpApi.getBootstrap(signal);
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.getBootstrap(signal);
      }
    },
    async searchEntry(payload: DictionarySearchPayload, signal?: AbortSignal) {
      try {
        return await httpApi.searchEntry(payload, signal);
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.searchEntry(payload, signal);
      }
    },
  };
}

export function Mo3gmApiProvider({
  api,
  children,
}: PropsWithChildren<{ api: Mo3gmApi }>) {
  return (
    <Mo3gmApiContext.Provider value={api}>{children}</Mo3gmApiContext.Provider>
  );
}

export function useMo3gmApi() {
  const api = useContext(Mo3gmApiContext);
  if (!api) throw new Error("Mo3gmApiProvider is required");
  return api;
}
