---
name: compliance-check
description: Use proactively when the user is DESIGNING or BUILDING an agent / Cowork plugin / agentic workflow — i.e. choosing which connectors, MCP servers, skills, or APIs the agent can call. Trigger when the user describes an agent in prose, lists connectors they're considering, asks "what should I include", composes a system prompt that references external systems, or edits a plugin/agent definition. Calls the `audit_agent_design` MCP tool (from this plugin's bundled `scope-mcp` MCP server) to produce a deterministic compliance advisory mapping each proposed action to risk level, business impact, and regulatory exposure (SOX, GDPR, PCI, HIPAA), and recommends scoping changes (drop, demote to read-only, gate behind human approval) BEFORE the agent is shipped. Design-time guidance, not run-time enforcement. Invoke the moment agent design is on the table — never wait for the user to ask "is this compliant?"
---

# Compliance check — design-time advisory for agent builders

This skill exists to answer one question while a user is **building** an agent or Cowork plugin: **"Given the connectors and tools you're attaching to this agent, what is the compliance and risk posture, and how should you scope it before you ship?"**

The answer is produced by the `audit_agent_design` MCP tool (provided by this plugin's bundled `scope-mcp` MCP server), which looks up each proposed action against a curated action-surface database hosted server-side. **You do not reason about compliance impact yourself** — you enumerate the proposed tools, call the MCP tool, and present its JSON output as advisory guidance. The MCP tool is the source of truth.

## When to fire this skill

Trigger whenever any of these are true:

- The user describes an agent in prose: *"I'm building an agent that does X with Salesforce and Slack."*
- The user asks about adding connectors / MCP servers / skills to an agent: *"Should I add the GitHub connector?"*, *"What if this agent had write access to Salesforce?"*
- The user is composing a system prompt that grants tool access.
- The user pastes or edits a plugin manifest, `.mcp.json`, agent definition file, or connector list.
- The user is iterating on agent scope: *"Can I narrow this down?"*, *"Is this overpowered?"*

Do **not** wait to be asked. The whole point of this skill is to surface compliance posture *before* it becomes a problem.

Do **not** fire this skill for **execution** of an already-shipped agent — only for **design / build / scoping** conversations. (For an explicit run-time pre-flight on a specific tool list, the user can invoke `/scope-mcp:audit` with that list — the `audit` skill handles both design-time and pre-flight framings.)

## How to run the audit

### Step 1 — Enumerate the action surface

Translate the user's design into a list of action ids in canonical `<platform>.<action>` form. Three input shapes show up:

| User says... | You do... |
|---|---|
| *"Give it the Salesforce connector"* | Use a wildcard: `salesforce.*` |
| *"It needs to update opportunities and create cases"* | Specific ids: `salesforce.update_opportunity_stage`, `salesforce.create_case` |
| *"It posts to Slack and merges PRs"* | Specific ids across platforms: `slack.post_message`, `github.merge_pull_request` |

If a user says "the X connector" without naming actions, **pass `x.*`** — the MCP tool knows how to enumerate the full surface. Surfacing the *full* attack surface of attaching a whole connector is part of the value.

If you derive action ids from prose, briefly state your derivation so the user can correct you ("I'm reading this as `salesforce.update_opportunity_stage` and `slack.post_message` — correct me if you meant something else").

### Step 2 — Call the `audit_agent_design` MCP tool

You **MUST** invoke the `audit_agent_design` MCP tool provided by this plugin's bundled MCP server (`scope-mcp`). Do **not** run any local script, do **not** shell out to `python3`, do **not** read the YAML data files yourself. The MCP tool is the only sanctioned path — it returns a deterministic JSON report you then render to the user as a markdown advisory (Step 3).

```jsonc
{
  "name": "audit_agent_design",
  "arguments": {
    "tools": ["salesforce.*", "slack.post_message"],
    "scenario": "Sales deal-update agent v1"
  }
}
```

The tool accepts wildcards (`salesforce.*`), bare platform names (`salesforce` → expanded to `salesforce.*`), and exact ids — mix freely.

If the tool is not visible in your tool list, **ask the host to ensure the `scope-mcp` MCP server is connected**. There is no local fallback — the audit logic and data live in the MCP server (hosted), not in the plugin.

### Step 3 — Read the report

When `audit_agent_design` runs, the MCP-Apps-aware host opens an interactive dashboard rendered in the conversation; the same JSON is also in `result.content[0].text` for your own consumption.

Relevant fields in the JSON:

- `summary.recommendation` — `proceed` / `proceed_with_audit_trail` / `require_human_review` / `require_human_approval` / `block_and_require_human_approval`. **In design-time framing, treat this as scoping guidance**, not an execution gate.
- `summary.highest_risk` — `low` / `medium` / `high` / `critical` / `unmapped`.
- `summary.compliance_regimes_triggered` — subset of the 25-code allowlist (privacy: `GDPR, UK_GDPR, CCPA, PIPEDA, LGPD, APPI, PIPL, POPIA`; industry: `HIPAA, PCI, GLBA, FERPA, COPPA`; financial: `SOX, COSO`; security: `SOC2, ISO_27001, NIST_CSF`; AI: `EU_AI_ACT, NIST_AI_RMF, CO_AI_ACT`; sector: `FEDRAMP, NY_DFS_500, PSD2, FDA_PART_11`).
- `summary.sod_concerns` — count of segregation-of-duties red flags.
- `actions[]` — per-tool detail (risk, business_impact, compliance, sod_concern, category).
- `unmapped[]` — tools with no compliance entry on file.

### Step 4 — Present an advisory, not a gate

Render the result as a **build advisory** with this structure (markdown, in chat):

```markdown
## Compliance posture for this agent

This agent's proposed action surface includes **<N>** distinct actions across **<P>** platforms. Highest observed risk: **<highest_risk>**. Regulatory regimes touched: **<regimes>**. Segregation-of-duties red flags: **<n>**.

### Risk breakdown
| Tool | Platform | Risk | Compliance | SoD |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

### Why this matters
- `<critical/high tool>` — <business_impact, one line>
- `<critical/high tool>` — <business_impact, one line>

### Recommendations for scoping this agent
- **Drop unless required:** `<tool>` — <one-line rationale>
- **Gate behind human approval:** `<tool>` — <one-line rationale>
- **Demote to read-only equivalent if possible:** `<tool>` — ...
- **Add audit-trail logging on:** `<tool>`
- **Document regulatory exposure:** SOX impact requires audit-trail; GDPR exposure may require DPA review; etc.

### Unmapped tools (no compliance data on file)
- `<tool>` ← treat as unknown risk; flag for human review before shipping.
```

Ground every recommendation in the MCP tool's output. Do not invent risk judgments.

### Step 5 — Offer follow-ups

After presenting the report, proactively offer one or more of:

- *"Want me to re-audit if you drop `<critical tool>`?"* (re-run with a narrower list)
- *"Want me to write a scoped `.mcp.json` that only includes the read-only tools?"*
- *"Want a draft of the `description` field for this agent that documents its compliance posture?"*

## Hard rules

- **Never reason about compliance impact yourself.** All risk/regime claims must come from the MCP tool's JSON output.
- **Never paraphrase risk levels.** If the data says `medium`, say `medium`, not "moderate" or "manageable."
- **Always surface unmapped tools.** The gap *is* part of the answer.
- **Distinguish design-time from run-time.** This skill is for "should I attach this?" not "may I run this?"
- **Don't run the audit silently.** Always show the user the table and the recommendations.

## Data provenance

The compliance data is curated by LangGuard and lives inside the hosted `scope-mcp` MCP server (`source: langguard-editorial` on every action). When the user asks "what platforms / tools do you know about?" or wants to browse the catalog, call `audit_agent_design` with a wildcard like `["salesforce.*"]` (or all platforms) and present the resulting `actions[]` list.
