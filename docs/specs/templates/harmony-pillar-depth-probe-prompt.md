# HARMONY — Pillar Depth-Probe Prompt
## For use in each dedicated pillar chat to resolve final decisions before build

---

## How to Use This Prompt

1. Open the pillar's dedicated chat
2. Fill in the three bracketed fields at the top of the prompt:
   - `[PILLAR NAME AND NUMBER]`
   - `[PILLAR PURPOSE — one sentence from the spec]`
   - `[NORTH STARS THIS PILLAR SERVES — I, II, III or combination]`
3. Paste the entire prompt as your next message
4. Once the chat has responded, use the follow-up instruction at the bottom to trigger document generation

---

## THE PROMPT — PASTE AND CUSTOMISE BELOW THIS LINE

---

This session has a specific and bounded purpose. We are resolving the final open decisions for **[PILLAR NAME AND NUMBER]** of the Harmony Spatial Operating System before build begins.

The governing context for this session is the Harmony Master Specification V1.0, which is loaded in this project. Treat it as the authoritative reference for all responses. If anything in this session appears to conflict with the spec, flag it explicitly rather than resolving it silently.

**This pillar's purpose:** [PILLAR PURPOSE — one sentence from the spec]

**North Stars this pillar must serve:** [NORTH STARS THIS PILLAR SERVES]

---

Your role in this session is a senior technical architect and product strategist with deep experience in spatial computing, autonomous systems, and AI-native product design. You are not here to validate existing thinking. You are here to pressure-test it, surface what has not been named, and ensure that every decision made in this pillar is durable — capable of carrying the three North Stars without requiring a breaking change later.

Work through each of the following lenses in sequence. Be specific. Be direct. Where a decision is genuinely unresolved, name it as a decision required rather than papering over it with a general statement.

---

**Lens 1 — Purpose Stress Test**

Restate the purpose of this pillar in your own words, then push on it. Ask: is this the right purpose, or is it a symptom of a deeper function this pillar is actually serving? What would be lost if this pillar did not exist? What does it make possible for every other pillar that depends on it? What is the single most important thing this pillar must get right to serve all three North Stars?

---

**Lens 2 — Tool and Technology Audit**

What are the specific tools, technologies, frameworks, and external services that this pillar requires to function? For each one: is it a proven choice or an assumption? Is there a better alternative that has not been considered? What are the integration points with other pillars — what does this pillar consume from others, and what does it expose for others to consume? Are there any tool choices that would create a dependency that closes off one of the North Stars?

---

**Lens 3 — Decision Inventory**

Produce a numbered list of every decision this pillar requires before build can begin. For each decision: state the decision clearly, identify the options available, recommend the best option with a clear rationale, and flag whether this decision can be deferred without architectural consequence or must be resolved now. Do not conflate decisions that need to be made now with decisions that merely feel urgent. Be precise about which is which.

---

**Lens 4 — North Star Validation**

For each of the three North Stars that this pillar serves, answer the following: What specifically does this pillar contribute to that North Star? What would failure look like — what design choice or omission in this pillar would cause that North Star to be undeliverable? Is there anything in the current thinking for this pillar that creates a risk to any North Star, even a risk that seems small at this stage?

---

**Lens 5 — Inter-Pillar Dependencies**

Map this pillar's dependencies explicitly. Which pillars does this pillar depend on receiving inputs from, and what specifically does it need? Which pillars depend on this pillar, and what specifically must this pillar deliver to them? Are there any circular dependencies — situations where this pillar and another pillar each need the other to go first? If so, how should that be resolved? What is the correct build order relative to the other pillars?

---

**Lens 6 — The Gap Nobody Has Named**

Set aside everything in the current specification and ask: what is the most important thing about this pillar that has not yet been said? The capability that would make this pillar genuinely innovative rather than merely well-engineered. The failure mode that is currently invisible. The assumption that everyone is treating as settled but that deserves to be questioned. The feature or design principle that, if included, would make the other four pillars dramatically more powerful. Name it, explain it, and tell me whether it changes anything about how this pillar should be built.

---

**Lens 7 — Build Readiness Assessment**

On the basis of everything produced in this session: is this pillar ready to move into build? If yes, what is the first concrete task that should be handed to CoWork? If no, what specific decisions or inputs are still missing, and what is the fastest path to resolving them? Produce a plain-language summary of build readiness that a non-technical founder can act on immediately.

---

## FOLLOW-UP INSTRUCTION

Once the chat has responded to the depth-probe above, send this follow-up message to trigger document generation:

---

Thank you. Now produce two documents from this session using the templates below.

**Document 1** is the Pillar Brief — the instruction set that CoWork will read to understand what this pillar needs to deliver.

**Document 2** is the Project Management Brief — the structured input that the PM Agent will use to build this pillar into the master plan and Gantt chart.

Format both documents exactly as specified in the `HARMONY_PILLAR_BRIEF_TEMPLATE.md` file in the Project Context folder. Output both documents in full, in order, ready to be copied and saved.

---
