#!/usr/bin/env python3
"""
BlackBirdDS — Figma Sync Script
================================
Fetches design tokens from the Figma file and regenerates the token data
embedded in blackbirdds-docs.html, keeping the layout/components intact.

Usage:
    FIGMA_TOKEN=<token> python3 scripts/sync_from_figma.py

Environment variables:
    FIGMA_TOKEN   (required) Personal access token from Figma → Settings → Access tokens
    FIGMA_FILE_ID (optional) Defaults to the BlackBirdDS file
"""

import os
import sys
import json
import re
import requests
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────────

FIGMA_TOKEN   = os.environ.get("FIGMA_TOKEN", "")
FIGMA_FILE_ID = os.environ.get("FIGMA_FILE_ID", "2Ov115BSkN5jNisHpc6ZXq")
BASE_URL      = "https://api.figma.com/v1"
HEADERS       = {"X-Figma-Token": FIGMA_TOKEN}
DOCS_FILE     = Path(__file__).parent.parent / "blackbirdds-docs.html"

MARKER_START  = "<!-- FIGMA_TOKENS_START -->"
MARKER_END    = "<!-- FIGMA_TOKENS_END -->"

# ── Figma API helpers ───────────────────────────────────────────────────────────

def api_get(path: str) -> dict:
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_variables() -> dict | None:
    """
    Fetch all local variables (requires Figma Professional or Enterprise plan).
    Returns None gracefully if not available so the script can fall back.
    """
    try:
        data = api_get(f"/files/{FIGMA_FILE_ID}/variables/local")
        return data
    except requests.HTTPError as e:
        if e.response.status_code in (403, 404):
            print("  ⚠️  Variables API not available — plan may not include REST variable access.")
            print("      Falling back to styles-based data extraction.")
            return None
        raise


def fetch_file() -> dict:
    """Fetch the full Figma file (includes document tree, styles list)."""
    print("  Fetching Figma file…")
    return api_get(f"/files/{FIGMA_FILE_ID}")


def fetch_node_details(node_ids: list[str]) -> dict:
    """Fetch specific nodes from the file (used for style details)."""
    ids_param = ",".join(node_ids[:50])  # API cap: ~50 IDs per request
    data = api_get(f"/files/{FIGMA_FILE_ID}/nodes?ids={ids_param}")
    return data.get("nodes", {})


# ── Color helpers ───────────────────────────────────────────────────────────────

def rgba_to_hex(r: float, g: float, b: float, a: float = 1.0) -> str:
    ri, gi, bi = int(r * 255), int(g * 255), int(b * 255)
    if a < 1.0:
        ai = int(a * 255)
        return f"#{ri:02X}{gi:02X}{bi:02X}{ai:02X}"
    return f"#{ri:02X}{gi:02X}{bi:02X}"


def color_from_figma(c: dict) -> str:
    return rgba_to_hex(c["r"], c["g"], c["b"], c.get("a", 1.0))


# ── Token extraction ────────────────────────────────────────────────────────────

