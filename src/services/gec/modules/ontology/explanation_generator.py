"""Explaination generator for ontology candidates."""

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
        relation_uri: str,
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

        return "مخالفة في قواعد التركيب النحوي"
