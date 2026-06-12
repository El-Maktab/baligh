"""Client for interacting with the Arramooz dictionary SQLite database.

Utilizes arramooz-pysqlite package.
"""

import asyncio
from typing import Any

import arramooz.arabicdictionary


class ArramoozClient:
    """Wrapper around the arramooz-pysqlite dictionary.

    Provides async methods for vocabulary checks and feature lookups
    by executing synchronous SQLite queries in separate threads.
    """

    def __init__(self):
        """Initializes the Arramooz dictionary wrappers for nouns and verbs."""
        # ArabicDictionary opens SQLite connections internally and indexes
        # on initialization.
        self.nouns_dict = arramooz.arabicdictionary.ArabicDictionary("nouns")
        self.verbs_dict = arramooz.arabicdictionary.ArabicDictionary("verbs")

    def _lookup_sync(self, word: str) -> list[dict[str, Any]]:
        """Synchronously queries nouns and verbs tables for the given word.

        Args:
            word: The normalized Arabic word to search for.

        Returns:
            list: Combined list of matching entry dictionaries, each tagged
                with their source table.
        """
        results = []

        noun_results = self.nouns_dict.lookup(word)
        if noun_results:
            for row in noun_results:
                row_dict = dict(row)
                row_dict["table"] = "nouns"
                results.append(row_dict)

        verb_results = self.verbs_dict.lookup(word)
        if verb_results:
            for row in verb_results:
                row_dict = dict(row)
                row_dict["table"] = "verbs"
                results.append(row_dict)

        return results

    async def check_word_exists(self, word: str) -> bool:
        """Asynchronously checks if a word exists in either nouns or verbs database.

        Args:
            word: The Arabic word to check.

        Returns:
            bool: True if the word is in the dictionary, False otherwise.
        """
        results = await asyncio.to_thread(self._lookup_sync, word)
        return len(results) > 0

    async def get_word_features(self, word: str) -> list[dict[str, Any]]:
        """Asynchronously retrieves morphological features for a word.

        Args:
            word: The Arabic word to look up.

        Returns:
            list[dict]: Feature dictionaries found in either nouns or verbs tables.
        """
        return await asyncio.to_thread(self._lookup_sync, word)