def extract_colors_from_variables(var_data: dict) -> tuple[list, list]:
    """
    Parse color variables into:
      - primitive_colors: [{name, hex, group}]
      - semantic_tokens:  [{name, light, dark, category, usage}]
    """
    variables   = var_data.get("variables", {})
    collections = var_data.get("variableCollections", {})

    # Build collection name → id map
    coll_by_id = {cid: c for cid, c in collections.items()}

    primitives = []
    semantic   = []

    for var_id, var in variables.items():
        if var.get("resolvedType") != "COLOR":
            continue

        coll_id   = var.get("variableCollectionId", "")
        coll      = coll_by_id.get(coll_id, {})
        coll_name = coll.get("name", "")
        var_name  = var.get("name", "")
        modes     = coll.get("modes", [])

        # ── Primitive colors ────────────────────────────────────────────────
        if coll_name in ("🎨 Colors", "Colors", "Primitives"):
            values = var.get("valuesByMode", {})
            if not values:
                continue
            first_mode_val = next(iter(values.values()))
            if isinstance(first_mode_val, dict) and "r" in first_mode_val:
                hex_val = color_from_figma(first_mode_val)
                # Derive group from variable name (e.g. "colors/brand/500" → "Brand")
                parts = var_name.split("/")
                if len(parts) >= 2:
                    group = parts[-2].capitalize() if parts[-2].lower() not in ("colors",) else parts[-3].capitalize() if len(parts) >= 3 else "Other"
                else:
                    group = coll_name
                primitives.append({"name": var_name, "hex": hex_val, "group": group})

        # ── Semantic tokens (two-mode: Light / Dark) ────────────────────────
        elif coll_name in ("Semantic Colors", "Semantic"):
            values     = var.get("valuesByMode", {})
            mode_names = {m["modeId"]: m["name"] for m in modes}
            light_val  = dark_val = None

            for mode_id, val in values.items():
                mode_name = mode_names.get(mode_id, "").lower()
                # Resolve aliases (variables that point to other variables)
                if isinstance(val, dict) and val.get("type") == "VARIABLE_ALIAS":
                    resolved = variables.get(val.get("id", ""), {})
                    resolved_vals = resolved.get("valuesByMode", {})
                    val = next(iter(resolved_vals.values()), val)
                if isinstance(val, dict) and "r" in val:
                    hex_val = color_from_figma(val)
                    if "light" in mode_name:
                        light_val = hex_val
                    elif "dark" in mode_name:
                        dark_val = hex_val

            if light_val or dark_val:
                # Infer category from token name (e.g. "color/bg/primary" → "Background")
                parts = var_name.lower().split("/")
                category_map = {
                    "bg": "Background", "background": "Background",
                    "surface": "Surface",
                    "text": "Text",
                    "border": "Border",
                    "accent": "Accent",
                    "success": "Success", "warning": "Warning",
                    "error": "Error",   "info": "Info",
                }
                category = "Other"
                for part in parts:
                    if part in category_map:
                        category = category_map[part]
                        break

                semantic.append({
                    "name":     var_name,
                    "light":    light_val or "#000000",
                    "dark":     dark_val  or "#FFFFFF",
                    "category": category,
                    "usage":    "",   # Usage descriptions aren't stored in variables
                })

    return primitives, semantic


def extract_spacing_from_variables(var_data: dict) -> list:
    """Extract spacing and border-radius tokens → [{name, value, px}]"""
    variables   = var_data.get("variables", {})
    collections = var_data.get("variableCollections", {})
    coll_by_id  = {cid: c for cid, c in collections.items()}
    tokens      = []

    for var_id, var in variables.items():
        if var.get("resolvedType") != "FLOAT":
            continue
        coll_name = coll_by_id.get(var.get("variableCollectionId", ""), {}).get("name", "")
        if coll_name not in ("Spacing", "Border Radius", "Letter Spacing"):
            continue
        values   = var.get("valuesByMode", {})
        px_value = next(iter(values.values()), 0)
        if isinstance(px_value, (int, float)):
            tokens.append({
                "collection": coll_name,
                "name":       var.get("name", ""),
                "px":         px_value,
            })

    return sorted(tokens, key=lambda t: (t["collection"], t["px"]))


def extract_typography_from_file(file_data: dict, nodes: dict) -> list:
    """
    Extract text styles from the Figma file.
    Returns [{name, fontSize, fontWeight, lineHeight, letterSpacing, fontFamily}]
    """
    styles = file_data.get("styles", {})
    text_styles = []

    for node_id, style_meta in styles.items():
        if style_meta.get("styleType") != "TEXT":
            continue
        node_detail = nodes.get(node_id, {}).get("document", {})
        style       = node_detail.get("style", {})
        if not style:
            continue

        lh_raw = style.get("lineHeightPx") or style.get("lineHeightPercentFontSize", 0)
        ls_raw = style.get("letterSpacing", 0)

        text_styles.append({
            "name":          style_meta.get("name", ""),
            "fontSize":      style.get("fontSize", 16),
            "fontWeight":    style.get("fontWeight", 400),
            "fontFamily":    style.get("fontFamily", "IBM Plex Sans"),
            "lineHeight":    round(lh_raw, 2) if lh_raw else None,
            "letterSpacing": round(ls_raw, 2) if ls_raw else 0,
        })

    return sorted(text_styles, key=lambda s: (s["fontSize"], s["fontWeight"]))


