<p align="center">
  <img src="./logo.png" alt="SCOPE MCP" width="320">
</p>

<p align="center"><b>SCOPE</b> - <b>S</b>ecurity, <b>C</b>ompliance &amp; <b>O</b>perational <b>P</b>olicy <b>E</b>valuation.</p>

## Why this exists

Agentic workflows have changed what "automation" means inside an organization. A single Claude agent today can be granted a dozen MCP tools across Salesforce, Stripe, GitHub, Slack, Gmail, a payroll system, an observability stack, a vector store - and every one of those tools is an action the agent can take on your behalf. The granularity that made integrations feel safe a decade ago (one narrowly-scoped credential per script, one trigger, one path through your data) is gone. Agents hold real authority over real systems, and they hold it across the same boundary lines that compliance frameworks were drawn around.

Compliance review has not caught up. SOC 2, GDPR, HIPAA, PCI, SOX, the EU AI Act - these regimes were designed around human actors and traditional applications. Their controls land at the project level, in annual audits, in change-management reviews, in vendor questionnaires. There is no equivalent of a linter or static-analysis pass for the question that actually matters when you're building an agent: **"what compliance and risk exposure am I taking on by attaching these specific tools?"** The result is that exposure gets noticed late, in production, after the agent has been running for a while - typically when somebody finally maps the attack surface for an audit and discovers the agent has `slack.read_direct_messages` (PHI, attorney-client privilege, internal HR data) or `stripe.create_refund` (SOX-relevant, segregation-of-duties violation, PCI scope) on its toolbelt.

Runtime guardrails help, but most agent harnesses don't enforce policy at runtime - and even when they do, runtime is too late. The shipping decision was already made; the agent is already deployed; the data has already moved.

SCOPE runs at the design moment. As you describe an agent - *"an agent that watches Stripe for failed payments, looks up the customer in Salesforce, and posts to Slack"* - it produces a compliance posture report immediately. Risk levels per action, regulatory regimes triggered, segregation-of-duties red flags, concrete scoping recommendations. You see the exposure **before** the agent ships, while you still have cheap options: drop a tool, swap a write for a read, gate a critical action behind human approval, or document the regulatory exposure for a real compliance review.

Two design choices make the report trustworthy enough to use in actual change-management workflows:

- **Deterministic, not generated.** The risk levels and regime tags come from a curated database. The same input produces the same output, every time. That's auditable in a way LLM output isn't - there's no debate about hallucinations, no flickering classifications between runs.
- **Open data.** The 80+ YAMLs in [`data/`](./data) are in this public repo. You can read every classification this plugin will ever emit. If you think `slack.read_direct_messages` is over-tagged with HIPAA for your context, or that a Stripe action's confidence should be `medium` rather than `high`, the data is right there to challenge - open an [issue or PR](./CONTRIBUTING.md).

## What you get

A Claude plugin that runs a **pre-flight evaluation** on agentic workflows you're building. Tell SCOPE which MCP tools, connectors, or API actions your agent will be permitted to invoke and it produces a deterministic report:

- A **risk level** for every action (`low` / `medium` / `high` / `critical`)
- The **business impact** in one sentence
- Which **regulatory regimes** the action touches (25 codes - GDPR, HIPAA, PCI, SOX, SOC 2, EU AI Act, NY DFS 500, and more)
- Whether the action raises a **segregation-of-duties** concern
- A **recommendation**: `proceed`, `proceed_with_audit_trail`, `require_human_review`, `require_human_approval`, or `block_and_require_human_approval`

## Quickstart

### 1. Get a SCOPE access token

