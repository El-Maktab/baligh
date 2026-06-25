import type {
  DictionaryBootstrap,
  DictionarySearchPayload,
  DictionarySearchResponse,
} from "./types";

export const mo3gmContract = {
  bootstrap: "/api/v1/mo3gm",
  search: "/api/v1/mo3gm/search",
} as const;

export type Mo3gmContract = {
  DictionaryBootstrap: DictionaryBootstrap;
  DictionarySearchPayload: DictionarySearchPayload;
  DictionarySearchResponse: DictionarySearchResponse;
};
