"""Controlled name-prefix import experiment; never changes DRC rules or GDS."""

PROVIDER_PATTERNS = ("lvsres_*", "*_CELL_SUB", "VIA_M1_*", "VIA_M2_*",
                     "RSC_*", "*_CELL_CORNER")
PROVIDER_IMPORT_SHA256 = "b320bf2513c6856affa403d66c7bf9bb5d9753dc6db1c3a6edadccad01270309"


def render_import_script(original, mode):
    if mode not in ("official", "jq-prefixed"):
        raise ValueError(f"Unknown import experiment: {mode}")
    commands = [line.strip() for line in original.splitlines()
                if line.strip() and not line.lstrip().startswith("#")]
    if commands != [f"gds flatglob {pattern}" for pattern in PROVIDER_PATTERNS]:
        raise ValueError("Provider import commands differ from the audited six patterns")
    if mode == "official":
        return original
    # Suffix patterns already match prefixed names. Add only the four missing
    # prefix variants; retain every original command and all geometry/checks.
    added = [f"gds flatglob JQ_{pattern}" for pattern in PROVIDER_PATTERNS
             if not pattern.startswith("*")]
    return original + "\n# Diagnostic only: same provider cell families with JQ_ names.\n" + "\n".join(added) + "\n"
