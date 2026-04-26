# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# API Request / Response Models (Pydantic v2)
#
# These models enforce the same validation as the JSON schemas. They
# are the public contract that external consumers — other Harmony
# pillars, SDKs, and CLI tools — code against. Patterns mirror those
# in cell_identity_schema.json and alias_namespace_rules.md.

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# --- Regex patterns (kept in sync with the SQL schema and JSON schema) ----

CELL_KEY_PATTERN = r"^hsam:r[0-9]{2}:[a-z]{2,8}:[0-9a-hjkmnp-tv-z]{16}$"
VOLUMETRIC_CELL_KEY_PATTERN = (
    r"^hsam:r[0-9]{2}:[a-z]{2,8}:[0-9a-hjkmnp-tv-z]{16}"
    r":v-?[0-9]+\.[0-9]--?[0-9]+\.[0-9]$"
)
# Either surface or volumetric — used by endpoints that accept both shapes.
ANY_CELL_KEY_PATTERN = (
    r"^hsam:r[0-9]{2}:[a-z]{2,8}:[0-9a-hjkmnp-tv-z]{16}"
    r"(:v-?[0-9]+\.[0-9]--?[0-9]+\.[0-9])?$"
)
CELL_ID_PATTERN = r"^hc_[a-z0-9]{9}$"
ENTITY_ID_PATTERN = r"^ent_[a-z]{3}_[a-z0-9]{6}$"
CANONICAL_ID_PATTERN = r"^(hc_[a-z0-9]{9}|ent_[a-z]{3}_[a-z0-9]{6}|ds_[a-z0-9]{8}|st_[a-z0-9]{10}|ca_[a-z]{3}_[a-z0-9]{8})$"
ALIAS_PATTERN = r"^[A-Za-z]{2,4}-[0-9]{1,6}$"       # stored uppercase, input case-insensitive
NAMESPACE_PATTERN = r"^[a-z]{2,4}(\.[a-z0-9_]{2,32}){2,5}$"
PREFIX_PATTERN = r"^[A-Z]{2,4}$"
ENTITY_SUBTYPE_PATTERN = r"^[a-z]{3}$"
REGION_CODE_PATTERN = r"^[a-z]{2,8}$"


# -------------------------------------------------------------------------
# Error envelope
# -------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Machine-readable error code")
    detail: str = Field(..., description="Human-readable error description")


# -------------------------------------------------------------------------
# Cells
# -------------------------------------------------------------------------

class CellCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cell_key: str = Field(..., pattern=CELL_KEY_PATTERN)
    resolution_level: int = Field(..., ge=0, le=12)
    cube_face: int = Field(..., ge=0, le=5)
    face_grid_u: int = Field(..., ge=0)
    face_grid_v: int = Field(..., ge=0)
    region_code: str = Field(..., pattern=REGION_CODE_PATTERN)
    parent_cell_id: Optional[str] = Field(None, pattern=CELL_ID_PATTERN)
    human_alias: Optional[str] = Field(None, pattern=ALIAS_PATTERN)
    alias_namespace: Optional[str] = Field(None, pattern=NAMESPACE_PATTERN)
    friendly_name: Optional[str] = Field(None, max_length=200)
    semantic_labels: Optional[list[str]] = None

    @field_validator("human_alias")
    @classmethod
    def _normalise_alias(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v


# Volumetric subdivision — ADR-015 §2.8. A POST to this endpoint creates a
# volumetric child cell on an existing surface cell.
class VolumetricCellCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    surface_cell_id: str = Field(..., pattern=CELL_ID_PATTERN)
    altitude_min_m: float = Field(..., description="Band lower bound, metres (WGS84)")
    altitude_max_m: float = Field(..., description="Band upper bound, metres (WGS84)")
    vertical_subdivision_level: Optional[int] = Field(None, ge=1)
    human_alias: Optional[str] = Field(None, pattern=ALIAS_PATTERN)
    alias_namespace: Optional[str] = Field(None, pattern=NAMESPACE_PATTERN)
    friendly_name: Optional[str] = Field(None, max_length=200)
    semantic_labels: Optional[list[str]] = None

    @field_validator("human_alias")
    @classmethod
    def _normalise_alias(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v


# -------------------------------------------------------------------------
# Fidelity Coverage — PATCH /cells/{cell_key}/fidelity (Dr. Voss Option B)
# -------------------------------------------------------------------------

class StructuralFidelity(BaseModel):
    """Structural fidelity slot for a cell record."""
    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="available | pending | unavailable")
    source: Optional[str] = None
    captured_at: Optional[str] = None
    source_tier: Optional[int] = Field(None, ge=1, le=4)

    @model_validator(mode="after")
    def _validate_constraints(self) -> "StructuralFidelity":
        if self.status not in ("available", "pending", "unavailable"):
            raise ValueError(
                f"structural.status must be one of: available, pending, unavailable. Got: {self.status!r}"
            )
        if self.status == "available" and self.source is None:
            raise ValueError("structural.source must not be null when status is 'available'")
        if self.source_tier == 4 and self.status == "available":
            raise ValueError(
                "Tier 4 source cannot have status 'available' (ADR-022 §D3)"
            )
        return self


class PhotorealisticFidelity(BaseModel):
    """Photorealistic fidelity slot for a cell record."""
    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="available | pending | splat_pending | unavailable")
    source: Optional[str] = None
    captured_at: Optional[str] = None
    source_tier: Optional[int] = Field(None, ge=1, le=4)

    @model_validator(mode="after")
    def _validate_constraints(self) -> "PhotorealisticFidelity":
        if self.status not in ("available", "pending", "splat_pending", "unavailable"):
            raise ValueError(
                f"photorealistic.status must be one of: available, pending, splat_pending, unavailable. Got: {self.status!r}"
            )
        if self.status == "available" and self.source is None:
            raise ValueError("photorealistic.source must not be null when status is 'available'")
        if self.source_tier == 4 and self.status == "available":
            raise ValueError(
                "Tier 4 source cannot have status 'available' (ADR-022 §D3)"
            )
        return self


