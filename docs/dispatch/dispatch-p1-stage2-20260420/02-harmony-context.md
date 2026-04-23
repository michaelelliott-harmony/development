# 02 — Harmony Context
## Aligned to Master Spec V1.1.0

---

## What Harmony Is

Harmony is the Universal Spatial Address Protocol for the physical
world — from seabed to sky. It is not a GIS viewer. It is not a
mapping platform. It is the canonical spatial substrate upon which
all applications that need to reason about physical space can be built.

**The foundational guarantee:** The same physical location always
produces the same Harmony address — forever, regardless of who derives
it or when. This determinism is an architectural guarantee.

---

## The Three North Stars

**North Star I — The Seamless World**
Complete elimination of tile-switching and polygon pop-in. Seamless
descent from orbital to street level, including vertically through
buildings. No visible boundaries. Continuous LOD streaming.

**North Star II — The GPS-Free Spatial Substrate**
Harmony becomes the canonical substrate for autonomous systems in all
three dimensions, seabed to sky. A drone navigating GPS-denied urban
airspace, a robot clearing a building floor by floor, a submarine
mapping a harbour approach — all within the same cell hierarchy.

**North Star III — The Spatial Knowledge Interface**
When a user asks an AI about a place, the world transforms around the
answer. The knowledge unfolds as the user travels through Harmony
toward the place being described. Extends across all six dimensions.

---

## Dimensional Architecture

| Dimension | Status |
|---|---|
| 3D — Volume | ADR-015 accepted. Stage 2 — YOU ARE BUILDING THIS |
| 4D — Time | Reserved at schema. Pillar 4. Design required. |
| 5D — Uncertainty | Conceptual. ADR required. |
| 6D — Semantics | Conceptual. ADR required. |

The governing rule: each dimension must be confirmed forward-compatible
with the next before activation. Stage 2 must not foreclose 4D.

---

## Design Philosophy

1. Wrap proven systems, own the semantics
2. Stability over cleverness
3. Determinism is sacred — same input always produces same output
4. Design for the hardest consumer first — AVs at 120km/h
5. Abstractions must outlast implementations
6. Forward compatibility is a gate, not a preference

---

## The HTTP API Contract

The Pillar 1 HTTP API is the formal boundary between the spatial
substrate and every other pillar. No downstream pillar imports
Pillar 1 Python modules directly. All interaction is through the
12 HTTP endpoints. This contract is immutable within a session.
