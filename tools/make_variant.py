"""Builds a renamed copy of the integration that runs next to the regular one in the same Home Assistant.

    python tools/make_variant.py <target dir> [--suffix test] [--title "NeonPlan 3D Test"]

Example: `python tools/make_variant.py ~/ha-config/custom_components/neonplan3d_test` writes the domain
`neonplan3d_test` with its own stores (plans, packs, settings), sidebar page `/neonplan3d_test`, card
`custom:neonplan3d_test-card`, services `neonplan3d_test.*`, WebSocket commands, bundle files and Assist
intent. Nothing is shared with the regular `neonplan3d`, so a test install never touches the real plans.

Run `npm run build` in frontend/ first: the committed bundles are copied as they are.
Links to the project's sites (GitHub, the shop, the manual, the online demo) are left alone.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "custom_components" / "neonplan3d"
TEXT_SUFFIXES = {".py", ".js", ".json", ".yaml", ".yml", ".txt", ".md", ".html", ".css"}

# web addresses of the project that contain "neonplan3d" and must stay as they are
_KEEP_BEFORE = [
    r"github\.com/tobsen1302/",
    r"github\.com/Mastershort/",
    r"github\.com/mastershort/",
    r"githubusercontent\.com/tobsen1302/",
    r"githubusercontent\.com/Mastershort/",
    r"mastershort\.de/",
    r"mastershort\.de/en/",
]
# "neonplan3d" as the name of the integration (domain, stores, URLs, elements, files)
NAME = re.compile(r"(?<![A-Za-z0-9_])" + "".join(f"(?<!{k})" for k in _KEEP_BEFORE) + r"neonplan3d(?!\.mastershort)")
# the bundles define their inner elements as "fp3d-…" only when no element of that name exists yet: with two
# integrations on one page the second would use the first one's elements (and talk to its stores), so the copy
# gets elements, classes and CSS variables of its own
FP3D = re.compile(r"(?<![A-Za-z0-9_])fp3d-")
# the card's entry in the dashboard's card picker (minified: name:X(void 0,"card_name"))
CARD_NAME = re.compile(
    r'(customCards\.push\(\{type:"neonplan3d_[a-z0-9]+-card",name:)[A-Za-z_$][\w$]*\(void 0,"card_name"\)'
)


def transform(text: str, suffix: str, title: str) -> str:
    """Rename the integration in a Python, JSON or YAML file."""
    domain = f"neonplan3d_{suffix}"
    text = NAME.sub(domain, text)
    # the Assist intent is global in Home Assistant: two integrations must not register the same one
    text = text.replace("NeonPlanAsk", f"NeonPlan{suffix.capitalize()}Ask")
    # the stores of the integration's earlier name are taken over once: not by a test copy
    text = text.replace('LEGACY_DOMAIN = "floorplan_3d"', f'LEGACY_DOMAIN = "{domain}_no_legacy"')
    return text.replace('PANEL_TITLE = "NeonPlan 3D"', f'PANEL_TITLE = "{title}"')


def transform_js(text: str, suffix: str, title: str) -> str:
    """Rename the integration in a bundle, with elements and CSS of its own."""
    text = FP3D.sub(f"fp3d{suffix}-", transform(text, suffix, title))
    text = CARD_NAME.sub(lambda m: m.group(1) + json.dumps(title), text)
    return text.replace("fp3dReloadSent", f"fp3d{suffix}ReloadSent")


def main() -> int:
    """Write the copy and check that nothing of the old name is left."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("target", type=Path, help="the new folder, e.g. <config>/custom_components/neonplan3d_test")
    parser.add_argument("--suffix", default="test", help="domain suffix: neonplan3d_<suffix> (a-z, 0-9)")
    parser.add_argument("--title", default="NeonPlan 3D Test", help="name in the sidebar and the integration list")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9]{1,20}", args.suffix):
        parser.error("--suffix: only a-z and 0-9")
    domain = f"neonplan3d_{args.suffix}"
    target: Path = args.target.resolve()
    if target.name != domain:
        parser.error(f"the folder must be named {domain} (Home Assistant loads an integration by its folder name)")
    if target.exists():
        shutil.rmtree(target)
    for src in sorted(SOURCE.rglob("*")):
        if "__pycache__" in src.parts or src.is_dir():
            continue
        rel = src.relative_to(SOURCE)
        dst = target / Path(*[NAME.sub(domain, part) for part in rel.parts])
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix == ".js":
            dst.write_text(transform_js(src.read_text(encoding="utf-8"), args.suffix, args.title), encoding="utf-8")
        elif src.suffix in TEXT_SUFFIXES:
            dst.write_text(transform(src.read_text(encoding="utf-8"), args.suffix, args.title), encoding="utf-8")
        else:
            shutil.copyfile(src, dst)
    manifest_path = target / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["name"] = args.title
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # what is left of the old name (the new one, neonplan3d_<suffix>, contains it)
    old = re.compile(NAME.pattern + f"(?!_{args.suffix})")
    left = [
        str(p.relative_to(target))
        for p in target.rglob("*")
        if p.is_file() and p.suffix in TEXT_SUFFIXES and old.search(p.read_text(encoding="utf-8"))
    ]
    if left:
        print("not renamed everywhere:", ", ".join(left), file=sys.stderr)
        return 1
    print(f"{domain} {manifest['version']} written to {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