def extract_shadows_from_file(file_data: dict, nodes: dict) -> list:
    """
    Extract effect styles (box shadows) from the Figma file.
    Returns [{name, css}]
    """
    styles  = file_data.get("styles", {})
    shadows = []

    for node_id, style_meta in styles.items():
        if style_meta.get("styleType") != "EFFECT":
            continue
        node_detail = nodes.get(node_id, {}).get("document", {})
        effects     = node_detail.get("effects", [])
        css_parts   = []

        for effect in effects:
            if effect.get("type") not in ("DROP_SHADOW", "INNER_SHADOW"):
                continue
            color  = effect.get("color", {"r":0,"g":0,"b":0,"a":0.15})
            offset = effect.get("offset", {"x":0, "y":4})
            blur   = effect.get("radius", 6)
            spread = effect.get("spread", 0)
            inset  = "inset " if effect.get("type") == "INNER_SHADOW" else ""
            r, g, b, a = color["r"], color["g"], color["b"], color.get("a", 0.15)
            rgba_str = f"rgba({int(r*255)},{int(g*255)},{int(b*255)},{round(a,2)})"
            css_parts.append(
                f"{inset}{offset['x']}px {offset['y']}px {blur}px {spread}px {rgba_str}"
            )

        if css_parts:
            shadows.append({
                "name": style_meta.get("name", ""),
                "css":  ", ".join(css_parts),
            })

    return sorted(shadows, key=lambda s: s["name"])


# ── HTML injection ──────────────────────────────────────────────────────────────

SWITCH_TAB_JS = """
// ── COMPONENT TABS ────────────────────────────────────────────────────────────
function switchTab(btn, panelId) {
  const section = btn.closest('.section');
  section.querySelectorAll('.comp-tab').forEach(t => t.classList.remove('active'));
  section.querySelectorAll('.comp-tab-panel').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  const panel = document.getElementById(panelId);
  if (panel) panel.classList.add('active');
}
"""


def build_token_script(primitives, semantic, spacing, typography, shadows) -> str:
    """
    Build the <script> block that will replace the content between the sync markers.
    """
    # Split spacing by collection (gracefully handle missing "collection" key)
    spacing_tokens = [t for t in spacing if isinstance(t, dict) and t.get("collection") == "Spacing"]
    radius_tokens  = [t for t in spacing if isinstance(t, dict) and t.get("collection") == "Border Radius"]
    ls_tokens      = [t for t in spacing if isinstance(t, dict) and t.get("collection") == "Letter Spacing"]

    colors_json  = json.dumps(primitives, ensure_ascii=False)
    spacing_json = json.dumps(
        [{"name": t["name"], "value": t.get("px", t.get("value", 0))} for t in spacing_tokens],
        ensure_ascii=False
    )
    radius_json  = json.dumps(
        [{"name": t["name"], "value": t.get("px", t.get("value", 0))} for t in radius_tokens],
        ensure_ascii=False
    )
    ls_json      = json.dumps(
        [{"name": t["name"], "value": t.get("px", t.get("value", 0))} for t in ls_tokens],
        ensure_ascii=False
    )
    typo_json    = json.dumps(typography, ensure_ascii=False)
    shadows_json = json.dumps(shadows, ensure_ascii=False)

    # Semantic tokens as clean JSON so load_fallback_data() can parse it reliably
    semantic_str = json.dumps(semantic, ensure_ascii=False, indent=2)

    script = f"""<script>
window.DS = {{"colors": {colors_json}}};

// Semantic tokens
window.DS.semantic = {semantic_str};

// Spacing tokens
window.DS.spacing = {spacing_json};

// Border radius tokens
window.DS.radius = {radius_json};

// Letter spacing tokens
window.DS.letterSpacing = {ls_json};

// Typography styles
window.DS.typography = {typo_json};

// Shadow styles
window.DS.shadows = {shadows_json};
{SWITCH_TAB_JS}
</script>"""
    return script


