# MADR Template Guide

This reference provides detailed guidance on each section of the MADR (Markdown Any
Decision Record) template, including what constitutes good and bad content for each.

## Table of Contents

1. [Context](#context)
2. [Decision](#decision)
3. [Consequences](#consequences)
4. [Decision Drivers](#decision-drivers)
5. [Considered Options](#considered-options)
6. [Common Issues](#common-issues)

---

## Context

**Purpose:** Describes the background, system state, problem, or motivation that led to
the decision. It answers: *Why do we need to make a decision?*

**What belongs here:**
- Technical constraints and requirements
- Stakeholder needs and business goals
- Current system state and its limitations
- Project circumstances and related issues

**What does NOT belong here:**
- Detailed comparisons between solutions (those go in Considered Options)
- The final decision (that goes in Decision)
- Rationale for why one option beats another (that goes in Decision Drivers or Decision)

**Good example:**
> Our e-commerce platform currently uses SQLite, which works for development but does
> not scale to production workloads with hundreds of concurrent users. We need a
> reliable relational database that provides ACID guarantees and can handle increased
> load over the next two years.

**Bad example (too vague):**
> We need a database.

**Bad example (wrong content — this is a decision, not context):**
> We have decided to use PostgreSQL because it is the best relational database.

---

## Decision

**Purpose:** Clearly and explicitly states the final choice that was made. This is the
core of the ADR — it should be unambiguous and definitive.

**What belongs here:**
- The selected approach, accepted alternative, or implemented design
- A brief rationale for why this option was chosen over the alternatives

**What does NOT belong here:**
- Extended pros/cons comparisons (those go in Considered Options)
- Background information (that goes in Context)

**Good example:**
> We will use PostgreSQL as our primary relational data store. PostgreSQL provides the
> best balance of ACID compliance, feature richness, and scalability for our platform.
> The team's familiarity with SQL reduces the learning curve.

**Bad example (ambiguous):**
> We are leaning towards a relational database.

**Bad example (no rationale):**
> Use PostgreSQL.

---

## Consequences

**Purpose:** Explains the results, implications, trade-offs, and expected impact of
the decision — both positive and negative.

**What belongs here:**
- Positive effects (what we gain)
- Negative effects (what we lose or risk)
- Technical debt, performance implications, maintenance burden
- Follow-up actions required (migrations, training, new infrastructure)

**What does NOT belong here:**
- The decision itself (that goes in Decision)
- Alternative options' consequences (those go in Considered Options)

**Good example:**
> **Positive:** Strong data integrity guarantees; rich feature set reduces need for
> additional data stores; excellent community support.
>
> **Negative:** Requires dedicated operational effort for backups and replication;
> team needs to learn PostgreSQL-specific administration; migration from SQLite
> requires careful planning.

**Bad example (only positive):**
> PostgreSQL is great and will solve all our problems.

**Bad example (empty):**
> N/A

---

## Decision Drivers

**Purpose:** Lists the main criteria, goals, or forces that shaped the decision-making
process. It clarifies what mattered most when choosing between options.

**What belongs here:**
- Specific qualities that were prioritized (performance, cost, simplicity, etc.)
- Constraints that eliminated some options
- Regulatory or compliance requirements
- Team capabilities and preferences

**What does NOT belong here:**
- The actual comparison of options (that goes in Considered Options)
- The final decision (that goes in Decision)

**Good example:**
> - **Data consistency and integrity**: ACID compliance is critical for e-commerce.
> - **Mature ecosystem**: We need robust ORM support and monitoring tools.
> - **Team familiarity with SQL**: The team has strong SQL expertise.
> - **Cost-effectiveness**: Open-source solutions are preferred.

**Bad example (too generic):**
> - Performance
> - Cost
> - Quality

---

## Considered Options

**Purpose:** Enumerates alternative approaches that were evaluated and explains why
they were not chosen. This demonstrates the decision was informed by comparison.

**What belongs here:**
- At least two alternatives (the chosen option plus at least one rejected option)
- Brief pros and cons for each alternative
- Rejection justifications

**What does NOT belong here:**
- The final decision rationale (that goes in Decision, though a brief summary is OK)

**Good example:**
> ### PostgreSQL
> **Pros:** ACID compliance, rich features, strong community.
> **Cons:** Requires operational expertise.
>
> ### MongoDB
> **Pros:** Flexible schema, horizontal scalability.
> **Cons:** No ACID by default, team has less NoSQL experience.
>
> ### MySQL
> **Pros:** Widely used, good performance.
> **Cons:** Fewer advanced features than PostgreSQL.

**Bad example (no alternatives):**
> We chose PostgreSQL.

**Bad example (no pros/cons):**
> We considered MongoDB and MySQL but chose PostgreSQL.

---

## Common Issues

When checking ADRs, the following patterns frequently appear:

| Issue | Description | Fix |
|-------|-------------|-----|
| **Missing sections** | One or more MADR sections are entirely absent | Add the missing section with appropriate content |
| **Mislabeled content** | Content exists but under the wrong heading | Move content to the correct section |
| **Vague content** | Section exists but content is generic or placeholder-like | Replace with project-specific details |
| **Overlapping sections** | Same content repeated in multiple sections | Consolidate into the correct section |
| **No alternatives** | Considered Options is missing or has only one option | Add at least 2 alternatives with pros/cons |
| **No consequences** | Consequences section is empty or only lists positives | Add negative impacts and trade-offs |
| **Context includes decisions** | Context section contains solution comparisons or the decision itself | Move decision content to Decision section |