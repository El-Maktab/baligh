"""Tests for the preprocessing service dependencies (Farasa and CAMeL Tools)."""

from farasa.segmenter import FarasaSegmenter
from camel_tools.morphology.database import MorphologyDB
from camel_tools.morphology.analyzer import Analyzer
from camel_tools.disambig.mle import MLEDisambiguator


def test_farasa_segmenter():
    """Verify that Farasa Segmenter can segment Arabic text."""
    segmenter = FarasaSegmenter(interactive=True)
    text = "ذهب الطلاب إلى المدرسة"
    segmented = segmenter.segment(text)
    assert "ال+طلاب" in segmented and "ال+مدرس+ة" in segmented
    assert "ذهب" in segmented


def test_camel_analyzer():
    """Verify that CAMeL Tools morphological analyzer can load and analyze words."""
    db = MorphologyDB.builtin_db()
    analyzer = Analyzer(db)
    analyses = analyzer.analyze("الطلاب")
    assert len(analyses) > 0
    assert any(analysis.get("pos") == "noun" for analysis in analyses)
    assert any(analysis.get("lex") == "طالِب" for analysis in analyses)


def test_camel_disambiguator():
    """Verify that CAMeL Tools MLE Disambiguator can disambiguate sentences in context."""
    mle = MLEDisambiguator.pretrained()
    sentence = ["ذهب", "الطلاب", "إلى", "المدرسة"]
    disambiguated = mle.disambiguate(sentence)
    
    assert len(disambiguated) == len(sentence)
    assert disambiguated[0].word == "ذهب"
    assert disambiguated[1].word == "الطلاب"
    
    # Check that it selects the correct part-of-speech tag for context
    top_analysis = disambiguated[0].analyses[0].analysis
    assert top_analysis.get("pos") == "verb"