def inject_into_html(script_block: str) -> None:
    """Replace the content between FIGMA_TOKENS_START and FIGMA_TOKENS_END in the HTML file."""
    html = DOCS_FILE.read_text(encoding="utf-8")
    if MARKER_START not in html or MARKER_END not in html:
        print(f"  ❌ Sync markers not found in {DOCS_FILE}. Cannot inject.")
        sys.exit(1)

    pattern     = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        re.DOTALL
    )
    replacement = f"{MARKER_START}\n{script_block}\n{MARKER_END}"
    new_html    = pattern.sub(replacement, html)

    DOCS_FILE.write_text(new_html, encoding="utf-8")
    print(f"  ✅ Updated {DOCS_FILE.name}  ({len(new_html):,} chars)")


# ── Fallback data (used when variables API isn't available) ─────────────────────

def load_fallback_data() -> tuple[list, list, list]:
    """
    If the Figma variables API is unavailable, return the existing token data
    embedded in the current HTML file so the script doesn't wipe everything.
    Reads each window.DS.xxx assignment separately (they are separate JS statements).
    """
    print("  Using existing token data as fallback (no changes to colors/spacing).")
    html = DOCS_FILE.read_text(encoding="utf-8")

    def extract_json_array(pattern: str) -> list:
        m = re.search(pattern, html, re.DOTALL)
        if not m:
            return []
        raw = m.group(1).strip()
        # Strip single-line JS comments before parsing
        raw = re.sub(r'//[^\n]*', '', raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    # Colors come from the main window.DS = {"colors": [...]} assignment
    colors: list = []
    main_match = re.search(r'window\.DS\s*=\s*(\{.*?\});', html, re.DOTALL)
    if main_match:
        try:
            existing = json.loads(main_match.group(1))
            colors = existing.get("colors", [])
        except json.JSONDecodeError:
            pass

    # Semantic, spacing, radius are separate window.DS.xxx = [...] assignments
    semantic = extract_json_array(r'window\.DS\.semantic\s*=\s*(\[.*?\]);')
    spacing  = extract_json_array(r'window\.DS\.spacing\s*=\s*(\[.*?\]);')

    print(f"  Fallback: {len(colors)} colors, {len(semantic)} semantic tokens, {len(spacing)} spacing tokens")
    return colors, semantic, spacing


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    if not FIGMA_TOKEN:
        print("❌  FIGMA_TOKEN environment variable is not set.")
        print("    Get one at: https://www.figma.com/settings → Personal access tokens")
        sys.exit(1)

    print(f"\n🐦 BlackBirdDS — Figma Sync")
    print(f"   File ID : {FIGMA_FILE_ID}")
    print(f"   Docs    : {DOCS_FILE}\n")

    # ── Step 1: Fetch variables ──────────────────────────────────────────────
    print("1/4  Fetching variables…")
    var_data   = fetch_variables()
    primitives = []
    semantic   = []
    spacing    = []

    if var_data:
        print("     ✓ Variables API available")
        primitives, semantic = extract_colors_from_variables(var_data)
        spacing              = extract_spacing_from_variables(var_data)
        print(f"     {len(primitives)} primitive colors, {len(semantic)} semantic tokens, {len(spacing)} spacing/radius tokens")
    else:
        primitives, semantic, spacing = load_fallback_data()

    # ── Step 2: Fetch file + styles ──────────────────────────────────────────
    print("2/4  Fetching file & styles…")
    file_data = fetch_file()
    all_styles = file_data.get("styles", {})
    text_ids   = [nid for nid, s in all_styles.items() if s.get("styleType") == "TEXT"]
    effect_ids = [nid for nid, s in all_styles.items() if s.get("styleType") == "EFFECT"]
    print(f"     {len(text_ids)} text styles, {len(effect_ids)} effect styles")

    # ── Step 3: Fetch node details for styles ────────────────────────────────
    print("3/4  Fetching style node details…")
    all_style_ids = text_ids + effect_ids
    nodes         = {}
    for i in range(0, len(all_style_ids), 50):
        batch  = all_style_ids[i:i + 50]
        chunk  = fetch_node_details(batch)
        nodes.update(chunk)
    print(f"     {len(nodes)} nodes fetched")

    typography = extract_typography_from_file(file_data, nodes)
    shadows    = extract_shadows_from_file(file_data, nodes)
    print(f"     {len(typography)} typography styles, {len(shadows)} shadows parsed")

    # ── Step 4: Rebuild the HTML data block ──────────────────────────────────
    print("4/4  Injecting tokens into HTML…")
    script_block = build_token_script(primitives, semantic, spacing, typography, shadows)
    inject_into_html(script_block)

    # ── Step 5: Regenerate tokens.css for Storybook / component use ──────────
    print("5/5  Regenerating tokens.css…")
    generate_tokens_css(primitives, semantic, spacing)

    print(f"\n✅  Sync complete!\n")


# ── CSS token generator ──────────────────────────────────────────────────────

CSS_FILE = Path(__file__).parent.parent / "components" / "tokens.css"

CATEGORY_MAP = {
    "bg": "Background", "background": "Background",
    "text": "Text",
    "border": "Border",
    "accent": "Accent",
    "success": "Success", "warning": "Warning",
    "error": "Error", "info": "Info",
}

def _css_name(token_name: str) -> str:
    """Convert 'color/bg/surface' → '--color-bg-surface'."""
    return "--" + token_name.replace("/", "-")


def generate_tokens_css(primitives: list, semantic: list, spacing: list) -> None:
    """
    Write components/tokens.css with:
      - Primitive brand/gray palette as CSS custom props
      - Semantic tokens in :root (Light) and @media dark
      - Spacing scale
      - Border-radius scale
    """
    lines = [
        "/**",
        " * BlackBirdDS — Design Tokens (auto-generated)",
        " * Do not edit manually — run scripts/sync_from_figma.py to update.",
        " */",
        "",
        "/* ── Primitive colors ─────────────────────────────────────────────── */",
        ":root {",
    ]
    for p in primitives:
        prop = "--" + p["name"].replace("/", "-")
        lines.append(f"  {prop}: {p['hex']};")
    lines += ["}", ""]

    # ── Semantic tokens — split Light / Dark ──────────────────────────────────
    light_lines = ["/* ── Semantic tokens — Light mode ──────────────────────────────── */", ":root {"]
    dark_lines  = ["/* ── Semantic tokens — Dark mode ───────────────────────────────── */",
                   "@media (prefers-color-scheme: dark) {", "  :root {"]

    current_cat = None
    for tok in semantic:
        if tok.get("category") != current_cat:
            current_cat = tok.get("category", "Other")
            light_lines.append(f"\n  /* {current_cat} */")
            dark_lines.append(f"\n    /* {current_cat} */")
        prop = _css_name(tok["name"])
        light_lines.append(f"  {prop}: {tok['light']};")
        dark_lines.append(f"    {prop}: {tok['dark']};")

    light_lines.append("}")
    dark_lines  += ["  }", "}"]
    lines += light_lines + [""] + dark_lines + [""]

    # ── Spacing ───────────────────────────────────────────────────────────────
    sp_tokens  = [t for t in spacing if "tracking" not in t.get("name","")]
    rad_tokens = [t for t in spacing if t.get("collection","") == "Border Radius"]

    if sp_tokens:
        lines += ["/* ── Spacing scale ──────────────────────────────────────────────── */", ":root {"]
        for t in sp_tokens:
            prop = _css_name(t["name"])
            val  = t.get("value", t.get("px", 0))
            lines.append(f"  {prop}: {val}px;")
        lines += ["}", ""]

    if rad_tokens:
        lines += ["/* ── Border radius ──────────────────────────────────────────────── */", ":root {"]
        for t in rad_tokens:
            prop = _css_name(t["name"])
            val  = t.get("value", t.get("px", 0))
            lines.append(f"  {prop}: {val}px;")
        lines += ["}", ""]

    CSS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CSS_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"  ✅ Updated {CSS_FILE.name}  ({CSS_FILE.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
