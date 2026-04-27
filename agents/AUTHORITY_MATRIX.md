# AUTHORITY_MATRIX.md
## Harmony Development Team — Decision Authority and Routing Table
## Every agent reads this document. Routing decisions are made from this table.

---

## Who Decides What

| Domain | Authority | Can Decide Without Mikey | Escalates to Mikey When |
|---|---|---|---|
| Spatial architecture | Dr. Mara Voss | Yes | Irreversible changes, North Star pivots |
| Security policy | Elena Márquez-Reid | Yes | Defence pathway, legal/regulatory, exceptions |
| File routing / naming | Marcus Webb | Yes — consults project structure doc | Never |
| ADR acceptance | Dr. Mara Voss | Yes — implementation ADRs | Design ADRs with major consequences |
| Sprint task assignment | Marcus Webb | Yes | Never |
| Migration execution | Mikey only | No — always a gate | N/A |
| External API connections | Elena then Mikey | Elena approves; Mikey gates execution | Always |
| Test pass/fail | QA Agent | Yes | Regressions in production tests |
| Code review approval | Reviewer | Yes — non-destructive changes | Destructive operations always |
| Rendering architecture (Pillar 3) | Dr. Lin Park | Yes | Strategic positioning conflicts, capital decisions exceeding agreed thresholds, partnership terms that affect cell primitive integrity |
| Live Substrate Service architecture | Dr. Lin Park | Yes | Same as above |

---

## Ambiguity Routing

When an agent encounters a question, route to:

| Question Type | Route To |
|---|---|
| File path or naming convention | Marcus Webb (checks project structure doc) |
| Architectural compatibility | Dr. Mara Voss |
| ADR gap | ADR Agent drafts → Dr. Voss accepts |
| Security policy | Elena Márquez-Reid |
| Scope ambiguity | Marcus Webb → Dr. Voss if unresolvable |
| Irreversible action | Marcus Webb → Telegram to Mikey |
| North Star conflict | Dr. Voss → Telegram to Mikey |
| Rendering pipeline architecture | Dr. Lin Park |
| Mobile delivery / latency / GPU concerns | Dr. Lin Park |
| Live Substrate Service questions | Dr. Lin Park |
| Cell Presence implementation questions | Dr. Lin Park |
| Live region protocol or feed binding questions | Dr. Lin Park |
| Cesium partnership architectural compatibility | Dr. Lin Park (consulted by Boateng on terms) |

---

## The Three Absolute Gates — Always Mikey

**Gate 1:** Any migration that drops columns, tables, or alters data types on populated tables.
**Gate 2:** Any operation that writes to an external API or transmits data outside Harmony.
**Gate 3:** Any decision that requires changing the fundamental direction of a pillar.

---

## Ambiguity Is Not an Excuse to Stop

Route the question. Receive the answer. Continue. The only valid reason to stop
entirely is a safety boundary violation or an absolute gate condition.

If you cannot determine the correct authority: route to Marcus Webb.
