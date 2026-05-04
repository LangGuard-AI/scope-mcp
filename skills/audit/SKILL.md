---
name: audit
description: Use this skill ONLY when the user explicitly invokes `/scope-mcp:audit` (or asks for a "compliance audit"). Runs a compliance audit against the curated action-surface database. Accepts MCP tool ids, API actions, connector wildcards (`salesforce.*`), bare platform names, or a prose description of the agent. Returns a deterministic risk + regulatory exposure report (SOX, GDPR, PCI, HIPAA) with concrete recommendations. Handles both design-time scoping ("should I build this?") and run-time pre-flight ("about to execute these tools — any issues?") — choose the framing in Step 3 based on what the user is actually doing.
---

# Compliance audit (explicit)

This skill is the **explicit** entry point for the compliance audit. It runs when the user invokes `/scope-mcp:audit <args>` or directly asks for a compliance audit. For the auto-trigger case (user describing an agent in passing during a design conversation), the `compliance-check` skill in this plugin handles that path.

The skill works for both:

- **Design-time scoping** — the user is choosing which connectors / tools to attach to an agent under construction.
- **Run-time pre-flight** — the user is about to execute a workflow with a specific, known list of tools and wants a go/no-go read.

Both modes call the same underlying audit and produce the same JSON. They differ only in how you frame the recommendations to the user (Step 3).

## Step 1 — Determine the action surface

Inspect what the user passed (slash arguments, or the natural-language prompt that invoked this skill):

| Input shape | What you do |
|---|---|
| Empty / vague | Ask the user to describe the agent or list the tools they want audited, and stop. |
| Concrete tool ids / wildcards (`salesforce.* slack.post_message github.merge_pull_request`) | Pass straight to the audit tool. |
| Prose (`"an agent that updates SF opportunities when a deal closes"`) | Derive likely action ids in canonical `<platform>.<action>` form. State your derivation explicitly so the user can correct you. Use wildcards (`salesforce.*`) for whole-connector references. |

Do not expand wildcards on your own judgment — the audit tool handles `salesforce.*` and bare platform names directly.

## Step 2 — Decide the framing (design vs. pre-flight)

This determines how you present the report in Step 3. Use the language and signals in the user's prompt:

| Signals → **Design-time** framing | Signals → **Run-time pre-flight** framing |
|---|---|
| "I'm building", "I'm thinking of adding", "should this agent have", "what if I gave it" | "I'm about to run", "before I execute", "pre-flight", "is it safe to run" |
| Whole-connector questions (`salesforce.*`) | A specific, fixed list of tool ids |
| Open scoping questions | An imminent execution |

If unclear, default to **design-time**. You can always re-frame if the user corrects you.

## Step 3 — Run the audit via the MCP tool

You **MUST** invoke the `audit_agent_design` MCP tool (provided by this plugin's bundled MCP server, `scope-mcp`). Do **not** run any local script or shell out to Python — the MCP tool is the only sanctioned path.

```jsonc
{
  "name": "audit_agent_design",
  "arguments": {
    "tools": ["<derived ids and globs>"],
    "scenario": "<short label — e.g. 'Pre-flight: nightly sync' or 'Design: lead-routing agent v1'>"
  }
}
```

If the tool is not visible, ask the host to ensure the `scope-mcp` MCP server is connected — do not fall back to a local script.

## Step 4 — Present the report

Render the report using the **build-advisory format** described in `skills/compliance-check/SKILL.md` (Step 4: "Present an advisory, not a gate"). Required sections:

1. One-line posture summary (highest risk, regimes, SoD count).
2. Markdown table of every action with risk, compliance, SoD.
3. Short list of "why this matters" for the critical/high entries (use `business_impact`).
4. Recommendations — phrased per the framing chosen in Step 2:
   - **Design-time**: scoping suggestions — "drop X", "demote Y to read-only", "gate Z behind human approval".
   - **Run-time pre-flight**: state the `summary.recommendation` explicitly:
     - `proceed` / `proceed_with_audit_trail` — go ahead.
     - `require_human_review` / `require_human_approval` — pause; surface the report to a human.
     - `block_and_require_human_approval` — do not run this workflow without explicit human sign-off.
5. Unmapped tools surfaced explicitly. If any tool comes back as `unmapped` in pre-flight framing, recommend at minimum a human review.

## Step 5 — Offer follow-ups

End by offering at least one concrete next action, e.g.:

- *"Want me to re-audit with `<critical tool>` removed?"*
- *"Want a draft `.mcp.json` that scopes this agent to just the read-only tools?"*
- *"Want a paragraph for the agent's documentation that discloses its compliance posture?"*

## Rules

- Never reason about compliance impact from your own knowledge. The MCP tool's JSON is the source of truth.
- Never paraphrase risk levels (`medium` is `medium`, not "moderate").
- Always surface `unmapped` tools — the gap is part of the value.
- The recommendation in the JSON is authoritative — don't soften "block_and_require_human_approval" into "consider reviewing".
