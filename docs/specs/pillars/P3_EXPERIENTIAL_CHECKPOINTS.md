# Pillar 3 — Experiential Checkpoints

**Owner:** Dr. Lin Park, Chief Rendering Architect
**Status:** Active — pre-dispatch, 2026-04-29
**Scope:** Subjective fidelity gates against which Pillar 3 build
milestones are judged. These are **observation tests**, not unit tests.
They measure whether the rendering experience is honest about itself.

---

## Why these exist

Frame-rate floors and motion-to-photon budgets tell us whether the
pipeline is fast. They do not tell us whether the experience is
continuous, surprising, or honestly representative of what the
substrate is doing. Those are perceptual properties. They are
detectable only by observers, and only by observers who have not
been pre-loaded with our framing.

We failed to instrument this on at least two prior projects in my
career. The result both times was a demo that engineers loved and
that no external observer could distinguish from a very good map.
This file exists so we do not repeat that.

Each checkpoint names the artefact under test, the **honest signal**
that determines pass/fail, and the observer profile required to
generate that signal. Internal review does not satisfy any
checkpoint here. The point is the unmediated reaction.

---

## P3-EC1 — Pillar 3 M1 completion

**What:** First orbital-to-regional descent.

**Criterion:** Does the transition feel continuous, or does it feel
like a loading sequence?

**Observer:** External, technically literate. Someone who has
written a renderer, shipped a game, or works in geospatial — but is
not a Harmony team member and has not been briefed on the cell
hierarchy or LOD strategy.

**Pass:** Observer describes the descent as a single motion, or
asks how the streaming hides the seams. They notice the
engineering, not the joins.

**Fail:** Observer pauses, blinks, or describes anything that
sounds like "loading," "popping," "tiles snapping in," or "now it's
finished loading." Any of these is a fail regardless of measured
frame rate.

**Target:** Month 10–11.

**Artefacts to capture:** Screen recording at native resolution,
observer's first sentence after the descent ends, observer's answer
to "what was that doing under the hood."

---

## P3-EC2 — Pillar 3 M3 completion

**What:** Full descent to street level on the Gosford pilot region.

**Criterion:** Does a non-technical observer react with surprise,
or do they recognise it as a very good map?

**Overlay:** WS-F open data reconstructed imagery applied for this
checkpoint (NSW Spatial Services 10cm aerial + GA 5m DEM, CC-BY).
Per DEC-023, the demo experience uses reconstructed imagery, not
Track 1 streaming mesh alone. This checkpoint tests the demo
configuration, not the production-only configuration.

**Observer:** External, non-technical. No prior Harmony exposure.
Not a developer, not a geospatial professional, not a friend of the
team.

**Pass:** Observer reacts with surprise — leans in, asks where the
data came from, asks whether they can go to a place they know.
Surprise is the signal.

**Fail:** Observer says "this is like Google Earth" or any
equivalent. Not because Google Earth is bad — it is excellent — but
because if our descent reads as a better-rendered Google Earth, we
have not yet delivered Cell Presence at this checkpoint. We have
delivered a map.

**Target:** Month 13–14.

**Artefacts to capture:** Screen recording, observer's first
unprompted sentence, the question they ask second.

---

## P3-EC3 — Pre-fundraise experiential audit

**What:** Three to five external observers, each shown the Pillar 3
M3 build independently. No Harmony team member narrates. No deck.
No framing. The build runs. The observer reacts. We listen.

**Criterion:** The unmediated reaction is the honest signal. Every
observer brings a different prior — some will react to the
geometry, some to the imagery, some to the motion, some to the
absence of a UI shell they expected. The aggregate of those
reactions is the audit result.

**Observer:** Three to five externals with no prior Harmony
exposure. Diverse enough that we are not just sampling our own
network. At least one should be in a domain we are not building
for.

**Pass:** A majority describe the experience in language that is
not "map," "globe," or "viewer." The vocabulary they reach for is
the audit's primary output.

**Fail:** A majority reach for prior-art vocabulary. If this
happens, the deck does not get shown. We rebuild the demo before
fundraising on it.

**Target:** Before any investor deck is shown.

**Artefacts to capture:** Each observer's full reaction transcript,
the vocabulary they used, the moment in the descent where the
reaction changed (or didn't).

---

## What this is not

These checkpoints do not replace performance gates. Frame-rate
floors, motion-to-photon budgets, arrival-time targets, and mobile
mid-tier device QA all continue to apply and are governed under
the rendering performance spec. An experiential checkpoint can
fail on a build that hits every numeric target. That is the point.

These checkpoints are also not focus groups. We are not asking
observers what they want. We are observing what they do.

---

## Logging

Each checkpoint produces an artefact bundle under
`docs/reports/p3-experiential/{checkpoint-id}-{YYYYMMDD}/`
containing recording, transcript, and a one-paragraph rendering
team note signed by the architect on duty.

I sign the EC3 note personally.

— Dr. Lin Park
Chief Rendering Architect
2026-04-29
