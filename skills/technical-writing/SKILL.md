---
name: technical-writing
description: Write or review clear technical documentation, procedures, specifications, reports, and explanations in any format or location. Use beyond docs folders; project-documentation separately governs repository organization and metadata.
---

# Technical writing

Put the key result, required action, or decisive constraint first. Let a reader find what matters without reading every sentence.

## Choose a useful form

- Prefer numbered steps for procedures, bullets for parallel points, tables for comparisons or mappings, and diagrams for relationships, flows, or states.
- Nest numbered steps when a parent operation has meaningful substeps. Avoid deep nesting that hides sequence or responsibility.
- Minimize long prose paragraphs. Keep a short paragraph when it explains cause, rationale, or an exception better than fragmented bullets.
- Use diagrams to answer a concrete question. Label entities and connections consistently; provide a concise text equivalent. Decorative imagery does not replace technical evidence.
- Split documents into review-sized units with one coherent purpose. Start sections with their key point; avoid repeated summaries and boilerplate.

## Write precise sentences

- Apply ASD-STE100 principles: short sentences, simple grammar, active voice, imperative instructions, consistent technical names, and one intended meaning per term.
- Give one action per procedural sentence unless actions must occur together. Put the condition before the action when it determines applicability.
- Use familiar words. Define necessary domain terms and abbreviations once. Avoid idioms, metaphor, promotional claims, vague pronouns, and unnecessary noun chains.
- Preserve needed articles, subjects, and qualifiers. Do not shorten text until its meaning changes or its uncertainty disappears.
- Separate requirements, recommendations, observations, and examples. Identify who must act and what constitutes completion. State uncertainty and unsupported claims honestly.

These are selected STE principles, not a complete implementation of ASD-STE100. Its controlled vocabulary and writing rules require the applicable specification and validation for a formal compliance claim. Do not reproduce its dictionary/manual or label ordinary simplified writing as certified/compliant.

## Make procedures executable

1. State purpose, prerequisites, required permissions, and inputs before the first affected step.
2. Place a warning before the hazardous action. State the hazard, consequence, and avoidance action; use notes for information rather than hidden commands.
3. Give ordered actions with explicit conditions and concrete values or clearly named placeholders. Preserve exact commands, UI labels, units, and identifiers.
4. State expected results at checkpoints. Include failure/stop conditions and recovery or escalation when needed.
5. Check commands and claims against available evidence. Report validation limits; never invent successful execution or review.

For Markdown, use a single document title and logical heading levels, descriptive relative links within the repository, backtick code fences with language labels, and longer outer fences for nested examples. Follow existing lint configuration and verify rendering, links, and diagrams where relevant. A tooling exception belongs in the applicable profile, not a silent rewrite of shared guidance.

## Authoritative STE sources

Consult the [ASD Simplified Technical English Maintenance Group](https://asd-ste100.org/) and its [official FAQ](https://asd-ste100.org/STE_faq.html) when the task needs exact standard rules. The official site may restrict automated retrieval; disclose that limitation rather than substituting an unofficial copy as authoritative. ASD's [public introductory extract, hosted by the University of Macerata](https://docenti.unimc.it/f.raffi/teaching/2023/28609/files/file-da-scaricare-su-pc-e-portare-a-lezione-4-aprile-2) explains controlled terminology; it is historical Issue 7 material, not proof of current compliance.
