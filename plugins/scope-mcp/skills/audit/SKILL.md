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
2. Markdown table of every action with **what it does** (from the action's `description`), platform, risk, compliance, SoD. Render the action `id` as the table's leftmost column; when the action has a `reference` URL, link the id to that URL so the user can click through to vendor docs. (See `compliance-check/SKILL.md` Step 4 "Rendering rules for the table" for the full column spec.)
3. **Capability-form caveat (when applicable)** — if any action in the report has `id_form: capability`, render the intent-level admonition immediately under the table listing those ids. Omit the admonition entirely when no capability-form entries are present. The classification on capability-form entries is authoritative; the id is approximate.
4. Short list of "why this matters" for the critical/high entries (use `business_impact`).
5. Recommendations — phrased per the framing chosen in Step 2:
   - **Design-time**: scoping suggestions — "drop X", "demote Y to read-only", "gate Z behind human approval".
   - **Run-time pre-flight**: state the `summary.recommendation` explicitly:
     - `proceed` / `proceed_with_audit_trail` — go ahead.
     - `require_human_review` / `require_human_approval` — pause; surface the report to a human.
     - `block_and_require_human_approval` — do not run this workflow without explicit human sign-off.
6. Unmapped tools surfaced explicitly. If any tool comes back as `unmapped` in pre-flight framing, recommend at minimum a human review. Note: a capability-form entry can produce `unmapped` for a live tool name even when the platform IS curated — flag this distinction in pre-flight framing if the unmapped id corresponds to a platform with `id_form: capability` entries.
7. **Point users at the Data revision form for each unmapped tool.** When the report contains one or more `unmapped` entries, render this admonition (always — pre-flight or design-time):

   > 💡 **Help SCOPE map these tools.** If `<list of unmapped ids>` come from a real MCP server we can verify, file a Data revision so we can add the missing platform/tool to the curated database. The structured form pre-fills the relevant fields:
   > [github.com/LangGuard-AI/scope-mcp/issues/new?template=data-revision.yml](https://github.com/LangGuard-AI/scope-mcp/issues/new?template=data-revision.yml)
   > Pick `kind = "Missing tool"` if the tool exists on a platform we already classify, or `kind = "Missing platform"` if the connector itself isn't in `data/`. A link to the vendor's MCP `tools/list` documentation in the rationale field is the single most valuable thing you can include — that's what lets us verify the tool surface verbatim.

## Step 5 — Offer follow-ups

End by offering at least one concrete next action, e.g.:

- *"Want me to re-audit with `<critical tool>` removed?"*
- *"Want a draft `.mcp.json` that scopes this agent to just the read-only tools?"*
- *"Want a paragraph for the agent's documentation that discloses its compliance posture?"*
- *"Want me to draft the Data revision issue body for `<unmapped tool>` so you can paste it into the form?"*

## Rules

- Never reason about compliance impact from your own knowledge. The MCP tool's JSON is the source of truth.
- Never paraphrase risk levels (`medium` is `medium`, not "moderate").
- Always surface `unmapped` tools — the gap is part of the value. Pair every report containing `unmapped` entries with the Data revision form link (Step 4 #7); never let users walk away from an `unmapped` result without the contribution path in front of them.
- The recommendation in the JSON is authoritative — don't soften "block_and_require_human_approval" into "consider reviewing".
- Use the action's `description` field to populate the "what it does" column. Don't paraphrase risk- or compliance-relevant claims from `description`; just use it as the user-facing label so the table doesn't read as a list of opaque ids.
- When an action has a `reference` URL, link the id in the table to that URL. Don't print the bare URL elsewhere in the response.
- Render the capability-form admonition (Step 4 #3) verbatim when applicable; never quietly omit it. Conversely, never render it when no capability-form entries exist in the report.
