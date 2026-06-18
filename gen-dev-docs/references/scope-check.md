# Scope Check (Phase 0)

Before brainstorming details, check whether the feature fits a single spec.
"Simple" features rarely need decomposition; large features almost always do.

## Decomposition Signals

| Signal | Example | Recommendation |
|--------|---------|----------------|
| Multiple independent subsystems | "auth + billing + dashboards" | 1 spec per subsystem |
| Different actor groups with non-overlapping flows | "admin import + student preview + parent notification" | 1 spec per actor flow |
| Mixed transactional + analytical features | "booking form + BI report" | Split into 2 specs |
| Multiple external integrations as separate features | "Slack integration + Google Calendar integration" | 1 spec each |

## Signals that are OK (no decomposition needed)

- Multiple storage layers serving one feature (MySQL + Redis cache + S3)
- Frontend + backend + batch job tightly coupled to one user-facing capability
- Multiple error cases / edge cases of the same flow
- Multiple roles using the **same** flow (admin and teacher viewing the same list)

## Decision Rule

Ask: **"Can each piece be built, tested, and shipped independently?"**
- YES → decompose (each piece needs its own spec)
- NO → one spec is fine

## Decomposition Output Template

```
## The scope is broad — proposing a split into sub-projects:

1. **{sub-feature-1}** — {1-line purpose}
2. **{sub-feature-2}** — {1-line purpose}
3. **{sub-feature-3}** — {1-line purpose}

Dependencies: {brief, e.g. "2 depends on 1"}
Let's start with **{sub-feature-1}**. Sound good?
(The rest will get their own specs separately.)
```

After user agreement, proceed to Phase 1 (Brainstorm) with **only the first sub-project**.
Other sub-projects get their own gen-dev-docs run later.
