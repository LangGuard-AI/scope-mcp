"""
validate_yaml.py — Curate skill YAML validator.

Usage:
    python3 plugins/scope-mcp/skills/curate/scripts/validate_yaml.py data/<platform>.yml

Exit codes:
    0  — validation passed
    1  — validation failure (messages printed to stderr)
    2  — parse error or path security violation (message printed to stderr)
"""

import re
import sys
import os
import yaml
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9-]{0,40}$')

# Script lives at: <repo>/plugins/scope-mcp/skills/curate/scripts/validate_yaml.py
# parents[0] = scripts/
# parents[1] = curate/
# parents[2] = skills/
# parents[3] = scope-mcp/
# parents[4] = plugins/
# parents[5] = <repo root>
REPO_ROOT = Path(__file__).resolve().parents[5]
DATA_DIR = REPO_ROOT / 'data'


def _load_regimes() -> set[str]:
    """Load regime codes from _meta/regimes.yml if available, else hardcoded fallback."""
    regimes_file = REPO_ROOT / '_meta' / 'regimes.yml'
    if regimes_file.exists():
        try:
            with open(regimes_file, encoding='utf-8') as fh:
                data = yaml.safe_load(fh)
                if data and isinstance(data.get('regimes'), list):
                    return {regime['code'] for regime in data['regimes'] if 'code' in regime}
        except Exception:
            pass  # Fall through to hardcoded set

    # Hardcoded fallback (canonical list from May 2026)
    return {
        'APPI', 'CCPA', 'COPPA', 'COSO', 'CO_AI_ACT', 'EU_AI_ACT', 'FDA_PART_11',
        'FEDRAMP', 'FERPA', 'GDPR', 'GLBA', 'HIPAA', 'ISO_27001', 'ISO_42001', 'LGPD',
        'NIST_AI_RMF', 'NIST_CSF', 'NY_DFS_500', 'PCI', 'PIPEDA', 'PIPL', 'POPIA',
        'PSD2', 'SOC2', 'SOX', 'UK_GDPR',
    }


ALLOWED_REGIMES = _load_regimes()


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def main() -> int:
    if len(sys.argv) != 2:
        _err(f"Usage: {sys.argv[0]} <path-to-yaml-file>")
        return 2

    raw_path = sys.argv[1]

    # ------------------------------------------------------------------
    # 1. Path-traversal / containment check
    # ------------------------------------------------------------------
    try:
        resolved = Path(raw_path).resolve()
    except Exception as exc:
        _err(f"ERROR: Cannot resolve path '{raw_path}': {exc}")
        return 2

    if not resolved.is_relative_to(DATA_DIR):
        _err(
            f"ERROR: Resolved path '{resolved}' is outside the allowed "
            f"data directory '{DATA_DIR}'. Refusing to process."
        )
        return 2

    # ------------------------------------------------------------------
    # 2. Load YAML
    # ------------------------------------------------------------------
    try:
        with open(resolved, encoding='utf-8') as fh:
            data = yaml.safe_load(fh)
    except FileNotFoundError:
        _err(f"ERROR: File not found: '{resolved}'")
        return 2
    except yaml.YAMLError as exc:
        _err(f"ERROR: YAML parse failure in '{resolved}': {exc}")
        return 2

    data = data or {}

    # ------------------------------------------------------------------
    # 3. Slug validation
    # ------------------------------------------------------------------
    slug = data.get('platform', '')
    if not slug:
        _err("ERROR: 'platform:' field is missing or empty.")
        return 1

    if not SLUG_RE.match(slug):
        _err(
            f"ERROR: platform slug '{slug}' does not match "
            f"'^[a-z0-9][a-z0-9-]{{0,40}}$'."
        )
        return 1

    # Basename check: file must be named <slug>.yml
    expected_basename = f"{slug}.yml"
    actual_basename = resolved.name
    if actual_basename != expected_basename:
        _err(
            f"ERROR: File is named '{actual_basename}' but platform slug is "
            f"'{slug}' — expected filename '{expected_basename}'."
        )
        return 1

    # ------------------------------------------------------------------
    # 4. Per-action validation
    # ------------------------------------------------------------------
    actions = data.get('actions') or []
    failures: list[str] = []

    for entry in actions:
        if not isinstance(entry, dict):
            continue

        action_id = entry.get('id', '<unknown>')

        # Compliance regime check
        for code in (entry.get('compliance') or []):
            if code not in ALLOWED_REGIMES:
                failures.append(
                    f"  {action_id}: invalid compliance code '{code}'"
                )

        # access_methods must be exactly ["MCP"]
        methods = entry.get('access_methods') or []
        for method in methods:
            if method != 'MCP':
                failures.append(
                    f"  {action_id}: non-MCP access_method '{method}' "
                    f"(access_methods must be exactly [MCP])"
                )
        if not methods:
            failures.append(
                f"  {action_id}: access_methods is empty (must be [MCP])"
            )

    if failures:
        _err(f"VALIDATION FAILED — {len(failures)} issue(s):")
        for msg in failures:
            _err(msg)
        return 1

    # ------------------------------------------------------------------
    # 5. Success
    # ------------------------------------------------------------------
    print(f"OK — {len(actions)} actions, all regimes valid, MCP-only")
    return 0


if __name__ == '__main__':
    sys.exit(main())
