# SCOPE YAML schema reference

This document describes the schema for the per-platform YAML files in [`data/`](./data). These files are the canonical source of truth for the hosted SCOPE MCP server — the audit tool reads them directly and emits exactly what they contain.

For contribution rules (verbatim ids, closed regime allowlist, calibrated confidence), see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Schema versions

| Version | Introduced | What changed |
|---|---|---|
| `1.0` | Launch | Base schema. All fields below except `description`, `reference` (action-level), and `id_form`. |
| `1.1` | May 2026 | Added optional `description`, `reference` (action-level and top-level), and `id_form`. |
| `1.2` | May 2026 | Added optional `server_version`, `server_website`, and `maintainer`. |

Files using `1.0` or `1.1` are still valid. New files and updates should use `1.2`.

## Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | string | yes | `"1.0"`, `"1.1"`, or `"1.2"`. |
| `platform` | string | yes | Lowercase slug used as the namespace prefix for all action ids (e.g. `salesforce`, `stripe`, `slack`). |
| `display_name` | string | yes | Title-case human-readable platform name. |
| `source` | string | yes | `langguard-editorial` for LangGuard-maintained entries, or `community-<handle>` for community contributions. |
| `updated` | string | yes | `"YYYY-MM"` — month the file was last substantively edited. |
| `reference` | string | no | *(v1.1)* URL to the platform's canonical MCP documentation. Falls back as the default `reference` for actions that don't specify their own. |
| `server_version` | string | no | *(v1.2)* Version of the MCP server software (e.g. `"2.1.0"`) or date last verified (e.g. `"2026-05"`). Prefer a version string when the server publishes one. |
| `server_website` | string | no | *(v1.2)* URL of the MCP server project (GitHub repo, product page, etc.). Distinct from `reference`, which points to MCP tool documentation. |
| `maintainer` | string | no | *(v1.2)* Contact for the MCP server maintainer — an email address or URL to a contact form. |
| `actions` | list | yes | Array of action entries (see below). |

## Action fields

Each entry in the `actions` list describes one tool the MCP server exposes.

