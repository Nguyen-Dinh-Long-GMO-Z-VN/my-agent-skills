# requirements.md Template

Default language: **English**. Switch to the user's project language only when the user
requests it or the target repo's existing docs already use that language. Technical terms
(SAML, Redis, API, etc.) stay in English regardless.

```markdown
# {Feature Name} — Requirements

> Last updated: {YYYY-MM-DD}
> Backlog: [{text}]({URL})
> Figma: [{text}]({URL})

---

## 1. Purpose & Background

### 1-1. Purpose
- {purpose}

### 1-2. Prerequisites
- **{key}**: {value}

---

## 2. Scope

### 2-1. In Scope
- {item}

### 2-2. Out of Scope
- {item} ({reason})

---

## 3. Assumptions & Constraints

### 3-1. Assumptions
- {assumption}
  > ⚠️ {note for any tentative decision}

### 3-2. Constraints
- {constraint}

---

## 4. Business Process / Use Cases

### 4-1. Use Case List

| UC-ID | Use Case | Actor |
|-------|----------|-------|
| UC-1  | {name}   | {actor} |

### 4-2. Use Case Details

#### UC-1: {name}
- Given: {precondition / state}
- When: {action}
- Then:
  - {result}
  - {result on failure, if any}

---

## 5. Screen / UI Requirements

### 5-1. {Screen name}
- **{field/element}**: {description}

---

## 6. {Notification / Batch Requirements} (if any)

### 6-1. {Batch name}
- Trigger timing: {timing}
- Recipients: {audience}

---

## 7. Security Requirements
- {requirement}

---

## 8. Error Handling

| Error type | User-facing message | Notes |
|------------|---------------------|-------|
| {name}     | "{message}"         | {notes} |

---

## 9. Open Questions

| Item | Detail |
|------|--------|
| {item} | {detail} |
```
