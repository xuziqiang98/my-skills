import os
import sys
import json
import re

EVOLUTION_TITLE = "User-Learned Best Practices & Constraints"
AUTO_GENERATED_NOTE = "> **Auto-Generated**: This file is maintained by `skill-evolution-manager`. Do not edit manually."
REFERENCE_BLOCK_START = "<!-- EVOLUTION_REFERENCE:START -->"
REFERENCE_BLOCK_END = "<!-- EVOLUTION_REFERENCE:END -->"


def build_evolution_markdown(data):
    lines = [f"# {EVOLUTION_TITLE}", "", AUTO_GENERATED_NOTE, ""]

    if data.get("preferences"):
        lines.append("## User Preferences")
        lines.append("")
        for item in data["preferences"]:
            lines.append(f"- {item}")
        lines.append("")

    if data.get("fixes"):
        lines.append("## Known Fixes & Workarounds")
        lines.append("")
        for item in data["fixes"]:
            lines.append(f"- {item}")
        lines.append("")

    if data.get("custom_prompts"):
        lines.append("## Custom Instruction Injection")
        lines.append("")
        lines.append(f"{data['custom_prompts']}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def upsert_skill_reference_block(skill_md_path):
    reference_block = "\n".join(
        [
            REFERENCE_BLOCK_START,
            "## Evolution Learned Reference",
            "",
            "> Evolution data is maintained in `references/evolution_learned.md` by `skill-evolution-manager`.",
            REFERENCE_BLOCK_END,
        ]
    )

    with open(skill_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = rf"\n*{re.escape(REFERENCE_BLOCK_START)}.*?{re.escape(REFERENCE_BLOCK_END)}\n*"
    replacement = f"\n\n{reference_block}\n"

    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)
        print("Updating existing evolution reference block...", file=sys.stderr)
    else:
        print("Appending evolution reference block...", file=sys.stderr)
        if not content.endswith("\n"):
            content += "\n"
        new_content = content + "\n" + reference_block + "\n"

    with open(skill_md_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def stitch_skill(skill_dir):
    """
    Reads evolution.json and writes evolution content to references/evolution_learned.md.
    Also appends/updates a reference block in SKILL.md.
    """
    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    evolution_json_path = os.path.join(skill_dir, "evolution.json")
    references_dir = os.path.join(skill_dir, "references")
    evolution_md_path = os.path.join(references_dir, "evolution_learned.md")

    if not os.path.exists(skill_md_path):
        print(f"Error: SKILL.md not found in {skill_dir}", file=sys.stderr)
        return False
        
    if not os.path.exists(evolution_json_path):
        print(f"Info: No evolution.json found in {skill_dir}. Nothing to stitch.", file=sys.stderr)
        return True

    try:
        with open(evolution_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error parsing evolution.json: {e}", file=sys.stderr)
        return False

    os.makedirs(references_dir, exist_ok=True)
    evolution_content = build_evolution_markdown(data)

    with open(evolution_md_path, "w", encoding="utf-8") as f:
        f.write(evolution_content)
    print(f"Successfully wrote evolution data into {evolution_md_path}")

    upsert_skill_reference_block(skill_md_path)
    print(f"Successfully updated evolution reference in {skill_md_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smart_stitch.py <skill_dir>")
        sys.exit(1)
        
    target_dir = sys.argv[1]
    stitch_skill(target_dir)