| Field | Type | Required | Since | Description |
|---|---|---|---|---|
| `id` | string | yes | 1.0 | `<platform>.<action>` — the tool's identifier. Must be verbatim from the MCP server's `tools/list` unless `id_form: capability` (see below). |
| `action` | string | yes | 1.0 | The action portion of the id (after the dot). |
| `object` | string | no | 1.0 | The domain object the action operates on (e.g. `Refund`, `Contact`, `Org`). |
| `id_form` | string | no | 1.1 | `verbatim` (default) or `capability`. Controls how the id is interpreted — see [id_form](#id_form). |
| `description` | string | no | 1.1 | One-sentence human-readable summary of what the tool does. For `capability` entries, this holds the vendor's verbatim capability label. |
| `reference` | string | no | 1.1 | URL to vendor documentation for this specific tool. Overrides the top-level `reference` when present. |
| `category` | string | yes | 1.0 | Functional grouping (e.g. `Financial`, `Identity & Access`, `Messaging`). Free-form but should be consistent within a platform file. |
| `risk` | enum | yes | 1.0 | `low` \| `medium` \| `high` \| `critical` — see [Risk gradient](#risk-gradient). |
| `business_impact` | string | yes | 1.0 | One sentence, present tense, naming the concrete consequence of the action. |
| `compliance` | list | yes | 1.0 | Array of regime codes from the [25-code allowlist](#compliance-regimes). May be empty (`[]`). |
| `sod_concern` | boolean | yes | 1.0 | `true` when a single principal performing this action bypasses a control that normally requires two — see [SoD](#segregation-of-duties). |
| `confidence` | enum | yes | 1.0 | `high` \| `medium` \| `low` — see [Confidence](#confidence). |
| `access_methods` | list | yes | 1.0 | How the action can be invoked: `REST`, `MCP`, `CLI`, etc. |

## Enums

### Risk gradient

| Level | Criteria | Examples |
|---|---|---|
| `critical` | Irreversible destruction; direct financial-statement impact; privilege escalation; bulk data exfiltration. | `stripe.create_refund`, `salesforce.deploy_metadata`, `salesforce.assign_permission_set` |
| `high` | Sensitive single-record operations: PII export, role change, payment-data write, sharing-rule change. | `salesforce.run_soql_query`, `slack.search_messages`, `github.merge_pull_request` |
| `medium` | Typical business writes that touch important state but are reviewable and reversible. | `salesforce.create_scratch_org`, `hubspot.update_deal` |
| `low` | Read-only-equivalent or low-impact reversible writes. | `slack.send_message`, `github.list_issues`, `notion.notion-search` |

### Confidence

| Level | Meaning |
|---|---|
| `high` | Action is well-documented; data type and effect are unambiguous; regime tagging follows directly from established rules. |
| `medium` | Scope or data type is ambiguous, risk depends on deployment context, or `id_form: capability` applies. |
| `low` | Behavior inferred from incomplete docs, or the regime tagging required a judgment call. |

When in doubt, downgrade. A correctly-flagged `medium` is more useful than an over-confident `high`.

### id_form

| Value | Meaning |
|---|---|
| `verbatim` | *(default)* The `id` and `action` are the literal tool name from the MCP server's `tools/list`. Audit matches on exact string equality. |
| `capability` | The vendor doesn't publish verbatim tool ids. The `id` is a slug derived from a capability label; `description` holds the vendor's verbatim label. Audit match is intent-level, not identifier-level. `confidence` must be capped at `medium`. |

Use `capability` only when no verbatim source exists (vendor docs, open-source server code, or a captured `tools/list` response). See [CONTRIBUTING.md](./CONTRIBUTING.md#escape-hatch--id_form-capability) for full rules.

### Segregation of duties

`sod_concern: true` only when one principal performing the action **bypasses** a control that normally requires two: self-approving a transaction, modifying audit logs, granting oneself elevated permissions, force-pushing to a protected branch, single-actor data destruction without recovery, etc.

## Compliance regimes

A closed allowlist of 25 canonical codes. The `compliance` array on each action must draw exclusively from this list.

| Category | Codes |
|---|---|
| **Privacy** | `GDPR`, `UK_GDPR`, `CCPA`, `PIPEDA`, `LGPD`, `APPI`, `PIPL`, `POPIA` |
| **Industry / sector data** | `HIPAA`, `PCI`, `GLBA`, `FERPA`, `COPPA` |
| **Financial reporting** | `SOX`, `COSO` |
| **Security frameworks** | `SOC2`, `ISO_27001`, `NIST_CSF` |
| **AI regulation** | `EU_AI_ACT`, `NIST_AI_RMF`, `CO_AI_ACT` |
| **Sector-specific** | `FEDRAMP`, `NY_DFS_500`, `PSD2`, `FDA_PART_11` |

Concerns that don't map to one of these codes (e.g. TCPA, AML, BIPA) should be described in `business_impact` prose instead. To propose adding a new code, [file a Data revision](https://github.com/LangGuard-AI/scope-mcp/issues/new?template=data-revision.yml) with kind = "Schema / regime suggestion".

## Annotated example

```yaml
schema_version: "1.2"
platform: stripe
display_name: Stripe
source: langguard-editorial
updated: "2026-05"
reference: https://stripe.com                    # platform-level MCP docs
server_version: "2.1.0"                          # version of the MCP server software
server_website: https://github.com/stripe/agent-toolkit  # MCP server project URL
maintainer: support@stripe.com                   # email or contact-form URL
actions:
  - id: stripe.create_refund                     # verbatim from Stripe MCP tools/list
    object: Refund
    action: create_refund
    # id_form omitted → defaults to "verbatim"
    description: "Moves money back to the customer; direct GL impact and chargeback exposure."
    # reference omitted → falls back to top-level
    category: Financial
    risk: critical                               # irreversible financial action
    business_impact: "Moves money back to the customer; direct GL impact and chargeback exposure."
    compliance: [SOX, COSO, PCI, SOC2, ISO_27001, PSD2]
    sod_concern: true                            # single actor can issue refund without approval
    confidence: high                             # well-documented, unambiguous effect
    access_methods: [REST, MCP]
```
