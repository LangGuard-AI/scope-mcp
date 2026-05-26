# Contributing to scope-mcp

This document is the source-of-truth contributor guide for human contributors and data reviewers. Some sections (particularly the Hard Rules and the 26-code regime allowlist) are also loaded by the `/scope-mcp:curate` skill at runtime to guide LLM-assisted data entry. Edits to these sections should preserve both human readability and the structured format the skill parses. When editing rule sections, be mindful that changes here affect LLM behavior.

The data is the project. The 80+ YAMLs in [`data/`](./data) are SCOPE's only source of truth — when you run an audit, the hosted server reads exactly those files and emits exactly what they say. So every correction, addition, and challenge to a classification directly improves the tool for everyone.

We especially want to hear from:

- **Practitioners** who've shipped agents touching one of these connectors and have first-hand opinions about which actions are dangerous, which are over-flagged, and which compliance regimes really apply in their context.
- **Compliance / GRC reviewers** who can sanity-check the regulatory regime tagging — particularly the contextual ones (HIPAA, GLBA, FERPA, NY DFS 500, FDA Part 11) that depend on how a customer deploys the platform.
- **Vendor engineers** who know their own MCP server's tool surface better than anyone outside the company. If we have your tool ids wrong, please tell us.
- **Users who hit `unmapped`** — if the audit flagged a tool SCOPE doesn't know about, that's a missing-data bug we want to fix.

You don't need to be a regulatory expert. "This feels off because…" is a useful issue.

## Two paths

### Path 1 — File a Data revision (recommended for feedback)

Use this when you've spotted something but don't want to author the YAML change yourself. We'll triage and either fix it or ask follow-up questions.

