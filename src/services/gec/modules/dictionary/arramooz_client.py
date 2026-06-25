"""Client for interacting with the Arramooz dictionary SQLite databases."""

import sqlite3
from pathlib import Path
from typing import Any

from loguru import logger
from pyarabic.araby import normalize_hamza

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "dictionary"
_DICT_DB = _DATA_DIR / "arabicdictionary.sqlite"
_FREQ_DB = _DATA_DIR / "wordfreq.sqlite"
_STOP_WORDS = _DATA_DIR / "stopwords.txt"


def _open_db(path: Path) -> sqlite3.Connection:
    """Open a read-only SQLite connection with Row factory."""
    uri = f"file:{path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _open_file(path: Path) -> frozenset[str]:
    """Open a text file and return a frozenset of its lines."""
    with open(path, encoding="utf-8") as f:
        return frozenset(line.strip() for line in f if line.strip())


class ArramoozClient:
    """Direct-SQLite client for the Arramooz dictionary databases.

    Provides methods for vocabulary checks, feature lookups,
    and word-frequency retrieval.
    """

    def __init__(self) -> None:
        """Initializes SQLite connections to the dictionary and frequency DBs."""
        self._dict_conn = _open_db(_DICT_DB)
        self._freq_conn: sqlite3.Connection | None = None
        self._stop_words: frozenset[str] = _open_file(_STOP_WORDS)
        logger.info("ArramoozClient initialized | dict_db={}", _DICT_DB)

    # ------------------------------------------------------------------
    # Dictionary lookups
    # ------------------------------------------------------------------

    def _lookup(self, word: str) -> list[dict[str, Any]]:
        """Queries nouns and verbs tables for the given word.

        Args:
            word: The Arabic word to search for.

        Returns:
            Combined list of matching entry dictionaries.
        """
        normalized = normalize_hamza(word)
        results: list[dict[str, Any]] = []
        cursor = self._dict_conn.cursor()

        for table in ("nouns", "verbs"):
            try:
                cursor.execute(
                    f"SELECT * FROM {table} WHERE normalized = ?",
                    (normalized,),
                )
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    row_dict["table"] = table
                    results.append(row_dict)
            except sqlite3.OperationalError:
                logger.exception("Error querying table {}", table)

        return results

    def check_word_exists(self, word: str) -> bool:
        """Checks if a word exists in either nouns or verbs database.

        Also checks against the built-in function word list
        (prepositions, pronouns, accusative particles) from pyarabic.

        Args:
            word: The Arabic word to check.

        Returns:
            True if the word is in the dictionary or function word list.
        """
        if word in self._stop_words:
            return True
        results = self._lookup(word)
        return len(results) > 0

    def get_word_features(self, word: str) -> list[dict[str, Any]]:
        """Retrieves morphological features for a word.

        Args:
            word: The Arabic word to look up.

        Returns:
            Feature dictionaries found in either nouns or verbs tables.
        """
        return self._lookup(word)

    def get_all_normalized_words(self) -> list[str]:
        """Queries distinct normalized words from both nouns and verbs tables.

        Also includes Arabic function words (prepositions, pronouns,
        accusative particles) from pyarabic so they are part of the
        vocabulary used for OOV checks and candidate generation.

        Returns:
            A combined list of unique normalized words.
        """
        words: set[str] = set()
        cursor = self._dict_conn.cursor()

        for table in ("nouns", "verbs"):
            try:
                cursor.execute(f"SELECT DISTINCT normalized FROM {table}")
                for row in cursor.fetchall():
                    val = row["normalized"]
                    if val:
                        words.add(val)
            except sqlite3.OperationalError:
                logger.exception("Error fetching words from {}", table)

        words.update(self._stop_words)

        logger.info("Fetched {} normalized words from dictionary", len(words))
        return list(words)

    # ------------------------------------------------------------------
    # Word frequency lookups
    # ------------------------------------------------------------------

    def _ensure_freq_db(self) -> sqlite3.Connection:
        """Lazily open the word-frequency database on first use."""
        if self._freq_conn is None:
            logger.debug("Lazily opening frequency DB | path={}", _FREQ_DB)
            self._freq_conn = _open_db(_FREQ_DB)
        return self._freq_conn

    def get_word_frequency(self, word: str) -> int:
        """Return the corpus frequency for *word* from the frequency DB.

        Args:
            word: The unvocalized Arabic word.

        Returns:
            The highest frequency value found, or 0.
        """
        conn = self._ensure_freq_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT MAX(freq) AS freq FROM wordfreq WHERE unvocalized = ?",
                (word,),
            )
            row = cursor.fetchone()
            if row and row["freq"] is not None:
                return int(row["freq"])
        except sqlite3.OperationalError:
            logger.exception("Error querying word frequency for {!r}", word)
        return 0

    def get_words_by_root(
        self, root: str, table: str | None = None
    ) -> list[dict[str, Any]]:
        """Queries nouns and verbs tables for entries with the given root.

        Args:
            root: The Arabic root to search for.
            table: Optional table to restrict search ("nouns" or "verbs").

        Returns:
            List of matching entry dictionaries.
        """
        tables = (table,) if table else ("nouns", "verbs")
        results: list[dict[str, Any]] = []
        cursor = self._dict_conn.cursor()

        for t in tables:
            try:
                cursor.execute(
                    f"SELECT * FROM {t} WHERE root = ?",
                    (root,),
                )
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    row_dict["table"] = t
                    results.append(row_dict)
            except sqlite3.OperationalError:
                logger.exception("Error querying table {} for root {}", t, root)

        return results

    def get_word_by_lemma(
        self, lemma: str, table: str | None = None
    ) -> list[dict[str, Any]]:
        """Queries nouns and verbs tables for entries with the given lemma.

        Args:
            lemma: The lemma/unvocalized word to search for.
            table: Optional table to restrict search ("nouns" or "verbs").

        Returns:
            List of matching entry dictionaries.
        """
        normalized = normalize_hamza(lemma)
        tables = (table,) if table else ("nouns", "verbs")
        results: list[dict[str, Any]] = []
        cursor = self._dict_conn.cursor()

        for t in tables:
            try:
                cursor.execute(
                    f"SELECT * FROM {t} WHERE unvocalized = ? OR normalized = ?",
                    (lemma, normalized),
                )
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    row_dict["table"] = t
                    results.append(row_dict)
            except sqlite3.OperationalError:
                logger.exception("Error querying table {} for lemma {}", t, lemma)

        return results

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close all open database connections."""
        self._dict_conn.close()
        if self._freq_conn is not None:
            self._freq_conn.close()
        logger.debug("ArramoozClient connections closed")