Self-service signup is at **[scope-mcp.langguard.ai/register-account](https://scope-mcp.langguard.ai/register-account)**. Enter your name, email, and (optional) opt-in for product updates, and we'll email your `cp_…` API token within seconds.

Three things to know before you submit:

- **One token per email.** If you lose it, email [support@langguard.ai](mailto:support@langguard.ai) — we don't have a way to recover it (we hash tokens at storage time), but we can invalidate the old one and issue a replacement.
- **Save the token immediately.** It's shown only once, in the email; we cannot fetch it later.
- **Token tier**: self-signup tokens default to a free rate limit (10 requests / minute). For higher volumes, contact [support@langguard.ai](mailto:support@langguard.ai).

### 2. Install the plugin

#### Claude Cowork

1. **Add the plugin** in Claude Cowork: Settings → Plugins → *Add plugin* → paste `https://github.com/LangGuard-AI/scope-mcp` as the repo URL.
2. When prompted, **authorize via OAuth**. You'll be redirected to a consent page where you paste the `cp_…` token from your signup email. Claude Cowork stores the authorization; you don't see the token again.
3. Start designing an agent — SCOPE's auto-trigger skill fires the moment you describe one.

#### Claude Code CLI

```bash
# Add this repo as a plugin marketplace
/plugin marketplace add LangGuard-AI/scope-mcp

# Install the plugin
/plugin install scope-mcp@scope-mcp-local
```

On first invocation, Claude Code runs the OAuth flow against the hosted SCOPE server (callback on `localhost:3118`). Paste your `cp_…` token in the consent page that opens; the resulting access token is cached locally.

#### Codex

```bash
# Register the marketplace
codex plugin marketplace add LangGuard-AI/scope-mcp

# Install the plugin
codex plugin install scope-mcp
```

Codex's MCP subsystem only speaks stdio, so the plugin's MCP config bridges to the hosted HTTPS server via [`mcp-remote`](https://github.com/geelen/mcp-remote) — invoked transparently as `npx -y mcp-remote@latest https://scope-mcp.langguard.ai/mcp` on first start. `mcp-remote` runs the OAuth flow in a browser tab, caches the resulting access token under `~/.mcp-auth/`, and proxies stdio↔HTTP for the Codex session. After the first authorization the plugin starts silently in subsequent Codex sessions.

> Requires Node 18+ on `PATH` (for `npx`). The bridge package is downloaded on first run and cached by npm.

### 3. Verify the install

In any session, type:

```
/scope-mcp:audit salesforce.* slack.post_message
```

You should see a markdown table with risk levels and compliance tags for each Salesforce action plus the Slack post.

## Usage

### Auto-trigger (recommended)

Just describe the agent you're building:

> *"I'm building an agent that watches our Stripe webhooks for failed payments, looks up the customer in Salesforce, and posts to Slack."*

SCOPE's `compliance-check` skill triggers automatically, derives the implied tool surface (`stripe.*`, `salesforce.*`, `slack.post_message`), and produces a build advisory.

### Explicit - `/scope-mcp:audit`

Pass anything: tool ids, connector wildcards, bare platform names, or a prose description.

```
/scope-mcp:audit github.merge_pull_request slack.read_direct_messages
/scope-mcp:audit hubspot.*
/scope-mcp:audit "an agent that updates SF opportunities when a deal closes"
```

The output adapts: design-time scoping advice when you're iterating on what to attach, run-time pre-flight gating when you're about to execute a fixed set of tools.

## Example output

```
## Compliance posture for this agent

3 actions across 2 platforms. Highest observed risk: **critical**.
Regulatory regimes touched: GDPR, UK_GDPR, CCPA, HIPAA, SOC2, ISO_27001.
Segregation-of-duties red flags: 1.

| Tool                          | Risk     | Compliance                          | SoD |
|-------------------------------|----------|-------------------------------------|-----|
| slack.read_direct_messages    | critical | GDPR, UK_GDPR, CCPA, HIPAA, SOC2…  | ⚠   |
| slack.post_message            | low      | -                                   |     |
| github.merge_pull_request     | high     | SOX, COSO, SOC2, ISO_27001          |     |

### Why this matters
- slack.read_direct_messages - Reads private 1:1 and small-group conversations;
  may include regulated health or personnel data.
- github.merge_pull_request - Bypasses code-review gating that audit logs depend on.

### Recommendations
- Drop unless required: slack.read_direct_messages
- Gate behind human approval: github.merge_pull_request
```

## Architecture

```mermaid
flowchart TD
    A["<b>Your Claude session</b><br/>Claude Code CLI or Claude Cowork"]
      -->|"tool call:<br/>audit_agent_design"| B
    B["<b>scope-mcp plugin</b> (this repo)<br/>skills + slash commands<br/>.mcp.json → hosted server"]
      -->|"MCP over HTTPS<br/>(OAuth 2.1 + PKCE)"| C
    C["<b>Hosted SCOPE MCP server</b><br/>operated by LangGuard<br/>audit_agent_design<br/>deterministic risk lookup"]
      -->|reads| D
    D[("<b>YAML compliance data</b><br/>THIS REPO → data/*.yml<br/>80 platforms, fully auditable")]
```

The plugin in this repo distributes the *interface*: skills (`audit`, `compliance-check`), the `/scope-mcp:audit` slash command, and an `.mcp.json` manifest pointing at the hosted SCOPE MCP server. It also distributes the *data*: the 80+ per-platform YAML files in [`data/`](./data) that catalogue every MCP tool the server knows about and how each one is classified.

When you run an audit, your Claude session calls the hosted MCP server over HTTPS. The server reads its data from the YAML files in this repository - that's the canonical source of truth, publicly auditable, and updated by pull request. You can read every classification this plugin will ever emit by browsing [`data/`](./data).

## Data and schema

```
data/
├── salesforce.yml          # canonical schema reference
├── github.yml
├── slack.yml
├── stripe.yml
├── notion.yml
├── hubspot.yml
└── ... 75+ more
```

Each file declares the platform's actions in this shape:

```yaml
schema_version: "1.0"
platform: stripe
display_name: Stripe
source: langguard-editorial
updated: "2026-05"
actions:
  - id: stripe.create_refund
    object: Refund
    action: create_refund
    category: Financial
    risk: critical
    business_impact: "Moves money back to the cardholder; touches payment rails and the GL."
    compliance: [SOX, COSO, PCI, SOC2, ISO_27001, PSD2]
    sod_concern: true
    confidence: high
    access_methods: [REST, MCP]
```

Tool ids are **verbatim** from each connector's published MCP `tools/list` documentation - case, vendor prefixes, and plurals preserved. So `notion.notion-create-pages` (kebab-case + vendor prefix) and `atlassian.createJiraIssue` (camelCase) appear exactly as the upstream MCP server emits them. This is what makes lookup deterministic at audit time.

## Compliance regimes covered

A closed list of 25 canonical codes. The audit returns the subset triggered by your tool selection.

| Category | Codes |
|---|---|
| **Privacy** | `GDPR`, `UK_GDPR`, `CCPA`, `PIPEDA`, `LGPD`, `APPI`, `PIPL`, `POPIA` |
| **Industry / sector data** | `HIPAA`, `PCI`, `GLBA`, `FERPA`, `COPPA` |
| **Financial reporting** | `SOX`, `COSO` |
| **Security frameworks** | `SOC2`, `ISO_27001`, `NIST_CSF` |
| **AI regulation** | `EU_AI_ACT`, `NIST_AI_RMF`, `CO_AI_ACT` |
| **Sector-specific** | `FEDRAMP`, `NY_DFS_500`, `PSD2`, `FDA_PART_11` |

## Repository layout

```
scope-mcp/
├── .claude-plugin/
│   ├── plugin.json              # plugin manifest
│   └── marketplace.json         # marketplace catalog
├── .mcp.json                    # points at the hosted MCP server URL
├── skills/
│   ├── compliance-check/SKILL.md   # auto-trigger (proactive design-time)
│   └── audit/SKILL.md              # /scope-mcp:audit (explicit)
├── data/                        # per-platform YAML compliance data (~80 files)
├── CHANGELOG.md
└── README.md
```

## Contributing

**The data is the project.** SCOPE is only as good as the YAMLs in [`data/`](./data), and we want community input on every part of them - risk levels, business-impact wording, regime tagging, missing tools, hallucinated tools, calibration of `confidence`. If you've used a connector in a regulated context and our classification feels off, we want to hear about it.

Two ways to contribute, both welcome:

- **Open an issue** if you have feedback but don't want to write YAML. A one-paragraph "I think `stripe.create_refund` should also tag `NY_DFS_500` because…" is plenty - we'll do the rest.
- **Open a PR** if you want to make the change directly. Edit or add files under [`data/`](./data) following the schema in `data/salesforce.yml`. Approved PRs reach production within 60 minutes of merge.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for issue templates, the three hard rules for new data (verbatim tool ids, closed regime allowlist, calibrated confidence), and a PR checklist.

## Limitations

- **Coverage**: ~80 platforms today, expanding. If you audit a tool SCOPE doesn't recognize, it surfaces as `unmapped` and the audit recommends human review by default.
- **Not a runtime gate**: SCOPE produces an advisory report. It does not enforce execution policy at runtime - that's a separate problem your agent harness solves.
- **Editorial judgment**: Risk and regime classifications reflect informed industry consensus, not legal advice. Sector-specific applicability (e.g. whether HIPAA applies to a given Slack workspace) depends on your deployment and is flagged in `business_impact` prose.

## Privacy

**The hosted SCOPE MCP server does not log requests.** Specifically:

- **No request body is ever persisted.** When your agent calls `audit_agent_design` with a tool list, the server reads it, computes the report from the curated YAML data, returns the response, and discards the input. The submitted tool list never lands in any log line, database row, or object store.
- **No IP address is ever stored alongside submitted content.** The only place a client IP touches the system is a per-IP rate-limit counter for `/register-account` and `/browse`, and that's keyed on `sha256(ip)` with the row containing only a count + TTL. The IP-hash partition has no correlation key to any row that holds submitted data — they cannot be joined.
- **Application logs (CloudWatch) capture HTTP method + path + the MCP method name** (e.g. `POST /mcp tools/call name=audit_agent_design`) — never the arguments, never the IP. Errors are scrubbed to `{name, message}` before logging so AWS SDK and transport errors cannot smuggle the original request body into the log group.
- **API Gateway access logs are not enabled.** AWS HTTP APIs don't auto-log without explicit `AccessLogSettings`; the SAM template intentionally omits the block, with an inline comment documenting that adding one in the future MUST scrub `$context.identity.sourceIp` to preserve this invariant.
- **No third-party telemetry, analytics, or APM agent runs in the Lambda.** No Datadog, Sentry, X-Ray, OpenTelemetry, or similar exporters are configured.
- **Registration data minimization**: `/register-account` stores name + email + a SHA-256 hash of the issued token. The token itself is never stored. Nothing is correlated with the IP that submitted the form.

If you have a use case that requires deeper privacy assurances (audit logs against the deployed infrastructure, verification of the exact code that handles your traffic, contractual data-handling commitments), email [scope-mcp@langguard.ai](mailto:scope-mcp@langguard.ai).

## Contact

- **Get an access token**: self-service at [scope-mcp.langguard.ai/register-account](https://scope-mcp.langguard.ai/register-account).
- **Lost your token, rate-limit increase, commercial inquiries**: [support@langguard.ai](mailto:support@langguard.ai).
- **Issues / data corrections**: open a GitHub issue on this repo.
