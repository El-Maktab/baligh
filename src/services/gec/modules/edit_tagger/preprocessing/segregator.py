"""Edit segregation utilities."""

from src.services.gec.modules.edit_tagger.common import ProjectedExample
from src.services.gec.modules.edit_tagger.preprocessing.punctuation import (
    PUNCTUATION_SET,
)

class Segregator:
    """Segregates edits by punctuation type."""

    def segregate(self, proj_examples: list[ProjectedExample]) -> tuple[ProjectedExample, ProjectedExample]:
        """Segregate edits into punctuation and non-punctuation."""
        
        punc_labels : list[str] = []
        non_punc_labels : list[str] = []        
        punc_tokens : list[str] = []
        non_punc_tokens : list[str] = []
        count = 0
        coun2 = 0
        for example in proj_examples:
            for token, label in zip(example.subwords, example.labels_star):
                if self._is_punctuation_edit(token, label):
                    punc_labels.append(label)
                    punc_tokens.append(token)
                    count+=1
                else:
                    non_punc_labels.append(label)
                    non_punc_tokens.append(token)
                    coun2+=1
        print(count)
        punc_edits = ProjectedExample(subwords= punc_tokens, labels_star= punc_labels, labels=[])
        non_punc_edits = ProjectedExample(subwords= non_punc_tokens, labels_star= non_punc_labels, labels= [])
        return punc_edits, non_punc_edits

    def _is_punctuation_edit(self, token: str, label: str) -> bool:
        """Determine whether an alignment represents only punctuation."""
        return any(token) in PUNCTUATION_SET or any(label) in PUNCTUATION_SET