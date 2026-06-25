from __future__ import annotations

from src.services.gec.schemas import (
    DictionaryCandidateEdit,
    EditOperation,
    EditTaggerCandidateEdit,
    GECUnionCandidateEdit,
    ModuleName,
    OntologyCandidateEdit,
)


def levenshtein(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            curr_row.append(min(prev_row[j + 1] + 1, curr_row[j] + 1, prev_row[j] + (c1 != c2)))
        prev_row = curr_row
    return prev_row[-1]


def score_candidate(
    candidate: GECUnionCandidateEdit,
    module_name: ModuleName,
    error_span,
    original_text: str,
    tokens: list,
    peer_candidates: list,
    config,
) -> float:
    score = 0.0
    
    if module_name == ModuleName.ONTOLOGY:
        score += config.W_ONTOLOGY
        if isinstance(candidate, OntologyCandidateEdit):
            if candidate.is_independent:
                score += config.W_INDEPENDENT
            if candidate.group.group_rank > 0:
                score += config.W_GROUP_RANK / candidate.group.group_rank
    elif module_name == ModuleName.TAG:
        score += config.W_TAG
    elif module_name == ModuleName.DICTIONARY:
        score += config.W_DICTIONARY
        if isinstance(candidate, DictionaryCandidateEdit):
            alts = candidate.alternatives
            if alts and alts[0] == candidate.correction:
                score += config.W_FIRST_ALT
    
    score += config.W_EDIT_CONF * candidate.edit_confidence
    score += config.W_GED_CONF * error_span.confidence
    
    if candidate.edit_confidence < config.CONF_LOW_THRESHOLD:
        score -= config.W_LOW_CONF
    
    if error_span.provenance_tier.value == "tier_1_rule_derived":
        score += config.W_TIER1
    elif error_span.provenance_tier.value == "tier_2_rule_supported":
        score += config.W_TIER2
    
    dist = levenshtein(original_text, candidate.correction)
    norm = max(len(original_text), len(candidate.correction), 1)
    score -= config.W_CHAR_DIST * (dist / norm)
    
    delta = abs(len(candidate.correction) - len(original_text))
    norm = max(len(original_text), 1)
    score -= config.W_LENGTH_RATIO * (delta / norm)
    
    if candidate.correction.strip() == "":
        if isinstance(candidate, EditTaggerCandidateEdit) and candidate.edit_operation:
            if candidate.edit_operation[0] != EditOperation.DELETE:
                score -= config.W_EMPTY
    
    from src.services.ged.schemas import ErrorCategory
    if error_span.category == ErrorCategory.ORTHOGRAPHY and module_name == ModuleName.DICTIONARY:
        score += config.W_SPELL_DICT
    if error_span.category in (ErrorCategory.SYNTAX, ErrorCategory.MORPHOLOGY) and module_name == ModuleName.ONTOLOGY:
        score += config.W_GRAM_ONT
    if error_span.explanation_eligible and module_name == ModuleName.ONTOLOGY:
        score += config.W_EXPLAIN
    
    agreeing = 0
    for other_name, other_cand in peer_candidates:
        if other_name != module_name and other_cand.correction == candidate.correction:
            agreeing += 1
    if agreeing > 0:
        score += config.W_AGREEMENT
    
    if len(error_span.sources) > 1:
        score += config.W_MULTI_SRC
    
    for tref in candidate.token_refs:
        if 0 <= tref < len(tokens) and tokens[tref].is_oov:
            score += config.W_OOV
            break
    
    if candidate.correction == original_text:
        return float("-inf")
    
    if isinstance(candidate, EditTaggerCandidateEdit) and candidate.edit_operation:
        first_op = candidate.edit_operation[0]
        if first_op == EditOperation.DELETE and candidate.correction.strip() != "":
            score -= config.W_OP_MISMATCH
        if first_op == EditOperation.INSERT and candidate.correction.strip() == "":
            score -= config.W_OP_MISMATCH
    
    return score