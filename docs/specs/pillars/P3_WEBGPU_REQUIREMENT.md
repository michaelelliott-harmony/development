# Pillar 3 — WebGPU Requirement

**Owner:** Dr. Lin Park, Chief Rendering Architect
**Status:** Binding requirement on Pillar 3 build dispatch
**Companion to:** `HARMONY_RENDERING_ARCHITECTURE_PLAN_V1_0.docx`
**Date:** 2026-04-29

The Rendering Architecture Plan V1.0 is held in `.docx` form and is
not ergonomic to amend inline. This note is the binding addendum
covering the WebGPU question. It is normative.

---

## Requirement

WebGPU is a **hard requirement** for the Track 2 Gaussian splatting
render path.

It is **not** a migration path.
It is **not** a future enhancement.
It is **not** an optimisation we will reach for later.

Pillar 3 ships with WebGPU support. A Pillar 3 client without
WebGPU is not a Pillar 3 client. It is a Track 1 client.

WebGL2 is acceptable **only** for the Track 1 production
infrastructure path — streaming progressive mesh per DEC-022. A
WebGL2 client renders Track 1. A WebGPU client renders Track 1 and
Track 2.

There is no WebGL2 fallback for Track 2. We do not pretend to
deliver Cell Presence at any tier above Cell Witness on a renderer
that cannot do it. Honesty about the device's capability is
substrate-level, not a UX afterthought.

---

## Rationale — failure mode named first

WebGL2 lacks the compute shader model needed for efficient splat
rasterisation at the splat counts we require. The failure mode if
we ignore this:

1. We attempt 3D Gaussian splat rendering on WebGL2 by emulating
   compute with fragment-shader passes and CPU-side sorting.
2. At low splat counts (<100k) on flagship devices over fast
   networks, this looks like it works. The demo passes.
3. At production splat counts (millions per cell, multiple cells
   in view) on a mid-tier Android phone on congested 4G, the CPU
   sort dominates frame time, the GPU stalls waiting for the
   sorted index buffer, motion-to-photon collapses, and Cell
   Presence is degraded to a slideshow.
4. The bug surfaces at integration testing under load, after
   client architecture has been written against the assumption
   that "it works on WebGL2." Reversing that assumption is a
   rewrite.

I have watched the equivalent of this failure mode play out on at
least two mobile rendering projects, both times because someone
optimised for the flagship device demo and the mid-tier reality
was discovered too late. We are not doing that here.

---

## What WebGPU buys us

- Compute shaders for splat sort and culling. Sort runs on the GPU
  in parallel with rasterisation prep, not as a CPU-side blocker.
- Storage buffers and bind groups that map cleanly onto a
  per-cell splat resource model. The cell primitive becomes a
  GPU-resident resource group, not a stream of attribute updates.
- A path to indirect draw and culling on GPU, which is how we keep
  the fusion arbitration layer honest at high cell counts.
- A modern shader language (WGSL) that is debuggable. WebGL2
  GLSL debugging on mobile is a nightmare we do not need to
  re-enter.

---

## Device coverage reality

This is the bit that requires honesty.

WebGPU on iOS: Safari shipped WebGPU enabled by default. Coverage
on supported Apple silicon devices is the path of least resistance.

WebGPU on Android: Chrome ships WebGPU on devices with capable
drivers. Coverage is real but is **not** universal across the
mid-tier Android population we care about. Some mid-tier SoCs
either lack a compliant Vulkan driver or have a known-broken one.

Implication: a meaningful subset of mid-tier Android users will
not get Track 2. They get Track 1, which is by design Cell
Witness with structural fidelity. We do not silently degrade — we
report the tier they are receiving, and we do not lie about it.
This is a substrate-level honesty contract, not a UX choice.

The mobile client architecture must therefore:

1. Detect WebGPU availability at session start.
2. Negotiate the available Cell Presence tier with the Live
   Substrate Service based on detected capability.
3. Surface the tier honestly to Pillar 5 so the interaction layer
   never claims a fidelity the client cannot render.
4. Persist the negotiated tier across a session. We do not hop
   tiers mid-descent.

---

## What this rules out

- Targeting WebGL2 for any splat rendering. No.
- Shipping a "WebGPU coming soon" Pillar 3 v1. No.
- Hiding the tier from the user when capability is reduced. No.
- Treating the WebGPU requirement as something Pillar 5 negotiates
  at runtime without substrate involvement. The Live Substrate
  Service owns tier negotiation.

---

## What remains open

- Specific minimum feature-level subset of WebGPU we depend on
  (timestamp queries optional; storage buffers required;
  read-write storage textures required for the splat sort kernel
  we are evaluating). Spec lands with the Track 2 prototype.
- Splat-count budget per cell on the mid-tier WebGPU baseline
  device we adopt as the QA reference. To be measured, not
  guessed. Prototype gates this.
- Behaviour when WebGPU is present but the device is thermally
  throttling. Likely answer: tier-down to Track 1 mid-session
  with explicit user-visible signal. Not "silently render fewer
  splats."

These open questions do not weaken the requirement. They are
sharpened by it.

---

## Authority

This requirement is binding under my authority over Pillar 3
rendering pipeline architecture (backend selection) and the
mobile client architecture (adaptive transmission). It does not
require cross-pillar sign-off because it does not modify any
contract Pillar 1, Pillar 2, Pillar 4, or Pillar 5 depends on. It
modifies only how Pillar 3 renders.

If a downstream pillar believes WebGPU dependency creates a
constraint they cannot accept, raise it and I will engage. I will
not weaken the requirement to hide a tier mismatch the substrate
should be reporting honestly.

— Dr. Lin Park
Chief Rendering Architect
2026-04-29
