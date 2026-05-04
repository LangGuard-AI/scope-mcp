# Contributing to scope-mcp

The data is the project. The 80+ YAMLs in [`data/`](./data) are SCOPE's only source of truth — when you run an audit, the hosted server reads exactly those files and emits exactly what they say. So every correction, addition, and challenge to a classification directly improves the tool for everyone.

We especially want to hear from:

- **Practitioners** who've shipped agents touching one of these connectors and have first-hand opinions about which actions are dangerous, which are over-flagged, and which compliance regimes really apply in their context.
- **Compliance / GRC reviewers** who can sanity-check the regulatory regime tagging — particularly the contextual ones (HIPAA, GLBA, FERPA, NY DFS 500, FDA Part 11) that depend on how a customer deploys the platform.
- **Vendor engineers** who know their own MCP server's tool surface better than anyone outside the company. If we have your tool ids wrong, please tell us.
- **Users who hit `unmapped`** — if the audit flagged a tool SCOPE doesn't know about, that's a missing-data bug we want to fix.

You don't need to be a regulatory expert. "This feels off because…" is a useful issue.

## Two paths

### Path 1 — Open an issue (recommended for feedback)

Use this when you've spotted something but don't want to author the YAML change yourself. We'll triage and either fix it or ask follow-up questions.

Open an issue at [github.com/LangGuard-AI/scope-mcp/issues/new](https://github.com/LangGuard-AI/scope-mcp/issues/new). Some templates that work well:

**Misclassification** — "This action is wrong"

> **Tool**: `slack.read_direct_messages`
> **Current classification**: `risk: critical`, `compliance: [GDPR, UK_GDPR, CCPA, PIPEDA, LGPD, APPI, PIPL, POPIA, HIPAA, SOC2, ISO_27001, NIST_CSF]`
> **Suggested change**: HIPAA shouldn't be a default tag — only a fraction of Slack workspaces are HIPAA-covered.
> **Reasoning**: …

**Missing platform** — "SCOPE doesn't know about X"

> **Platform**: `customer-io`
> **Authoritative MCP tool list**: <link to vendor MCP docs page>
> **Why it matters**: agents using Customer.io can send marketing emails at scale; should be classified for CAN-SPAM-adjacent and PII concerns.

**Hallucinated tool** — "This action doesn't exist on the real connector"

> **Tool**: `linear.delete_issue`
> **Issue**: Linear's MCP server doesn't expose a delete tool. The action should be removed from `data/linear.yml`.
> **Source**: <link to Linear's MCP docs>

**Confidence too high / too low**

> **Tool**: `stripe.execute_analytics`
> **Current**: `confidence: high`
> **Suggestion**: downgrade to `medium` — the tool's behavior depends on what the analytics query touches, which the metadata can't capture.

**General feedback / discussion**

> Just open an issue. Ideas about new compliance regimes to support, schema improvements, audit-report shape, etc. all welcome.

### Path 2 — Open a PR (for direct changes)

Fork the repo, branch off `main`, edit or add a file under [`data/`](./data), and open a PR. Use [`data/salesforce.yml`](./data/salesforce.yml) as the canonical schema reference.

There are three hard rules for new YAML data. PRs that violate them will be sent back for revision.

#### Rule 1 — Tool ids verbatim from the MCP server

The `id` and `action` fields MUST be the literal tool name the MCP server exposes — case, vendor prefixes, and plurals preserved.

The right source is the connector's **published MCP `tools/list` documentation** (or the source code of the MCP server, if open-source). The right source is **NOT** the vendor's REST API documentation — MCP servers often use a different naming convention and a different granularity than REST.

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

If you can't find an authoritative tool list within a few minutes of searching, **open an issue instead of a PR** so we can decide together whether to skip the platform or wait for upstream docs.

#### Rule 2 — `compliance:` uses only the 25 canonical codes

The closed allowlist:

```
APPI, CCPA, COPPA, COSO, CO_AI_ACT, EU_AI_ACT, FDA_PART_11, FEDRAMP,
FERPA, GDPR, GLBA, HIPAA, ISO_27001, LGPD, NIST_AI_RMF, NIST_CSF,
NY_DFS_500, PCI, PIPEDA, PIPL, POPIA, PSD2, SOC2, SOX, UK_GDPR
```

If a real concern doesn't fit one of these (e.g. TCPA, CAN-SPAM, BIPA, AML, KYC, BSA, state data-broker laws), **describe it in the `business_impact` prose** — don't invent a new code. The closed list keeps audit summaries comparable across platforms.

If you think a regime genuinely should be added to the canonical list, open an issue first. Adding a code is a project-level decision, not a per-PR change.

##### Quick decision rules

- **Privacy regimes** (GDPR, UK_GDPR, CCPA, PIPEDA, LGPD, APPI, PIPL, POPIA): tag the full set whenever an action touches identifiable personal data. SaaS platforms typically hold data globally, so the default is "tag all eight" for any PII read/write/export.
- **Industry regimes** (HIPAA, PCI, GLBA, FERPA, COPPA): only when the data type matches. HIPAA on healthcare-context platforms; PCI on payment-card data; GLBA on financial-services personal data; FERPA on student records; COPPA on children's data.
- **Financial reporting** (SOX, COSO): on actions that affect financial reporting, revenue recognition, IT general controls on financial systems, or audit-log integrity for financial systems. Tag SOX and COSO together — COSO is the framework SOX is implemented against.
- **Security frameworks** (SOC2, ISO_27001): on actions affecting security/availability/processing-integrity/confidentiality controls. Pair SOC2 with ISO_27001 for most security-relevant writes — the controls overlap heavily. Add NIST_CSF for high-impact security controls (privilege escalation, secret management, audit-log tampering).
- **AI regulation** (EU_AI_ACT, NIST_AI_RMF, CO_AI_ACT): only when the action itself is part of automated decisioning that affects an individual's rights or interests (profiling, automated hiring/credit/insurance/healthcare decisions, biometric ID). Most CRM/repo/messaging actions don't qualify.
- **Sector-specific** (FEDRAMP, NY_DFS_500, PSD2, FDA_PART_11): only when the platform is inherently in scope. FedRAMP-deployed gov cloud, NY-licensed financial institutions, EU payment-service providers, FDA-regulated electronic records.

When in doubt, omit. Wrong tags are worse than missing tags.

#### Rule 3 — Calibrated `confidence`

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
- [ ] `compliance:` arrays use only the 25 canonical codes.
- [ ] `confidence` is calibrated honestly; `low` entries are flagged in the PR description.
- [ ] `risk` matches the gradient rules.
- [ ] `business_impact` is one declarative sentence per action.
- [ ] You included a link to the authoritative tool-list source in the PR description.

## What happens after you submit

- **Issues**: triaged by LangGuard within a few business days. Data corrections we agree with usually land within a week.
- **PRs**: reviewed by LangGuard. We may suggest revisions to align with the rules above. Approved merges are deployed to production audits within 60 minutes (server-side cache TTL).
- All contributors are credited in the file's `source` field if the change is substantial. The default `source: langguard-editorial` is reserved for editorial maintenance; community-contributed entries should set `source: community-<your-handle>` or similar.

## Code of conduct

Be respectful and direct. Disagreements about classifications are welcome — bring evidence (vendor docs, customer experience, regulator guidance) and we'll work through it.

## Contact

- **Issues / data discussion**: open a GitHub issue.
- **Sensitive disclosures, commercial inquiries**: [scope-mcp@langguard.ai](mailto:scope-mcp@langguard.ai).