The repo ships a structured issue form at [**Data revision → New issue**](https://github.com/LangGuard-AI/scope-mcp/issues/new?template=data-revision.yml). The form has a single revision-kind dropdown that covers every type of correction we accept:

| Revision kind | Use this when… |
|---|---|
| **Misclassification** | An entry's risk level, regime tags, or `sod_concern` are wrong |
| **Hallucinated tool** | An action exists in our YAML but NOT on the real MCP server |
| **Missing tool** | The real MCP server has tools SCOPE doesn't classify |
| **Missing platform** | SCOPE doesn't know about a connector we should cover |
| **Confidence calibration** | Existing `confidence` is too high or too low |
| **Description / business_impact wording** | Factual or tone fix on the prose fields |
| **Schema / regime suggestion** | Propose adding a regime to the canonical 26-code allowlist |
| **Other** | Anything else; describe it in the rationale field |

The form's required fields are platform slug, proposed change, and rationale. Optional but very helpful: action id, the current YAML entry pasted as YAML, and an authoritative source URL (vendor MCP docs, regulator guidance, MCP server source code) backing the change. The form pre-fills the issue title with `[data]` and the `data` label so the triage queue stays clean.

[The Data revision form](https://github.com/LangGuard-AI/scope-mcp/issues/new?template=data-revision.yml) is the canonical entry point — bookmark it. Blank issues are disabled, but two contact links handle the cases that don't fit the form:

- **Question, general feedback, or operational discussion** → [scope-mcp@langguard.ai](mailto:scope-mcp@langguard.ai)
- **Sensitive disclosure (security, regulatory, customer-confidential)** → [scope-mcp@langguard.ai](mailto:scope-mcp@langguard.ai)

### Path 2 — Open a PR (for direct changes)

Fork the repo, branch off `main`, edit or add a file under [`data/`](./data), and open a PR.

### Schema reference (v1.2)

```yaml
schema_version: "1.2"
platform: <slug>
display_name: <Title Case Name>
source: langguard-editorial            # or community-<handle> for community PRs
updated: "<YYYY-MM>"
reference: https://...                 # OPTIONAL — canonical vendor MCP docs URL
server_version: "1.0.0"               # OPTIONAL — MCP server version or date last verified
server_website: https://...            # OPTIONAL — MCP server project URL (distinct from reference)
maintainer: user@example.com           # OPTIONAL — email or contact-form URL for the server maintainer
actions:
  - id: <platform>.<action>            # required
    object: <Object>                   # optional but recommended
    action: <action>                   # required (verbatim tool name OR slug, see below)
    id_form: verbatim                  # OPTIONAL — "verbatim" (default) or "capability"
    description: "..."                 # OPTIONAL — human-readable English description of the tool
    reference: https://...             # OPTIONAL — deep link to per-tool docs (falls back to top-level)
    category: <Category>               # required
    risk: <low|medium|high|critical>   # required
    business_impact: "..."             # required
    compliance: [<regimes>]            # required (may be [])
    sod_concern: <bool>                # required
    confidence: <high|medium|low>      # required
    access_methods: [<methods>]        # required
```

Files curated before May 2026 use `schema_version: "1.0"` or `"1.1"` and omit the newer fields — that's still valid. New PRs should use `"1.2"` and include `description` + `reference` where available. The v1.2 fields (`server_version`, `server_website`, `maintainer`) are optional — populate them only when you have a confirmed value.

There are three hard rules for new YAML data. PRs that violate them will be sent back for revision.

> Loaded by /curate skill

#### Rule 1 — Tool ids verbatim from the MCP server (with one documented escape hatch)

The `id` and `action` fields MUST be the literal tool name the MCP server exposes — case, vendor prefixes, and plurals preserved.

The right source is the connector's **published MCP `tools/list` documentation** (or the source code of the MCP server, if open-source, or a captured live `tools/list` response). The right source is **NOT** the vendor's REST API documentation — MCP servers often use a different naming convention and a different granularity than REST.

Concrete examples of what verbatim looks like in practice:

| Connector | Naming convention | Example id |
|---|---|---|
| Stripe, Linear, Asana, HubSpot | `snake_case`, unprefixed | `stripe.create_refund` |
| Notion | `kebab-case` with `notion-` prefix | `notion.notion-create-pages` |
| Atlassian Rovo | `camelCase` | `atlassian.createJiraIssue` |
| Mercury | `camelCase`, unprefixed | `mercury.listTransactions` |
| Mixpanel | Title-`Kebab-Case` | `mixpanel.Run-Query` |
| Snowflake Cortex | UPPER_SNAKE | `snowflake.SYSTEM_EXECUTE_SQL` |

Don't normalize, don't simplify, don't fix the upstream's "weird" choices — even kebab-case-with-vendor-prefix. The plugin matches on exact tool ids when audits run; mismatches turn into `unmapped` results that aren't useful to anyone.

##### Escape hatch — `id_form: capability`

A few connectors (Slack is the canonical example) operate a closed-source hosted MCP server, gate `tools/list` behind OAuth, and publish their tool surface in vendor docs only as **plain-language capability labels** ("Send a message", "Search messages/channels") rather than verbatim identifier strings. For these, exact-match audit is impossible until someone captures a real `tools/list`.

Rather than skip these platforms entirely, the schema permits a labelled fallback:

```yaml
- id: slack.send_message
  action: send_message                  # slug derived from the capability label
  id_form: capability                   # signals: NOT a verbatim tools/list name
  description: "Send a message"         # the verbatim capability label from vendor docs
  reference: https://docs.slack.dev/ai/slack-mcp-server
  ...
  confidence: medium                    # capability-form entries cap at medium
```

Rules for `id_form: capability`:

- Use only when the vendor publishes capability labels but not verbatim tool ids in any source you can reach (vendor docs, open-source server code, captured `tools/list`).
- The `description` field MUST hold the verbatim capability label as the vendor wrote it.
- The `id` and `action` SHOULD be the lower-snake-case slug of the capability label, prefixed with the platform slug — that's the convention the audit uses for fuzzy matching.
- Cap `confidence` at `medium`. The classification is reliable, but the `id` won't exact-match what `tools/list` actually returns, so audit results for these entries are intent-level rather than identifier-level.
- File a follow-up to refresh the entry to `id_form: verbatim` once the real tool surface becomes available (e.g. when the vendor publishes `tools/list` docs or someone captures it via OAuth).

If neither verbatim ids nor capability labels are available — i.e. the vendor publishes nothing about the tool surface at all — **[file a Data revision](https://github.com/LangGuard-AI/scope-mcp/issues/new?template=data-revision.yml) (kind = "Missing platform") instead of a PR** so we can decide together whether to skip the platform or wait for upstream docs.

#### `description` and `reference` (always optional, recommended for `verbatim` too)

These two fields are useful regardless of `id_form`:

- **`description`** — one-sentence human-readable summary of what the tool does. Helps reviewers and downstream UIs without forcing them to parse the id. For verbatim entries, copy or paraphrase the description from the vendor's `tools/list` schema. For capability entries, use the verbatim capability label.
- **`reference`** — URL pointing at the canonical documentation for this tool (per-action) or for the connector's MCP surface as a whole (top-level). Use the top-level `reference` for the connector's MCP overview page; use action-level `reference` only when the vendor has stable per-tool deep links.

Neither field affects audit logic today; both are surfaced in the audit response so consumers can show context and link out to vendor docs.

#### Rule 2 — `compliance:` uses only the 26 canonical codes

> Loaded by /curate skill

The closed allowlist:

```
APPI, CCPA, COPPA, COSO, CO_AI_ACT, EU_AI_ACT, FDA_PART_11, FEDRAMP,
FERPA, GDPR, GLBA, HIPAA, ISO_27001, ISO_42001, LGPD, NIST_AI_RMF,
NIST_CSF, NY_DFS_500, PCI, PIPEDA, PIPL, POPIA, PSD2, SOC2, SOX, UK_GDPR
```

**Canonical machine-readable list:** [`_meta/regimes.yml`](_meta/regimes.yml)

If a real concern doesn't fit one of these (e.g. TCPA, CAN-SPAM, BIPA, AML, KYC, BSA, state data-broker laws), **describe it in the `business_impact` prose** — don't invent a new code. The closed list keeps audit summaries comparable across platforms.

If you think a regime genuinely should be added to the canonical list, [file a Data revision](https://github.com/LangGuard-AI/scope-mcp/issues/new?template=data-revision.yml) with kind = "Schema / regime suggestion" first. Adding a code is a project-level decision, not a per-PR change.

##### Quick decision rules

- **Privacy regimes** (GDPR, UK_GDPR, CCPA, PIPEDA, LGPD, APPI, PIPL, POPIA): tag the full set whenever an action touches identifiable personal data. SaaS platforms typically hold data globally, so the default is "tag all eight" for any PII read/write/export.
- **Industry regimes** (HIPAA, PCI, GLBA, FERPA, COPPA): only when the data type matches. HIPAA on healthcare-context platforms; PCI on payment-card data; GLBA on financial-services personal data; FERPA on student records; COPPA on children's data.
- **Financial reporting** (SOX, COSO): on actions that affect financial reporting, revenue recognition, IT general controls on financial systems, or audit-log integrity for financial systems. Tag SOX and COSO together — COSO is the framework SOX is implemented against.
- **Security frameworks** (SOC2, ISO_27001): on actions affecting security/availability/processing-integrity/confidentiality controls. Pair SOC2 with ISO_27001 for most security-relevant writes — the controls overlap heavily. Add NIST_CSF for high-impact security controls (privilege escalation, secret management, audit-log tampering).
- **AI regulation — automated decisioning** (EU_AI_ACT, NIST_AI_RMF, CO_AI_ACT): only when the action itself is part of automated decisioning that affects an individual's rights or interests (profiling, automated hiring/credit/insurance/healthcare decisions, biometric ID). Most CRM/repo/messaging actions don't qualify.
- **AI regulation — AIMS controls** (ISO_42001): only on AIMS control-point actions — managing the AI model lifecycle (deploy/retire/rollback), AI access/permissions, training-data writes, AI configuration/guardrails, AI event logging, AI impact assessment, or onboarding third-party AI providers. Do **not** bundle `ISO_42001` with `ISO_27001` on every security write — Annex A is AI-specific, not generic infosec. A tool that merely runs inference is not an AIMS control point. An advisory-only action that a human approves before commit is not automated decisioning either.
- **Sector-specific** (FEDRAMP, NY_DFS_500, PSD2, FDA_PART_11): only when the platform is inherently in scope. FedRAMP-deployed gov cloud, NY-licensed financial institutions, EU payment-service providers, FDA-regulated electronic records.

When in doubt, omit. Wrong tags are worse than missing tags.

#### Rule 3 — Calibrated `confidence`

> Loaded by /curate skill

Be honest about how solid the classification is. The `confidence` field tells reviewers which entries to scrutinize before relying on the audit.

- **`high`** — Action is well-documented; data type and effect are unambiguous; regime tagging follows directly from the rules above; comparable actions exist on other platforms with consistent classification. Example: `salesforce.create_contact` (clearly PII write).
- **`medium`** — Action exists but its scope or data type is ambiguous; OR risk depends on context (e.g. "could touch PHI in healthcare orgs"); OR you applied a tag that's defensible but not certain. Example: `slack.upload_file` (risk depends on file content).
- **`low`** — You inferred behavior from incomplete docs; OR the platform has unusual semantics; OR the regime tagging required a judgment call you weren't sure about; OR the action is novel and has no analog among existing platforms.

When in doubt, downgrade. A correctly-flagged `medium` is more useful than an over-confident `high`.

#### Risk gradient

Apply strictly. Don't be lenient because a tool "feels routine."

- **`critical`** — irreversible destruction; direct financial-statement impact; privilege escalation; data exfiltration at scale (bulk PII export, mass DM read).
- **`high`** — single-record but sensitive (PII export of one record, role change, payment-data write, sharing-rule change).
- **`medium`** — typical business writes that touch important state but are reviewable/reversible.
- **`low`** — read-only-equivalent or low-impact reversible writes (create task, post message as bot, fork repo).

#### SoD (segregation of duties)

`sod_concern: true` only when one principal performing the action **bypasses** a control that normally requires two principals: self-approving a transaction, modifying audit logs, granting oneself elevated permissions, force-pushing to a protected branch, single-actor data destruction without recovery, etc.

#### `business_impact` style

One sentence, present tense, names the concrete consequence. Match the tone of `data/salesforce.yml`. Examples:

- ✅ "Posts a refund to the cardholder; touches payment rails and the GL."
- ❌ "This is a complex action that has many implications including financial reporting and customer trust." (vague, multi-clause)
- ❌ "Refunds are issued via Stripe's payment processing system." (describes mechanics, not impact)

#### PR checklist

Before opening:

- [ ] Tool ids are verbatim from authoritative MCP docs (not REST API names).
- [ ] `compliance:` arrays use only the 26 canonical codes.
- [ ] `confidence` is calibrated honestly; `low` entries are flagged in the PR description.
- [ ] `risk` matches the gradient rules.
- [ ] `business_impact` is one declarative sentence per action.
- [ ] You included a link to the authoritative tool-list source in the PR description.

## What happens after you submit

- **Data revision issues**: triaged by LangGuard within a few business days. Corrections we agree with usually land within a week. Track yours in the [`data` label](https://github.com/LangGuard-AI/scope-mcp/issues?q=is%3Aissue+label%3Adata).
- **PRs**: reviewed by LangGuard. We may suggest revisions to align with the rules above. Approved merges are deployed to production audits within 60 minutes (server-side cache TTL).
- All contributors are credited in the file's `source` field if the change is substantial. The default `source: langguard-editorial` is reserved for editorial maintenance; community-contributed entries should set `source: community-<your-handle>` or similar.

## Code of conduct

Be respectful and direct. Disagreements about classifications are welcome — bring evidence (vendor docs, customer experience, regulator guidance) and we'll work through it.

## Contact

- **Data corrections / proposed YAML changes**: [file a Data revision](https://github.com/LangGuard-AI/scope-mcp/issues/new?template=data-revision.yml).
- **Questions, general feedback, operational discussion**: [scope-mcp@langguard.ai](mailto:scope-mcp@langguard.ai).
- **Sensitive disclosures (security, regulatory, customer-confidential), commercial inquiries**: [scope-mcp@langguard.ai](mailto:scope-mcp@langguard.ai).
