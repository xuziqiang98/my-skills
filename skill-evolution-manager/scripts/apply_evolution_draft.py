import argparse
import json
import os
import sys

CORE_KEYS = {"preferences", "fixes", "custom_prompts"}
ALLOWED_DRAFT_KEYS = CORE_KEYS | {"_meta"}


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
        raise ValueError("Field 'custom_prompts' must be string")
    return prompt.strip()


def _validate_draft(draft):
    if not isinstance(draft, dict):
        raise ValueError("Draft JSON must be an object")

    unknown = sorted(set(draft.keys()) - ALLOWED_DRAFT_KEYS)
    if unknown:
        raise ValueError(
            f"Unsupported keys in draft: {unknown}. Allowed keys: {sorted(ALLOWED_DRAFT_KEYS)}"
        )

    if "preferences" in draft and not isinstance(draft["preferences"], list):
        raise ValueError("Field 'preferences' must be a list of strings")
    if "fixes" in draft and not isinstance(draft["fixes"], list):
        raise ValueError("Field 'fixes' must be a list of strings")
    if "custom_prompts" in draft and not isinstance(draft["custom_prompts"], str):
        raise ValueError("Field 'custom_prompts' must be string")


def _build_canonical_data(draft):
    preferences = _dedupe_str_list(draft.get("preferences", []))
    fixes = _dedupe_str_list(draft.get("fixes", []))
    custom_prompts = _normalize_prompt(draft.get("custom_prompts", ""))

    canonical = {
        "preferences": preferences,
        "fixes": fixes,
    }
    if custom_prompts:
        canonical["custom_prompts"] = custom_prompts
    return canonical


def parse_args():
    parser = argparse.ArgumentParser(
        description="Apply optimized evolution draft and overwrite evolution.json."
    )
    parser.add_argument("skill_dir", help="Target skill directory")
    parser.add_argument("draft_path", help="Draft JSON path to apply")
    parser.add_argument(
        "--keep-draft",
        action="store_true",
        help="Keep draft file after successful apply",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    evolution_json_path = os.path.join(args.skill_dir, "evolution.json")

    try:
        with open(args.draft_path, "r", encoding="utf-8") as f:
            draft = json.load(f)
        _validate_draft(draft)
        canonical = _build_canonical_data(draft)
    except Exception as e:
        print(f"Error applying draft: {e}", file=sys.stderr)
        return 1

    with open(evolution_json_path, "w", encoding="utf-8") as f:
        json.dump(canonical, f, indent=2, ensure_ascii=False)
    print(f"Applied optimized evolution data to {evolution_json_path}")

    if not args.keep_draft and os.path.exists(args.draft_path):
        os.remove(args.draft_path)
        print(f"Removed draft file {args.draft_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
