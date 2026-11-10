# Content metadata

Use YAML frontmatter with the following fields. Omit optional empty objects. There are no timestamp fields; retain chronology through version history and decision links.

| Field | Values and meaning |
| --- | --- |
| `type` | `overview`, `guide`, `reference`, `architecture`, `runbook`, `decision`, `plan` |
| `status` | Decision: `proposed`, `accepted`, `rejected`, `superseded`; plan: `exploratory`, `proposed`, `active`, `completed`, `abandoned`; other types: `draft`, `active`, `deprecated`, `superseded` |
| `authority` | `informative`, `normative`, `exploratory`, `historical`; plans stay exploratory, draft/proposed content is not normative |
| `criticality` | `low`: orientation; `normal`: ordinary usage; `high`: errors can materially harm service, security, data, or people |
| `review.status` | `unreviewed`, `needs-review`, `verified` |
| `generated.by` | Optional actual generator/tool identity. Authorship/provenance, not approval |
| `generated.sources` | Required with generator: nonempty canonical source links or revision references |
| `generated.method` | Required with generator: reproducible generation command or method |
| `verified.by` | Actual reviewer identity, required only with a verified review |
| `verified.evidence` | Required with verification: nonempty links or reproducible check results |
| `verified.scope` | Required with verification: exactly what was checked, including material limitations |
| `superseded_by` | Required for superseded content: link to replacement |
| `extensions` | Profile-defined fields, documented by the profile; no temporal metadata |

All content requires `type`, `status`, `authority`, `criticality`, and `review.status`. Do not equate active with normative: active reference material can describe behavior without prescribing it. A plan can be active work while remaining exploratory knowledge. Proposed decisions remain informative or exploratory until acceptance evidence exists; accepted decisions may be normative or informative. Rejected/superseded decisions are historical.

High-criticality runbooks need verification of prerequisites, permissions, hazards, stop conditions, expected results, and recovery before operational reliance. Until that evidence exists, use `draft` and `needs-review`; prominently state that the procedure is not ready for operational use. Verification of prose alone does not verify the procedure. Other high-criticality content should state its review limitations too.

```yaml
---
type: runbook
status: draft
authority: informative
criticality: high
review:
  status: needs-review
---
```

For a generated region within a mixed document, label region-specific provenance adjacent to the region; do not imply the whole document is generated. Document-level `generated` covers the whole document only. A verified subsection does not justify whole-document `review.status: verified`; describe a narrower claim beside that subsection instead.

The JSON Schema validates field shape and lifecycle combinations. Review evidence truthfulness, source authority, region scope, and profile conflicts separately. Parse YAML without executing tags, reject duplicate keys, and validate the resulting object. A schema pass is not editorial or operational approval.
