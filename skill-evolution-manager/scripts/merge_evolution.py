import os
import sys
import json

ALLOWED_KEYS = {"preferences", "fixes", "custom_prompts"}


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


def _validate_new_data_shape(new_data):
    if not isinstance(new_data, dict):
        raise ValueError("New evolution data must be a JSON object")

    unknown_keys = sorted(set(new_data.keys()) - ALLOWED_KEYS)
    if unknown_keys:
        raise ValueError(
            f"Unsupported keys in new evolution data: {unknown_keys}. "
            f"Only {sorted(ALLOWED_KEYS)} are allowed."
        )

    for key in ("preferences", "fixes"):
        if key in new_data and not isinstance(new_data[key], list):
            raise ValueError(f"Field '{key}' must be a list of strings")

    if "custom_prompts" in new_data and not isinstance(new_data["custom_prompts"], str):
        raise ValueError("Field 'custom_prompts' must be a string")


def _load_core_data(evolution_json_path):
    if not os.path.exists(evolution_json_path):
        return {}
    try:
        with open(evolution_json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return {}

    if not isinstance(raw, dict):
        return {}

    core = {}
    if "preferences" in raw and isinstance(raw["preferences"], list):
        core["preferences"] = _dedupe_str_list(raw["preferences"])
    if "fixes" in raw and isinstance(raw["fixes"], list):
        core["fixes"] = _dedupe_str_list(raw["fixes"])
    if "custom_prompts" in raw and isinstance(raw["custom_prompts"], str):
        prompt = raw["custom_prompts"].strip()
        if prompt:
            core["custom_prompts"] = prompt
    return core

def merge_evolution(skill_dir, new_data_json_str):
    """
    Merges new evolution data into existing evolution.json.
    Deduplicates list items.
    """
    evolution_json_path = os.path.join(skill_dir, "evolution.json")

    current_data = _load_core_data(evolution_json_path)

    try:
        new_data = json.loads(new_data_json_str)
        _validate_new_data_shape(new_data)
    except json.JSONDecodeError as e:
        print(f"Error decoding new data JSON: {e}", file=sys.stderr)
        return False
    except ValueError as e:
        print(f"Error validating new evolution data: {e}", file=sys.stderr)
        return False

    # Merge logic
    for list_key in ["preferences", "fixes"]:
        if list_key in new_data:
            existing_list = current_data.get(list_key, [])
            merged = existing_list + new_data[list_key]
            current_data[list_key] = _dedupe_str_list(merged)

    if "custom_prompts" in new_data:
        prompt = new_data["custom_prompts"].strip()
        if prompt:
            current_data["custom_prompts"] = prompt
        else:
            current_data.pop("custom_prompts", None)

    # Save back
    with open(evolution_json_path, "w", encoding="utf-8") as f:
        json.dump(current_data, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully merged evolution data for {os.path.basename(skill_dir)}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python merge_evolution.py <skill_dir> <json_string>")
        sys.exit(1)
        
    skill_dir = sys.argv[1]
    json_str = sys.argv[2]
    ok = merge_evolution(skill_dir, json_str)
    sys.exit(0 if ok else 1)
