# WS-A — Cesium Reframing Memo

**Author:** Dr. Lin Park, Chief Rendering Architect
**For:** Mikey Elliott (founder), Dr. Mara Voss, Dr. Kofi Boateng
**Date:** 2026-04-29
**Status:** Reframing input to WS-A. Not a partnership term sheet.

---

## The reframe

WS-A as currently scoped reads as a vendor evaluation: *is Cesium
willing to collaborate, and on what terms?* That is the wrong
question. It puts Harmony in the position of a buyer assessing a
supplier, when the architectural reality is the opposite shape.

The right framing:

> Cesium has the best renderer in the world but no substrate.
> Harmony has the substrate but is not a renderer.
> The combination is stronger than either alone.

WS-A should be conducted as a **renderer + substrate partnership
conversation**, not a vendor evaluation.

---

## Why this matters

If we walk into the conversation as a buyer, we end up negotiating
about access, licensing, and integration support. We win nothing
strategic. The cell primitive becomes a payload Cesium happens to
render, which makes Harmony a CesiumJS application — interesting,
but not architecturally distinct.

If we walk in as a peer with a substrate they do not have and
cannot easily build, we negotiate about **whose addressing model
the integrated stack adopts**. That is the only conversation that
matters.

Cesium's strength is 3D Tiles and a rendering engine that has been
hardened against geospatial reality for over a decade. We are not
going to out-render them. We should not try. Their renderer is
the asset.

Harmony's strength is the cell — addressable, stateful,
multi-fidelity, planet-scale, with a substrate-level identity
model and an emerging Live Substrate Service. They cannot
easily build that. Their LOD model is tile-tree-shaped and
optimised for static asset delivery. The cell is something else.
That is the asset.

Neither side gets to the planetary spatial operating system
alone. The combined stack does.

---

## Target outcome of WS-A

**Cesium adopts the Harmony cell addressing protocol as their LOD
pre-fetch layer.**

That is the win condition. Concretely:

- Cesium continues to render via 3D Tiles. Unchanged.
- Cesium's pre-fetch and streaming logic addresses content via
  Harmony cell keys, not tile coordinates. The cell becomes the
  stable identifier the renderer asks for.
- Harmony's Live Substrate Service answers those requests with
  cell-addressable streams (geometry, fidelity coverage, live
  state). 3D Tiles becomes one of several payload formats a cell
  can resolve to.
- Cell-addressable streaming primitives sit as **architectural
  peers to 3D Tiles**, not as a layer beneath them.

This is the only outcome that justifies the engineering cost of
the partnership on the Harmony side. Anything weaker and we are
building a Cesium plugin.

---

## What we are not asking for

- We are not asking Cesium to abandon 3D Tiles. 3D Tiles is good.
  It is a payload format the cell can resolve to.
- We are not asking Cesium to adopt our renderer. We do not have
  one in the sense they do, and we are not trying to build one in
  that sense.
- We are not asking for a co-marketing arrangement. The
  conversation is architectural.

---

## What we are willing to give

- Cell addressing protocol published as an open spec. Not a
  Harmony-internal contract.
- OGC engagement on cell-addressable streaming as a peer
  primitive. Boateng leads. We are willing to do the standards
  work, not just the marketing.
- 3D Tiles as a first-class payload format inside the cell
  fidelity model. Not grudgingly — actually first-class.
- Reference implementation of the Cesium-side adapter, written
  by us, against their integration points.

---

## How the conversation is conducted

- Boateng faces outward — owns the standards-and-relationship
  surface. He has the strategic measure for this.
- I face inward and am consulted on architectural compatibility.
  If a term is proposed that subordinates the cell primitive to
  3D Tiles in the integrated stack, I will surface it as a
  failure condition before terms are signed.
- Founder owns the partnership strategy and any commercial terms.
  I do not.

---

## What success looks like, in a sentence

Cesium asks for cells by key, the Live Substrate Service answers,
and the cell is the unit both sides reason about. We meet at the
addressing layer, and 3D Tiles continues to be the rendering
backbone for one of the fidelity tiers.

## What failure looks like

A partnership that produces an integration in which Harmony
content is delivered to Cesium as a 3D Tiles tileset and the cell
exists only on our side of the wire. That is a failure mode I
will not sign off on. We would be better off pursuing OGC
membership independently and publishing our own splat streaming
protocol.

— Dr. Lin Park
Chief Rendering Architect
2026-04-29
