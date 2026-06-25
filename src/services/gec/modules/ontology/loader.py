"""rdflib loader and cache for the Arabic Syntax Ontology."""

from pathlib import Path
from typing import Optional

from loguru import logger
from rdflib import Graph

DEFAULT_OWL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "ontology"
    / "oas_grammar.owl"
)


class OntologyLoader:
    """Singleton class to load and execute queries on the Arabic Syntax Ontology."""

    _instance: Optional["OntologyLoader"] = None
    graph: Graph
    is_loaded: bool

    def __new__(cls, *args, **kwargs):
        """Ensures only one instance of OntologyLoader is created."""
        if cls._instance is None:
            logger.debug("Creating new OntologyLoader singleton instance")
            cls._instance = super().__new__(cls)
            cls._instance.graph = Graph()
            cls._instance.is_loaded = False
        else:
            logger.debug("Returning existing OntologyLoader singleton instance")
        return cls._instance

    def __init__(self, owl_path: Path | None = None):
        """Initializes the loader with the path to the OWL file.

        Args:
            owl_path: Optional path to the oas_grammar.owl file.
                Defaults to the default path.
        """
        self.owl_path = Path(owl_path) if owl_path else DEFAULT_OWL_PATH
        if not self.owl_path.exists():
            logger.warning("OWL file not found at path: {}", self.owl_path)

    def load_graph(self) -> None:
        """Parses the OWL file into the rdflib Graph.

        Blocks until the ontology is loaded into memory.
        """
        if not self.is_loaded:
            logger.info("Parsing ontology graph from: {}", self.owl_path)
            try:
                self.graph.parse(source=str(self.owl_path), format="xml")
            except Exception:
                logger.exception("Failed to parse ontology from: {}", self.owl_path)
                raise
            self.is_loaded = True
            logger.info(
                "Ontology graph loaded successfully. Total triples: {}", len(self.graph)
            )
        else:
            logger.debug("Ontology graph already loaded; skipping re-parse")

    def query(self, sparql_query: str):
        """Executes a SPARQL query against the loaded graph.

        Args:
            sparql_query: The SPARQL query string.

        Returns:
            rdflib.query.Result: The query results.

        Raises:
            RuntimeError: If called before load_graph() has completed.
        """
        if not self.is_loaded:
            logger.error("Ontology graph not loaded when query was called")
            raise RuntimeError("Ontology graph is not loaded. Call load_graph() first.")
        logger.debug("Executing SPARQL query")
        return self.graph.query(sparql_query)
