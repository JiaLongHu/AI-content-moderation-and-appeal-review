from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.models import RiskCategory, RiskLevel

Confidence = Annotated[float, Field(ge=0.0, le=1.0)]


class CategoryScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: RiskCategory
    confidence: Confidence


class ModerationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categories: Annotated[list[CategoryScore], Field(min_length=1, max_length=8)]
    final_category: RiskCategory
    final_level: RiskLevel
    reason: Annotated[str, Field(min_length=1, max_length=300)]

    @model_validator(mode="after")
    def validate_category_relationships(self) -> "ModerationOutput":
        category_names = [item.category for item in self.categories]
        if len(category_names) != len(set(category_names)):
            raise ValueError("risk categories must not be duplicated")
        if self.final_category not in category_names:
            raise ValueError("final_category must be present in categories")
        if self.final_level is RiskLevel.L0 and self.final_category is not RiskCategory.NORMAL:
            raise ValueError("L0 must use the normal category")
        if RiskCategory.NORMAL in category_names and len(category_names) > 1:
            raise ValueError("normal cannot be combined with risk categories")
        return self

    @property
    def confidence_by_category(self) -> dict[RiskCategory, float]:
        return {item.category: item.confidence for item in self.categories}

    @property
    def final_confidence(self) -> float:
        return self.confidence_by_category[self.final_category]
