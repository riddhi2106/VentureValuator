"""Pydantic contracts shared by the LLM-backed pipeline agents."""

import json
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

TextEvidence = str | list[str]


def _string_list(value: Any) -> list[str]:
    """Normalize a scalar or collection into non-empty strings."""

    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    return [str(item).strip() for item in items if str(item).strip()]


class ExtractionOutput(BaseModel):
    """Normalized facts extracted from a startup pitch deck."""

    name: str = ""
    problem: TextEvidence = ""
    solution: TextEvidence = ""
    target_customer: TextEvidence = ""
    business_model: TextEvidence = ""
    pricing: TextEvidence = ""
    gtm_strategy: TextEvidence = ""
    team: TextEvidence = ""
    cost_structure: TextEvidence = ""
    competition: list[str] = Field(default_factory=list)
    notable_metrics: dict[str, Any] = Field(default_factory=dict)
    assumptions: TextEvidence = ""
    evidence: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("competition", mode="before")
    @classmethod
    def normalize_competition(cls, value: Any) -> list[str]:
        return _string_list(value)

    @field_validator("notable_metrics", mode="before")
    @classmethod
    def normalize_metrics(cls, value: Any) -> dict[str, Any]:
        if value in (None, ""):
            return {}
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, list):
            normalized: dict[str, Any] = {}
            for item in value:
                if isinstance(item, dict):
                    normalized.update(item)
                elif isinstance(item, str) and ":" in item:
                    key, metric_value = item.split(":", 1)
                    normalized[key.strip()] = metric_value.strip()
            return normalized
        return {}


class ResearchSource(BaseModel):
    """One traceable source supporting a market claim."""

    title: str = ""
    url: str = ""
    snippet: str = ""
    verified: bool = False


class CompetitiveLandscape(BaseModel):
    direct_competitors: list[str] = Field(default_factory=list)
    indirect_competitors: list[str] = Field(default_factory=list)
    competitive_advantages: list[str] = Field(default_factory=list)
    competitive_risks: list[str] = Field(default_factory=list)


class IndustryBenchmarks(BaseModel):
    average_gross_margin: str = ""
    typical_cac_range: str = ""
    ltv_range: str = ""
    unit_economics_notes: str = ""


class MarketOutput(BaseModel):
    """Validated market-research output consumed by later agents."""

    market_category: str = ""
    tam: str = ""
    sam: str = ""
    som: str = ""
    market_growth_rate: str = ""
    key_trends: list[str] = Field(default_factory=list)
    customer_segments: list[str] = Field(default_factory=list)
    competitive_landscape: CompetitiveLandscape = Field(default_factory=CompetitiveLandscape)
    regional_factors: str = ""
    industry_benchmarks: IndustryBenchmarks = Field(default_factory=IndustryBenchmarks)
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    summary_insights: str = ""
    sources: list[ResearchSource] = Field(default_factory=list)


class SkepticOutput(BaseModel):
    """Adversarial diligence findings from the skeptical partner agent."""

    red_flags: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    challenged_claims: list[str] = Field(default_factory=list)
    partner_questions: list[str] = Field(default_factory=list)
    diligence_next_steps: list[str] = Field(default_factory=list)
    skeptic_summary: str = ""
    evidence_refs: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator(
        "red_flags",
        "missing_data",
        "challenged_claims",
        "partner_questions",
        "diligence_next_steps",
        mode="before",
    )
    @classmethod
    def normalize_findings(cls, value: Any) -> list[str]:
        return _string_list(value)


SLIDE_TITLES = (
    "Problem",
    "Target User",
    "Current Behavior",
    "Solution",
    "Why Now",
    "Market Size",
    "Competition",
    "Unique Advantage",
    "Business Model",
    "Traction",
    "Financial Projection Summary",
    "The Ask (Fundraising)",
)


class PitchSlide(BaseModel):
    title: str
    bullets: list[str] = Field(default_factory=list, max_length=6)
    source_refs: list[str] = Field(default_factory=list)


class PitchDeckOutput(BaseModel):
    """Exact twelve-slide structure required by the PowerPoint renderer."""

    slides: list[PitchSlide] = Field(min_length=12, max_length=12)

    @model_validator(mode="after")
    def validate_slide_order(self):
        actual = tuple(slide.title for slide in self.slides)
        if actual != SLIDE_TITLES:
            raise ValueError(f"slide titles/order must be: {SLIDE_TITLES}")
        return self


class MemoInsights(BaseModel):
    """Optional LLM narrative that cannot modify deterministic memo scores."""

    strengths: list[str] = Field(default_factory=list, max_length=5)
    risks: list[str] = Field(default_factory=list, max_length=5)
