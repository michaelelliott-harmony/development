# Harmony Pillar 2 — Source Adapter Layer
# Adapters are format/protocol-specific readers that emit raw features.
# They know nothing about Harmony semantics.
from harmony.pipelines.adapters.base import SourceAdapter, RawFeature

__all__ = ["SourceAdapter", "RawFeature"]
