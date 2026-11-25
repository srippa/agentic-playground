# Architecture Decision Records (`docs/decisions/`)

Short (under 1 page) records capturing every meaningful design choice across Stages 0–6.

**Rule:** The coding agent drafts `docs/decisions/NNN-short-title.md` with `Status: proposed`. **Only the project owner marks a record `accepted`.**

## Index
- [001-runtime-and-wire-tap.md](./001-runtime-and-wire-tap.md) — Local 64 GB Runtime Strategy & Wire-Tap Transport (`Status: accepted`)

## Template (`NNN-short-title.md`)

```markdown
# NNN: Title
Date: YYYY-MM-DD · Stage: N · Status: proposed | accepted | superseded by NNN

## Context
What problem, what constraints.

## Options
1. ... (pros / cons)
2. ...

## Decision
What we chose.

## Why
The reasoning and evidence (link to wire dump, benchmark table, or trace).

## Consequences
What this makes easy or hard later.
```
