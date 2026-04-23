# 06 — Security Policy
## Non-Negotiables for This Session

---

## Absolute Rules

1. Secrets never in prompts, logs, code, or filenames
2. No direct commits to main — feature branch only
3. Migrations produced, not executed
4. No destructive operations without requires_approval: true
5. Source tree at 04_pillars/pillar-1-spatial-substrate/harmony/
   is the only place implementation code goes

## Branch Naming

agent/marcus-webb/p1-stage2-20260420

## Commit Format

[AGENT] MarcusWebb: {description} (task:p1-stage2-20260420)

## If You Detect a Security Issue

Stop immediately. Return outcome: security_violation with description.
Do not proceed until resolved.
