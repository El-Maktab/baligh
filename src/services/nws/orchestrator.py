"""NWS Orchestrator.

Integrates the Caching Layer, WAC (CharNGram), and NWP (Hybrid) models.
"""

import re

from src.services.nws.features.cache.manager import CacheManager
from src.services.nws.features.nwp.hybrid.model import HybridArabicPredictor
from src.services.nws.features.wac.char_ngram.model import CharNGramLM
from src.services.nws.schemas import NWSInput, NWSOutput, NWSSource, Suggestion

#############################################################################
# Normalization section
#############################################################################

TASHKEEL = re.compile(r"[\u064B-\u065F\u0670]")
TATWEEL = re.compile(r"\u0640")
ALIF_MAP = str.maketrans(
    {"\u0622": "\u0627", "\u0623": "\u0627", "\u0625": "\u0627", "\u0671": "\u0627"}
)
YAA_MAP = str.maketrans(
    {
        "\u0649": "\u064a",
        "\ufeef": "\u064a",
        "\ufef0": "\u064a",
        "\ufef1": "\u064a",
        "\ufef2": "\u064a",
        "\ufef3": "\u064a",
        "\ufef4": "\u064a",
    }
)
HAA_MAP = str.maketrans({"\u0629": "\u0647"})


def normalise_arabic(text: str) -> str:
    if not text:
        return text
    text = TASHKEEL.sub("", text)
    text = TATWEEL.sub("", text)
    text = text.translate(ALIF_MAP)
    text = text.translate(YAA_MAP)
    text = text.translate(HAA_MAP)
    text = re.sub(r"[^\u0600-\u06FF\u0750-\u077F\s0-9\.,!?؟\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


#############################################################################
# NWS Orchestrator
#############################################################################


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
            nwp_model: Hybrid LSTM +/or N-Gram Next-Word Predictor.
            wac_model: Character N-Gram Auto-Completion model.
            min_cache_confidence: Minimum score [0.0, 1.0] for a prediction to be cached.
        """
        self.cache_manager = cache_manager
        self.nwp = nwp_model
        self.wac = wac_model
        self.min_cache_confidence = min_cache_confidence

    def predict(self, input_data: NWSInput, debug: bool = False) -> NWSOutput:
        """Route the input to the appropriate cache or ML model."""
        # Build cache key
        cache_key = self.cache_manager.build_key(
            tokens=input_data.tokens,
            current_fragment=input_data.current_fragment,
        )

        # Lookup in Cache Layer (Tier 1 -> Tier 2 -> Tier 3)
        cached_suggestions = self.cache_manager.lookup(cache_key)
        if cached_suggestions is not None:
            if debug:
                source = (
                    cached_suggestions[0].source if cached_suggestions else "unknown"
                )
                print(f"[DEBUG NWS] Cache HIT from {source}")

            return NWSOutput(
                mode=input_data.mode,
                suggestions=cached_suggestions[: input_data.top_k],
            )

        # Cache Miss - Route to ML models
        context_text = " ".join([t.form for t in input_data.tokens])
        model_results = []
        if input_data.mode == "WAC":
            full_text = context_text
            if input_data.current_fragment:
                full_text = (
                    f"{context_text} {input_data.current_fragment}"
                    if context_text
                    else input_data.current_fragment
                )

            full_text = normalise_arabic(full_text)
            model_results = self.wac.predict(full_text, top_k=input_data.top_k)

        elif input_data.mode == "NWP":
            nwp_context = context_text + " " if context_text else ""
            nwp_context = normalise_arabic(nwp_context)

            if not nwp_context.endswith(" "):
                nwp_context += " "
            model_results = self.nwp.predict(nwp_context, top_k=input_data.top_k)

        if debug:
            print(f"[DEBUG NWS] Cache MISS - Evaluated using {input_data.mode} model")
            for rank, (word, score) in enumerate(model_results):
                print(f"[DEBUG NWS] -> {rank}: {word} (score: {score:.4f})")

        # Format to Suggestions
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

        # cache results with high confidence only
        cacheable_suggestions = [
            s for s in suggestions if s.score >= self.min_cache_confidence
        ]
        if cacheable_suggestions:
            self.cache_manager.update(cache_key, cacheable_suggestions)

        return NWSOutput(mode=input_data.mode, suggestions=suggestions)
