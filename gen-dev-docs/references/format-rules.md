# Format Rules (Strict)

Must follow exactly — these match the Oshiete-AI/dev-docs format.

1. **Language**: Default **English**. Switch to the user's project language only when the user requests it or the target repo's existing docs already use that language. Technical terms (SAML, Redis, SQL, GraphQL, etc.) always stay in English regardless of base language.
2. **Header metadata**: Use `>` blockquote — NOT a table.
3. **Section dividers**: `---` between every `## N.` section.
4. **⚠️ pattern**: `> ⚠️ {note}` under any provisional/deferred-to-implementer decision.
5. **ASCII flow diagrams**: Use `↓` `├` `└` `→` inside fenced code blocks (no language tag) for simple linear flows.
5a. **Mermaid diagrams**: Use ` ```mermaid ` for complex flows with branching, multiple actors, or state transitions. Choose based on complexity:
    - Simple linear flow → ASCII
    - Multiple branches / actors / states → Mermaid (`sequenceDiagram`, `flowchart TD`, `stateDiagram-v2`)
    - Both can coexist in the same section if helpful
6. **SQL**: ` ```sql ` fenced block.
7. **GraphQL**: ` ```graphql ` fenced block.
8. **Open questions in plan.md**: Table with `| # | Item | Detail |` columns (English) or project-language equivalents.
9. **Open questions in requirements.md**: Table with `| Item | Detail |` columns (English) or project-language equivalents.
10. **Cross-link**: plan.md links to requirements.md in the Links table; requirements.md shows Backlog/Figma in blockquote.
11. **Status**: plan.md always `Status: Not implemented (requirements phase)` (or the equivalent in project language) unless told otherwise.
12. **GitHub Issue not created**: Use `(Not yet created)` (or the project-language equivalent if not English).
13. **Skip optional sections**: Only generate sections for which user provided content.
14. **Output file paths**: `features/{feature-kebab-case}/requirements.md` and `features/{feature-kebab-case}/plan.md`.
