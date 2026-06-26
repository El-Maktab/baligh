"""NWS Orchestrator.

Integrates the Caching Layer, WAC (CharNGram), and NWP (Hybrid) models.
"""

from src.services.nws.features.cache.manager import CacheManager
from src.services.nws.features.nwp.hybrid.model import HybridArabicPredictor
from src.services.nws.features.wac.char_ngram.model import CharNGramLM
from src.services.nws.schemas import NWSInput, NWSOutput, NWSSource, Suggestion


class NWSOrchestrator:
    """Orchestrates predictions using Caching, WAC, and NWP modules."""

    def __init__(
        self,
        cache_manager: CacheManager,
        nwp_model: HybridArabicPredictor,
        wac_model: CharNGramLM,
        min_cache_confidence: float = 0.10,
    ):
        """Initialize the orchestrator.

        Args:
            cache_manager: Handles Tier 1, 2, and 3 cache lookups/updates.
            nwp_model: Hybrid LSTM + N-Gram Next-Word Predictor.
            wac_model: Character N-Gram Auto-Completion model.
            min_cache_confidence: Minimum score [0.0, 1.0] for a prediction to be cached.
        """
        self.cache_manager = cache_manager
        self.nwp = nwp_model
        self.wac = wac_model
        self.min_cache_confidence = min_cache_confidence

    def predict(self, input_data: NWSInput, debug: bool = False) -> NWSOutput:
        """Route the input to the appropriate cache or ML model."""
        # 1. Build cache key
        cache_key = self.cache_manager.build_key(
            tokens=input_data.tokens,
            current_fragment=input_data.current_fragment,
        )

        # 2. Lookup in Cache Layer (Tier 1 -> Tier 2 -> Tier 3)
        cached_suggestions = self.cache_manager.lookup(cache_key)
        if cached_suggestions is not None:
            if debug:
                source = (
                    cached_suggestions[0].source if cached_suggestions else "unknown"
                )
                print(f"[DEBUG NWS] Cache HIT from {source}")
            # Slices to top_k just in case cache held more
            return NWSOutput(
                mode=input_data.mode,
                suggestions=cached_suggestions[: input_data.top_k],
            )

        # 3. Reconstruct context_text
        context_text = " ".join([t.form for t in input_data.tokens])

        # 4. Cache Miss - Route to ML models
        model_results = []
        if input_data.mode == "WAC":
            full_text = context_text
            if input_data.current_fragment:
                full_text = (
                    f"{context_text} {input_data.current_fragment}"
                    if context_text
                    else input_data.current_fragment
                )
            model_results = self.wac.predict(full_text, top_k=input_data.top_k)

        elif input_data.mode == "NWP":
            model_results = self.nwp.predict(context_text, top_k=input_data.top_k)

        if debug:
            print(f"[DEBUG NWS] Cache MISS - Evaluated using {input_data.mode} model")
            for rank, (word, score) in enumerate(model_results):
                print(f"[DEBUG NWS]   -> {rank}: {word} (score: {score:.4f})")

        # 5. Format to Suggestions
        suggestions = []
        for rank, (word, score) in enumerate(model_results):
            suggestions.append(
                Suggestion(
                    rank=rank,
                    word=word,
                    score=score,
                    source=NWSSource.MODEL,
                )
            )

        # 6. Filter for Caching
        # Only cache results that exceed our minimum confidence threshold to avoid
        # polluting the User LRU with highly uncertain predictions (e.g., typos).
        cacheable_suggestions = [
            s for s in suggestions if s.score >= self.min_cache_confidence
        ]

        # NOTE: if there are no cacheable_suggestions, we skip caching.
        # This acts as our safety mechanism for "wrong" predictions.
        if cacheable_suggestions:
            self.cache_manager.update(cache_key, cacheable_suggestions)

        return NWSOutput(mode=input_data.mode, suggestions=suggestions)