class FidelityCoverageUpdate(BaseModel):
    """Request body for PATCH /cells/{cell_key}/fidelity.

    Full replacement semantics — the entire fidelity_coverage JSONB field is
    overwritten with the body. Both structural and photorealistic are required.
    """
    model_config = ConfigDict(extra="forbid")

    structural: StructuralFidelity
    photorealistic: PhotorealisticFidelity


class CentroidECEF(BaseModel):
    x: float
    y: float
    z: float


class CentroidGeodetic(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class VerticalAdjacency(BaseModel):
    up: Optional[str] = None
    down: Optional[str] = None


class CellResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    canonical_id: str
    cell_key: str
    resolution_level: int
    cube_face: int
    face_grid_u: int
    face_grid_v: int
    edge_length_m: float
    area_m2: float
    distortion_factor: float
    centroid_ecef: CentroidECEF
    centroid_geodetic: CentroidGeodetic
    adjacent_cell_keys: list[str]
    parent_cell_id: Optional[str] = None
    human_alias: Optional[str] = None
    alias_namespace: Optional[str] = None
    friendly_name: Optional[str] = None
    semantic_labels: list[str] = []
    status: str
    schema_version: str
    created_at: str
    updated_at: str
    # Stage 2 — present on volumetric cells, omitted on surface cells.
    is_volumetric: Optional[bool] = None
    altitude_min_m: Optional[float] = None
    altitude_max_m: Optional[float] = None
    vertical_subdivision_level: Optional[int] = None
    vertical_parent_cell_id: Optional[str] = None
    vertical_adjacent_cell_keys: Optional[VerticalAdjacency] = None
    aviation_domain: Optional[bool] = None


# -------------------------------------------------------------------------
# Entities
# -------------------------------------------------------------------------

class EntityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_subtype: str = Field(..., pattern=ENTITY_SUBTYPE_PATTERN)
    primary_cell_id: str = Field(..., pattern=CELL_ID_PATTERN)
    metadata: Optional[dict[str, Any]] = None
    secondary_cell_ids: Optional[list[str]] = None
    human_alias: Optional[str] = Field(None, pattern=ALIAS_PATTERN)
    alias_namespace: Optional[str] = Field(None, pattern=NAMESPACE_PATTERN)
    friendly_name: Optional[str] = Field(None, max_length=200)
    semantic_labels: Optional[list[str]] = None

    @field_validator("human_alias")
    @classmethod
    def _normalise_alias(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v


class EntityResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    canonical_id: str
    entity_subtype: str
    primary_cell_id: str
    secondary_cell_ids: list[str] = []
    metadata: dict[str, Any] = {}
    human_alias: Optional[str] = None
    alias_namespace: Optional[str] = None
    friendly_name: Optional[str] = None
    semantic_labels: list[str] = []
    status: str
    schema_version: str
    created_at: str
    updated_at: str


# -------------------------------------------------------------------------
# Aliases
# -------------------------------------------------------------------------

class AliasBindRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_id: str = Field(..., pattern=CANONICAL_ID_PATTERN)
    alias: str = Field(..., pattern=ALIAS_PATTERN)
    alias_namespace: str = Field(..., pattern=NAMESPACE_PATTERN)

    @field_validator("alias")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()


class AliasRetireRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alias: str = Field(..., pattern=ALIAS_PATTERN)
    alias_namespace: str = Field(..., pattern=NAMESPACE_PATTERN)

    @field_validator("alias")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()


class AliasBindResponse(BaseModel):
    alias_id: str
    alias: str
    namespace: str
    canonical_id: str
    status: str
    effective_from: Optional[str] = None
    created: Optional[bool] = None


class AliasResolveResponse(BaseModel):
    canonical_id: str
    alias: str
    alias_status: str
    namespace: str
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None


class AliasRetireResponse(BaseModel):
    alias_id: str
    alias: str
    namespace: str
    canonical_id: str
    status: str
    effective_to: str


# -------------------------------------------------------------------------
# Namespaces
# -------------------------------------------------------------------------

class NamespaceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    namespace: str = Field(..., pattern=NAMESPACE_PATTERN)
    prefix: str = Field(..., pattern=PREFIX_PATTERN)
    initial_counter: int = Field(1, ge=1)


class NamespaceResponse(BaseModel):
    namespace: str
    prefix: str
    next_counter: int
    status: str
    created_at: str


# -------------------------------------------------------------------------
# Adjacency
# -------------------------------------------------------------------------

class AdjacencyNode(BaseModel):
    face: int
    i: int
    j: int
    cell_key: Optional[str] = None


class AdjacencyRingResponse(BaseModel):
    cell_key: str
    depth: int
    ring: list[AdjacencyNode]


class CellAdjacencyResponse(BaseModel):
    """
    Response for GET /cells/{key}/adjacency (Stage 2 shape).

    Surface cells: returns {cell_key, is_volumetric=false, lateral: [...]}
    Volumetric cells: additionally returns {vertical: {up, down}}.

    See ADR-015 §2.8.
    """
    model_config = ConfigDict(extra="allow")

    cell_key: str
    is_volumetric: bool
    lateral: list[str]
    vertical: Optional[VerticalAdjacency] = None


# -------------------------------------------------------------------------
# Health
# -------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    schema_version: str
    database: str
