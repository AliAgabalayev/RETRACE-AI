"""Shared, frozen data contracts for the visual-regression pipeline.

Owner: senior-pm froze these in hour 0; python-developer owns further edits.
Any change must be agreed with dl-engineer and qa-engineer and recorded in
docs/DECISIONS.md.

Conventions (see docs/PROJECT_BRIEF.md section 8):
- Image order is always (reference, candidate). Reference = previously approved
  screenshot; candidate = new build screenshot.
- Boxes are ``[x1, y1, x2, y2]`` in ORIGINAL reference-image pixel coordinates,
  right/bottom exclusive, integers.
- Transforms map candidate pixel coordinates to reference pixel coordinates as a
  3x3 homogeneous matrix (row-major nested lists).
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Box = tuple[int, int, int, int]


class RuleEffect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class Rule(BaseModel):
    id: str = Field(min_length=1, max_length=32)
    effect: RuleEffect
    description: str = Field(min_length=1)


class PairInput(BaseModel):
    """Inference input. Never carries ground-truth labels."""

    reference_path: str
    candidate_path: str
    rules: list[Rule]
    sample_id: str | None = None


class AlignmentStatus(str, Enum):
    IDENTITY = "identity"  # same size, no warp applied
    ALIGNED = "aligned"  # translation/affine estimated and passed quality checks
    RESIZED = "resized"  # dimensions differed; candidate resized to reference
    UNRELIABLE = "unreliable"  # estimation failed or quality too low -> review
    FAILED = "failed"  # could not decode / process


class AlignmentResult(BaseModel):
    status: AlignmentStatus
    # 3x3 matrix mapping candidate pixel (x, y, 1) -> reference pixel coordinates.
    candidate_to_reference: list[list[float]]
    # Fraction of reference pixels covered by valid aligned candidate pixels.
    overlap_fraction: float = Field(ge=0.0, le=1.0)
    # Path to a saved uint8 mask (255 = valid overlap) in reference coordinates.
    overlap_mask_path: str | None = None
    diagnostics: dict[str, float | str | int | bool] = Field(default_factory=dict)


ProposalSource = Literal["dinov2", "classical", "union"]


class RegionProposal(BaseModel):
    id: str  # stable within a run, e.g. "R1"
    box: Box  # reference coordinates, right/bottom exclusive
    score: float  # max/mean patch cosine distance (dinov2) or pixel diff score
    source: ProposalSource
    area_fraction: float = Field(ge=0.0, le=1.0)

    @field_validator("box")
    @classmethod
    def _valid_box(cls, v: Box) -> Box:
        x1, y1, x2, y2 = v
        if x2 <= x1 or y2 <= y1 or x1 < 0 or y1 < 0:
            raise ValueError(f"invalid box {v}")
        return v


class Verdict(str, Enum):
    ALLOWED = "allowed"
    FORBIDDEN = "forbidden"
    UNCERTAIN = "uncertain"


class RegionJudgment(BaseModel):
    region_id: str  # "SCENE" for the whole-scene audit
    observed_change: str
    verdict: Verdict
    rule_ids: list[str] = Field(default_factory=list)
    evidence: str = ""
    model: str  # e.g. "ollama:qwen2.5vl:3b", "mock:fault-injection"
    is_mock: bool = False
    errors: list[str] = Field(default_factory=list)
    # True only when the response passed schema + rule-ID + consistency checks.
    validated: bool = False
    latency_s: float | None = None


SCENE_REGION_ID = "SCENE"  # region_id of the whole-scene audit judgment


class SceneAudit(BaseModel):
    judgment: RegionJudgment
    # Additional suspicious changes the audit reported outside proposed regions.
    extra_changes_reported: bool = False


class FinalDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ExecutionStatus(str, Enum):
    COMPLETE = "complete"  # all stages ran with real components
    DEGRADED = "degraded"  # some component unavailable / fallback used
    ERROR = "error"  # pipeline could not produce a comparison


class Coverage(BaseModel):
    proposals_total: int = 0  # proposals found before the cap
    proposals_judged: int = 0
    truncated: bool = False  # cap dropped proposals
    scene_audit_ran: bool = False
    deadline_exceeded: bool = False


class Versions(BaseModel):
    feature_model: str | None = None  # e.g. "dinov2_vits14@<hub ref>"
    vlm_model: str | None = None
    prompt_version: str | None = None
    config_hash: str | None = None
    device: str | None = None
    dtype: str | None = None


class AnalysisResult(BaseModel):
    run_id: str
    sample_id: str | None = None
    created_at: str  # ISO 8601 UTC
    execution_status: ExecutionStatus
    final_decision: FinalDecision
    decision_reason: str
    rules: list[Rule]
    alignment: AlignmentResult | None = None
    proposals: list[RegionProposal] = Field(default_factory=list)
    judgments: list[RegionJudgment] = Field(default_factory=list)
    scene_audit: SceneAudit | None = None
    coverage: Coverage = Field(default_factory=Coverage)
    versions: Versions = Field(default_factory=Versions)
    timings: dict[str, float] = Field(default_factory=dict)  # seconds per stage
    errors: list[str] = Field(default_factory=list)
    # Artifact paths relative to the run directory.
    paths: dict[str, str] = Field(default_factory=dict)
    # Engine mode actually used: "real", "degraded", "mock".
    engine_mode: Literal["real", "degraded", "mock"] = "real"
