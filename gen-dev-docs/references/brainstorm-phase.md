# Brainstorm Phase (before generating docs)

Adapted from obra/superpowers brainstorming skill for doc generation.

**Default language**: English. Switch to the user's project language only when the user
requests it or the target repo's existing docs already use that language.

## Scope Check First (Phase 0)

Before asking detailed questions, check whether the feature is scoped for a single spec.
See `scope-check.md` for decomposition signals and the decomposition template.
If decomposition is needed, agree on the first sub-project with the user, then start the
questions below targeted at **only that sub-project**.

## Rules

- Ask ONE question at a time. Never bundle multiple questions.
- Prefer multiple-choice when possible.
- YAGNI: flag any scope that seems excessive.
- **Decide what to ask based on what you still don't understand** — there is no fixed question list.
  Stop asking when you have enough to propose approaches.
- HARD-GATE: do NOT generate any docs until user approves the design (section by section).

## What to Understand (not a checklist — use judgment)

To write good docs, you need to understand:
- Why this feature exists (business purpose)
- Who uses it and how
- What's in scope and what's explicitly out
- Key technical constraints or decisions already made
- Main flows (happy path + error cases)
- Any unresolved questions the team has

Ask only what you don't already know from context. If the user's initial message already
covers some of these, skip those questions.

---

## Approach Proposal (Phase 1.5)

Once you have enough understanding, propose 2–3 distinct approaches **before** moving to the design.
This prevents anchoring the user on the first idea that comes to mind.

### Rules
- Each approach must be **genuinely different** (not minor variations of the same idea)
- Lead with the recommended option + your reasoning
- Include tradeoffs: pros / cons / complexity
- If only one viable approach really exists, say so explicitly and explain why

### Template

```
## Approach Proposal

**Feature**: {1-line summary}

### Approach A: {name} (recommended)
- **Summary**: {1–2 lines}
- **Pros**:
  - {bullet}
- **Cons**:
  - {bullet}
- **Complexity**: Low / Medium / High

### Approach B: {name}
(same shape)

### Approach C: {name} (optional)
(same shape)

**Recommended**: A — {reason (business constraint, technical constraint, consistency with existing code, etc.)}

Which approach do you want to go with?
```

After the user picks an approach, proceed to section-by-section design.

---

## Section-by-section Approval (Phase 2) — HARD-GATE

After approach selected, present the design **ONE SECTION AT A TIME**.
Wait for explicit approval after each section before moving to the next.
This catches misalignment early instead of after a full-block summary.

### Sections (in order)

1. **Feature name, Purpose, Prerequisites**
2. **Scope** (In / Out)
3. **Use Case list** (UC-1, UC-2, ...)
4. **Main Flow** (happy path + key error cases)
5. **DB changes** (skip if none — state explicitly: "DB changes: none. Skipping.")
6. **Error / Security requirements** (brief — full detail comes in plan.md later)
7. **Open Questions**

### Per-section Message Template

```
## {Section name} ({N}/7)

{content scaled to complexity — a few sentences if simple, 200–300 words if nuanced}

Does this section look good?
```

### Rules
- One section per message. **Never bundle two sections.**
- If user requests changes → revise that section in the next message, re-ask approval.
- Skip optional sections explicitly with a one-line message, then move on.
- After all 7 sections approved, the design is complete. Move to "After Approval" below.

---

## After Approval → Collect Technical Details (Phase 3)

Only ask these AFTER all design sections are approved:

```
[Link info]
- Backlog URL + link text (write "Not yet created" if none)
- Figma URL + link text (write "Not yet created" if none)
- GitHub Issue URL (write "Not yet created" if none)
- Target repo name(s) (e.g., sophia-server, sophia-client)
- Last revision date

[Technical details] (best effort)
- SQL DDL (if there are table definitions)
- ASCII flow detail (library names, API paths, etc.)
- GraphQL / REST API design
- Error code list
```
