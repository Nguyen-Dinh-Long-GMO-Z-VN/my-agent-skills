# plan.md Template

Default language: **English**. Switch to the user's project language only when the user
requests it or the target repo's existing docs already use that language. Technical terms
stay in English regardless.

```markdown
# {Feature Name} — Plan

> Target repository: {repo1}, {repo2}
> Status: Not implemented (requirements phase)
> Last updated: {YYYY-MM-DD}

## Links

| Type         | Link |
|--------------|------|
| GitHub Issue | {(Not yet created) or [#number](url)} |
| Requirements | [requirements.md](./requirements.md) |
| Backlog      | [{text}]({URL}) |
| Figma        | [{text}]({URL}) |

---

## Design

### Flow

```
[{Triggering user action}]
  ↓ {API call or trigger}
  {processing detail}
  ├ {branch A} → {result A}
  └ {branch B} → {result B}
```

### DB Changes

> ⚠️ Column names and types are tentative. Implementer makes the final call.

```sql
CREATE TABLE {table_name} (
  {column} {TYPE} {constraints},  -- {comment}
);
```

(Or: "No DB changes.")

### {Technical Section} (e.g., API Design / Backend / Frontend / Settings Schema)

> ⚠️ {note for any tentative / implementer-judgment item}

{Key decisions, interfaces, data flows relevant to implementation.}

### Security

| Aspect | Mitigation |
|--------|------------|
| {aspect} | {mitigation} |

### Error Handling

| Error code | User-facing message | Log output |
|------------|---------------------|------------|
| `{CODE}`   | "{message}"         | {log or —} |

### Open Questions

| # | Item | Detail |
|---|------|--------|
| 1 | {item} | ⚠️ {tentative decision}. Implementer makes the final call. |

---

## Implementation Plan

- [ ] **Task 1: {name}**
  - Files: `{exact/path/to/file}` (create / modify)
  - {key decision, constraint, or note implementer needs}

- [ ] **Task 2: {name}**
  - Files: `{exact/path/to/file}`
  - {note}

- [ ] **Task N: {name}**
  - Files: `{exact/path/to/file}`
  - {note}
```
