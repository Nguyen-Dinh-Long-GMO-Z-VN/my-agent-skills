# Plan Self-Review (before final output)

After generating both files, dispatch a subagent to review them before presenting to user.

## Dispatch Template

```
Task tool (general-purpose):
  description: "Review generated feature docs"
  prompt: |
    You are a document reviewer. Verify these docs are complete and ready.

    **Files to review:**
    - {PATH}/requirements.md
    - {PATH}/plan.md

    ## What to Check

    | Category | What to Look For |
    |----------|-----------------|
    | Completeness | TODOs, placeholders, "TBD", incomplete sections |
    | Consistency | Internal contradictions, conflicting requirements between files |
    | Clarity | Requirements ambiguous enough to cause wrong implementation |
    | Scope | Focused enough — not covering multiple independent subsystems |
    | YAGNI | Unrequested features, over-engineering |
    | Format | Follows format-rules (blockquote metadata, --- dividers, ⚠️ pattern, ASCII/Mermaid flows) |
    | Cross-links | plan.md links to requirements.md; requirements.md has Backlog/Figma in blockquote |
    | Plan tasks | Each task has a clear name, file paths, and enough context to implement without asking |

    ## Calibration

    Only flag issues that would cause real problems during implementation.
    Missing section, contradiction, or ambiguous requirement = issue.
    Minor wording, stylistic preferences = not an issue.

    Approve unless there are serious gaps.

    ## Output Format

    **Status:** Approved | Issues Found

    **Issues (if any):**
    - [File/Section]: [specific issue] — [why it matters]

    **Recommendations (advisory, do not block approval):**
    - [suggestions]
```

## After Review

- **Approved** → Present docs to user, ask to save to repo
- **Issues Found** → Fix inline, re-run review once, then present
- Never run more than 2 review cycles (fix obvious issues, move on)
