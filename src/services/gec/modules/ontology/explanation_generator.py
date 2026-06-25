from pathlib import Path
from typing import Any

import yaml

DEFAULT_TEMPLATES_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "explanations"
    / "templates.yaml"
)


class ExplanationGenerator:
    """Generates human-readable Arabic explanations for grammatical corrections."""

    def __init__(self, templates_path: Path | None = None) -> None:
        """Initializes the ExplanationGenerator."""
        self.templates_path = templates_path or DEFAULT_TEMPLATES_PATH
        self._templates: dict[str, Any] = {}
        self._relation_map: dict[str, Any] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Loads explanation templates from the YAML file."""
        if not self.templates_path.exists():
            return
        try:
            with open(self.templates_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data:
                self._templates = data.get("templates", {})
                self._relation_map = data.get("metadata", {}).get(
                    "relation_to_template", {}
                )
        except Exception:
            pass

    def generate_explanation(
        self,
        relation_type: str,
        expected_features: dict[str, Any],
        actual_features: dict[str, Any],
    ) -> str:
        """Generates an Arabic explanation string for the grammatical correction.

        Args:
            relation_type: The type of relation violated or its URI.
            expected_features: Dict of expected morphological feature values.
            actual_features: Dict of actual morphological feature values.

        Returns:
            The explanation string in Arabic.
        """
        # Map legacy names to URIs
        relation_uri = relation_type
        if not relation_type.startswith("http"):
            if relation_type == "subject_verb":
                relation_uri = "http://arabicontology.org/oas_grammar.owl#فاعل"
            elif relation_type == "noun_adjective":
                relation_uri = "http://arabicontology.org/oas_grammar.owl#نعت"
            elif relation_type == "idafa":
                relation_uri = "http://arabicontology.org/oas_grammar.owl#مضاف_اليه"

        # Determine violation type
        violation_type = "case_mismatch"
        if (
            "nun_deletion" in expected_features
            or expected_features.get("nun_deletion") == "true"
        ):
            violation_type = "nun_deletion"
        elif (
            expected_features.get("definiteness") != actual_features.get("definiteness")
            and expected_features.get("definiteness") is not None
        ):
            violation_type = "definiteness_mismatch"
        elif (
            expected_features.get("number") != actual_features.get("number")
            and expected_features.get("number") is not None
        ):
            violation_type = "number_mismatch"
        elif (
            expected_features.get("gender") != actual_features.get("gender")
            and expected_features.get("gender") is not None
        ):
            violation_type = "gender_mismatch"

        # Match template configuration
        template_configs = self._relation_map.get(relation_uri, [])
        for config in template_configs:
            if config.get("condition") == violation_type:
                template_id = config.get("template_id")
                template = self._templates.get(template_id)
                if template:
                    template_str = template.get("template", "")

                    case_ar = {
                        "nominative": "مرفوعاً",
                        "accusative": "منصوباً",
                        "genitive": "مجروراً",
                        "jussive": "مجزوماً",
                    }
                    expected_case = case_ar.get(
                        expected_features.get("case", ""),
                        expected_features.get("case", ""),
                    )
                    actual_case = case_ar.get(
                        actual_features.get("case", ""), actual_features.get("case", "")
                    )

                    number_type = "جمع المذكر السالم"
                    if actual_features.get("number") == "dual":
                        number_type = "المثنى"

                    res = template_str.replace("{expected_case}", str(expected_case))
                    res = res.replace("{actual_case}", str(actual_case))
                    res = res.replace("{number_type}", number_type)
                    return res

        # Legacy fallbacks
        norm_type = (
            relation_type.split("#")[-1] if "#" in relation_type else relation_type
        )
        if norm_type in ("subject_verb", "فاعل"):
            expected_case = expected_features.get("case")
            actual_case = actual_features.get("case")
            if expected_case == "nominative" and actual_case in (
                "accusative",
                "genitive",
            ):
                return "الفاعل يجب أن يكون مرفوعاً"

            expected_number = expected_features.get("number")
            actual_number = actual_features.get("number")
            if expected_number == "singular" and actual_number in ("dual", "plural"):
                return "إذا تقدم الفعل على الفاعل، لزم إفراده"

            return "الفاعل يجب أن يكون مرفوعاً"

        elif norm_type in ("noun_adjective", "نعت"):
            return "النعت يتبع المنعوت في التذكير والتأنيث"

        elif norm_type in ("idafa", "مضاف_اليه"):
            actual_number = actual_features.get("number")
            if actual_number == "dual":
                return "تحذف نون المثنى عند الإضافة"
            return "تحذف نون جمع المذكر السالم عند الإضافة"

        return "مخالفة في قواعد التركيب النحوي"
