import argparse
import json
import os
import sys


def _dedupe_str_list(items):
    deduped = []
    seen = set()
    for item in items:
        if not isinstance(item, str):
            continue
        normalized = " ".join(item.strip().split())
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def _normalize_prompt(prompt):
    if not isinstance(prompt, str):
        return ""
    return prompt.strip()


def _load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("evolution.json must be a JSON object")
    return data


def build_draft(evolution_data, skill_dir):
    preferences = _dedupe_str_list(evolution_data.get("preferences", []))
    fixes = _dedupe_str_list(evolution_data.get("fixes", []))
    custom_prompts = _normalize_prompt(evolution_data.get("custom_prompts", ""))

    draft = {
        "preferences": preferences,
        "fixes": fixes,
        "custom_prompts": custom_prompts,
        "_meta": {
            "source_skill_dir": skill_dir,
            "instructions": [
                "Only edit preferences/fixes/custom_prompts.",
                "Remove duplicates and merge near-duplicate items.",
                "Keep each item atomic, generic, and reusable for the target skill.",
                "Place stable style/workflow guidance in preferences.",
                "Place validated corrective actions in fixes.",
                "Keep custom_prompts concise and high-leverage.",
            ],
        },
    }
    return draft


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare an evolution draft JSON for agent optimization."
    )
    parser.add_argument("skill_dir", help="Target skill directory")
    parser.add_argument(
        "--out",
        default="",
        help="Output draft path (default: <skill_dir>/evolution_draft.json)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    evolution_json_path = os.path.join(args.skill_dir, "evolution.json")
    out_path = args.out or os.path.join(args.skill_dir, "evolution_draft.json")

    try:
        evolution_data = _load_json(evolution_json_path)
        draft = build_draft(evolution_data, args.skill_dir)
    except Exception as e:
        print(f"Error preparing draft: {e}", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2, ensure_ascii=False)

    print(f"Prepared draft at {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
