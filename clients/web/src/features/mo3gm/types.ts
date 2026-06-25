export type DictionaryExample = {
  source: string;
  text: string;
};

export type DictionaryEntry = {
  word: string;
  vocalized: string;
  root: string;
  partOfSpeech: string;
  meanings: string[];
  synonyms: string[];
  antonyms: string[];
  examples: DictionaryExample[];
};

export type DictionaryBootstrap = {
  initialQuery: string;
  featuredEntry: DictionaryEntry;
  recentSearches: string[];
};

export type DictionarySearchPayload = {
  query: string;
};

export type DictionarySearchResponse = {
  query: string;
  entry?: DictionaryEntry;
};
