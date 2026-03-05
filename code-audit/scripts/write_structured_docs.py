#!/usr/bin/env python3
import argparse
import json
import os
import sys
import tempfile
from typing import Any, Dict, List

KIND_TO_FILENAME = {
    "project_summary": "project_summary.md",
    "source_index": "source_index.md",
    "sink_index": "sink_index.md",
    "defense_catalog": "defense_catalog.md",
    "progress": "progress.md",
    "findings": "findings.md",
    "interaction_matrix": "interaction_matrix.md",
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SEVERITY_LABEL = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}
SOURCE_RISK_LABEL = {"critical": "🔴 高", "high": "🔴 高", "medium": "🟡 中", "low": "🟢 低"}
STATUS_LABEL = {
    "pending": "⬼ 待分析",
    "in_progress": "▶️ 分析中",
    "completed": "✅ 已完成",
    "skipped": "⏸ 跳过",
}


class ValidationError(Exception):
    pass


def _type_name(value: Any) -> str:
    return type(value).__name__


def expect_dict(data: Any, path: str) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValidationError(f"{path} must be an object, got {_type_name(data)}")
    return data


def expect_str(data: Dict[str, Any], key: str, path: str, optional: bool = False) -> str:
    if key not in data:
        if optional:
            return ""
        raise ValidationError(f"{path}.{key} is required")
    value = data[key]
    if not isinstance(value, str):
        raise ValidationError(f"{path}.{key} must be string, got {_type_name(value)}")
    if not optional and value.strip() == "":
        raise ValidationError(f"{path}.{key} must not be empty")
    return value


def expect_int(data: Dict[str, Any], key: str, path: str, optional: bool = False) -> int:
    if key not in data:
        if optional:
            return 0
        raise ValidationError(f"{path}.{key} is required")
    value = data[key]
    if not isinstance(value, int):
        raise ValidationError(f"{path}.{key} must be int, got {_type_name(value)}")
    if value < 0:
        raise ValidationError(f"{path}.{key} must be >= 0")
    return value


def expect_bool(data: Dict[str, Any], key: str, path: str, optional: bool = False) -> bool:
    if key not in data:
        if optional:
            return False
        raise ValidationError(f"{path}.{key} is required")
    value = data[key]
    if not isinstance(value, bool):
        raise ValidationError(f"{path}.{key} must be bool, got {_type_name(value)}")
    return value


def expect_enum(
    data: Dict[str, Any], key: str, allowed: List[str], path: str, optional: bool = False, default: str = ""
) -> str:
    if key not in data:
        if optional:
            return default
        raise ValidationError(f"{path}.{key} is required")
    value = data[key]
    if not isinstance(value, str):
        raise ValidationError(f"{path}.{key} must be string, got {_type_name(value)}")
    if value not in allowed:
        raise ValidationError(f"{path}.{key} must be one of {allowed}, got {value}")
    return value


def expect_list(data: Dict[str, Any], key: str, path: str, optional: bool = False) -> List[Any]:
    if key not in data:
        if optional:
            return []
        raise ValidationError(f"{path}.{key} is required")
    value = data[key]
    if not isinstance(value, list):
        raise ValidationError(f"{path}.{key} must be list, got {_type_name(value)}")
    return value


def expect_list_str(data: Dict[str, Any], key: str, path: str, optional: bool = False) -> List[str]:
    items = expect_list(data, key, path, optional=optional)
    for i, item in enumerate(items):
        if not isinstance(item, str):
            raise ValidationError(f"{path}.{key}[{i}] must be string, got {_type_name(item)}")
    return items


def md_cell(value: Any) -> str:
    text = str(value) if value is not None else "-"
    text = text.replace("\n", " ").replace("|", "\\|").strip()
    return text or "-"


def as_bullet(items: List[str]) -> str:
    if not items:
        return "- 无"
    return "\n".join(f"- {item}" for item in items)


def validate_payload(kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    root = expect_dict(payload, "payload")
    payload_kind = expect_str(root, "kind", "payload")
    if payload_kind != kind:
        raise ValidationError(f"payload.kind ({payload_kind}) must match --kind ({kind})")
    expect_str(root, "version", "payload")
    expect_str(root, "generated_at", "payload")
    data = expect_dict(root.get("data"), "payload.data")

    validator = {
        "project_summary": validate_project_summary,
        "source_index": validate_source_index,
        "sink_index": validate_sink_index,
        "defense_catalog": validate_defense_catalog,
        "progress": validate_progress,
        "findings": validate_findings,
        "interaction_matrix": validate_interaction_matrix,
    }[kind]
    validated = validator(data)
    return {
        "kind": kind,
        "version": root["version"],
        "generated_at": root["generated_at"],
        "data": validated,
    }


def validate_project_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "project_name": expect_str(data, "project_name", "payload.data"),
        "repo_root": expect_str(data, "repo_root", "payload.data"),
        "project_types": expect_list_str(data, "project_types", "payload.data"),
        "languages": expect_list_str(data, "languages", "payload.data"),
        "frameworks": expect_list_str(data, "frameworks", "payload.data", optional=True),
        "architecture_patterns": expect_list_str(data, "architecture_patterns", "payload.data", optional=True),
        "key_entrypoints": expect_list_str(data, "key_entrypoints", "payload.data", optional=True),
        "security_focus": expect_list_str(data, "security_focus", "payload.data", optional=True),
        "assumptions": expect_list_str(data, "assumptions", "payload.data", optional=True),
    }


def validate_source_index(data: Dict[str, Any]) -> Dict[str, Any]:
    sources = expect_list(data, "sources", "payload.data")
    normalized = []
    for i, raw in enumerate(sources):
        item = expect_dict(raw, f"payload.data.sources[{i}]")
        normalized.append(
            {
                "id": expect_str(item, "id", f"payload.data.sources[{i}]"),
                "entry_point": expect_str(item, "entry_point", f"payload.data.sources[{i}]"),
                "location": expect_str(item, "location", f"payload.data.sources[{i}]"),
                "data_types": expect_list_str(item, "data_types", f"payload.data.sources[{i}]"),
                "risk": expect_enum(
                    item, "risk", ["critical", "high", "medium", "low"], f"payload.data.sources[{i}]"
                ),
                "downstream_modules": expect_list_str(
                    item, "downstream_modules", f"payload.data.sources[{i}]", optional=True
                ),
                "notes": expect_str(item, "notes", f"payload.data.sources[{i}]", optional=True),
            }
        )
    return {"sources": normalized}


def validate_sink_index(data: Dict[str, Any]) -> Dict[str, Any]:
    sinks = expect_list(data, "sinks", "payload.data")
    normalized = []
    for i, raw in enumerate(sinks):
        item = expect_dict(raw, f"payload.data.sinks[{i}]")
        normalized.append(
            {
                "id": expect_str(item, "id", f"payload.data.sinks[{i}]"),
                "sink": expect_str(item, "sink", f"payload.data.sinks[{i}]"),
                "location": expect_str(item, "location", f"payload.data.sinks[{i}]"),
                "sink_type": expect_str(item, "sink_type", f"payload.data.sinks[{i}]"),
                "required_privilege": expect_str(item, "required_privilege", f"payload.data.sinks[{i}]"),
                "impact": expect_str(item, "impact", f"payload.data.sinks[{i}]"),
                "sanitizers": expect_list_str(item, "sanitizers", f"payload.data.sinks[{i}]", optional=True),
                "notes": expect_str(item, "notes", f"payload.data.sinks[{i}]", optional=True),
            }
        )
    return {"sinks": normalized}


def validate_defense_catalog(data: Dict[str, Any]) -> Dict[str, Any]:
    defenses = expect_list(data, "defenses", "payload.data")
    normalized = []
    for i, raw in enumerate(defenses):
        item = expect_dict(raw, f"payload.data.defenses[{i}]")
        normalized.append(
            {
                "id": expect_str(item, "id", f"payload.data.defenses[{i}]"),
                "defense": expect_str(item, "defense", f"payload.data.defenses[{i}]"),
                "defense_type": expect_str(item, "defense_type", f"payload.data.defenses[{i}]"),
                "location": expect_str(item, "location", f"payload.data.defenses[{i}]"),
                "coverage": expect_list_str(item, "coverage", f"payload.data.defenses[{i}]"),
                "reversal_risk": expect_enum(
                    item, "reversal_risk", ["low", "medium", "high"], f"payload.data.defenses[{i}]"
                ),
                "notes": expect_str(item, "notes", f"payload.data.defenses[{i}]", optional=True),
            }
        )
    return {"defenses": normalized}


def validate_progress(data: Dict[str, Any]) -> Dict[str, Any]:
    items = expect_list(data, "items", "payload.data")
    normalized = []
    for i, raw in enumerate(items):
        item = expect_dict(raw, f"payload.data.items[{i}]")
        normalized.append(
            {
                "id": expect_str(item, "id", f"payload.data.items[{i}]"),
                "entry_point": expect_str(item, "entry_point", f"payload.data.items[{i}]"),
                "location": expect_str(item, "location", f"payload.data.items[{i}]"),
                "risk": expect_enum(
                    item, "risk", ["critical", "high", "medium", "low"], f"payload.data.items[{i}]"
                ),
                "status": expect_enum(
                    item,
                    "status",
                    ["pending", "in_progress", "completed", "skipped"],
                    f"payload.data.items[{i}]",
                ),
                "findings_count": expect_int(item, "findings_count", f"payload.data.items[{i}]", optional=True),
                "notes": expect_str(item, "notes", f"payload.data.items[{i}]", optional=True),
            }
        )

    total_sources = expect_int(data, "total_sources", "payload.data", optional=True)
    completed = expect_int(data, "completed", "payload.data", optional=True)
    skipped = expect_int(data, "skipped", "payload.data", optional=True)
    pending = expect_int(data, "pending", "payload.data", optional=True)

    if total_sources == 0:
        total_sources = len(normalized)
    if completed == 0 and "completed" not in data:
        completed = sum(1 for item in normalized if item["status"] == "completed")
    if skipped == 0 and "skipped" not in data:
        skipped = sum(1 for item in normalized if item["status"] == "skipped")
    if pending == 0 and "pending" not in data:
        pending = sum(1 for item in normalized if item["status"] == "pending")

    return {
        "total_sources": total_sources,
        "completed": completed,
        "skipped": skipped,
        "pending": pending,
        "items": normalized,
    }


def validate_findings(data: Dict[str, Any]) -> Dict[str, Any]:
    findings = expect_list(data, "findings", "payload.data")
    normalized = []
    for i, raw in enumerate(findings):
        item = expect_dict(raw, f"payload.data.findings[{i}]")
        evidence_score = expect_int(item, "evidence_score", f"payload.data.findings[{i}]")
        if evidence_score > 100:
            raise ValidationError(f"payload.data.findings[{i}].evidence_score must be <= 100")
        normalized.append(
            {
                "id": expect_str(item, "id", f"payload.data.findings[{i}]"),
                "title": expect_str(item, "title", f"payload.data.findings[{i}]"),
                "severity": expect_enum(
                    item, "severity", ["critical", "high", "medium", "low"], f"payload.data.findings[{i}]"
                ),
                "status": expect_enum(
                    item, "status", ["confirmed", "likely", "possible"], f"payload.data.findings[{i}]"
                ),
                "evidence_score": evidence_score,
                "type": expect_str(item, "type", f"payload.data.findings[{i}]"),
                "location": expect_str(item, "location", f"payload.data.findings[{i}]"),
                "source": expect_str(item, "source", f"payload.data.findings[{i}]", optional=True),
                "sink": expect_str(item, "sink", f"payload.data.findings[{i}]", optional=True),
                "summary": expect_str(item, "summary", f"payload.data.findings[{i}]"),
            }
        )
    return {"findings": normalized}


def validate_interaction_matrix(data: Dict[str, Any]) -> Dict[str, Any]:
    interactions = expect_list(data, "interactions", "payload.data")
    normalized = []
    for i, raw in enumerate(interactions):
        item = expect_dict(raw, f"payload.data.interactions[{i}]")
        normalized.append(
            {
                "id": expect_str(item, "id", f"payload.data.interactions[{i}]"),
                "vulnerability_a": expect_str(item, "vulnerability_a", f"payload.data.interactions[{i}]"),
                "vulnerability_b": expect_str(item, "vulnerability_b", f"payload.data.interactions[{i}]"),
                "effect": expect_str(item, "effect", f"payload.data.interactions[{i}]"),
                "description": expect_str(item, "description", f"payload.data.interactions[{i}]"),
                "severity": expect_enum(
                    item, "severity", ["critical", "high", "medium", "low"], f"payload.data.interactions[{i}]"
                ),
                "chainable": expect_bool(item, "chainable", f"payload.data.interactions[{i}]"),
            }
        )
    pairs_checked = expect_int(data, "pairs_checked", "payload.data")
    interactions_found = expect_int(data, "interactions_found", "payload.data", optional=True)
    if interactions_found == 0 and "interactions_found" not in data:
        interactions_found = len(normalized)
    return {"pairs_checked": pairs_checked, "interactions_found": interactions_found, "interactions": normalized}


def render_project_summary(payload: Dict[str, Any]) -> str:
    data = payload["data"]
    lines = [
        "# 项目审计概览",
        "",
        f"- 生成时间: {payload['generated_at']}",
        f"- 项目名称: {data['project_name']}",
        f"- 审计根目录: {data['repo_root']}",
        "",
        "## 项目类型",
        as_bullet(data["project_types"]),
        "",
        "## 主要语言",
        as_bullet(data["languages"]),
        "",
        "## 框架/技术栈",
        as_bullet(data["frameworks"]),
        "",
        "## 架构模式",
        as_bullet(data["architecture_patterns"]),
        "",
        "## 关键入口",
        as_bullet(data["key_entrypoints"]),
        "",
        "## 安全审计重点",
        as_bullet(data["security_focus"]),
        "",
        "## 假设与约束",
        as_bullet(data["assumptions"]),
        "",
    ]
    return "\n".join(lines)


def render_source_index(payload: Dict[str, Any]) -> str:
    rows = payload["data"]["sources"]
    lines = [
        "# 入口点清单",
        "",
        f"- 生成时间: {payload['generated_at']}",
        "",
        "| # | 入口点 | 位置 | 数据类型 | 初步风险 | 下游模块 | 备注 |",
        "|---|--------|------|----------|----------|----------|------|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {entry} | {loc} | {dtypes} | {risk} | {modules} | {notes} |".format(
                id=md_cell(row["id"]),
                entry=md_cell(row["entry_point"]),
                loc=md_cell(row["location"]),
                dtypes=md_cell(", ".join(row["data_types"])),
                risk=md_cell(SOURCE_RISK_LABEL[row["risk"]]),
                modules=md_cell(", ".join(row["downstream_modules"])),
                notes=md_cell(row["notes"]),
            )
        )
    lines.append("")
    return "\n".join(lines)


def render_sink_index(payload: Dict[str, Any]) -> str:
    rows = payload["data"]["sinks"]
    lines = [
        "# 敏感操作清单",
        "",
        f"- 生成时间: {payload['generated_at']}",
        "",
        "| # | Sink | 位置 | 类型 | 所需权限 | 影响 | Sanitizer | 备注 |",
        "|---|------|------|------|----------|------|-----------|------|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {sink} | {loc} | {stype} | {priv} | {impact} | {san} | {notes} |".format(
                id=md_cell(row["id"]),
                sink=md_cell(row["sink"]),
                loc=md_cell(row["location"]),
                stype=md_cell(row["sink_type"]),
                priv=md_cell(row["required_privilege"]),
                impact=md_cell(row["impact"]),
                san=md_cell(", ".join(row["sanitizers"])),
                notes=md_cell(row["notes"]),
            )
        )
    lines.append("")
    return "\n".join(lines)


def render_defense_catalog(payload: Dict[str, Any]) -> str:
    rows = payload["data"]["defenses"]
    lines = [
        "# 全局防御机制目录",
        "",
        f"- 生成时间: {payload['generated_at']}",
        "",
        "| # | 防御机制 | 类型 | 位置 | 覆盖范围 | 反转风险 | 备注 |",
        "|---|----------|------|------|----------|----------|------|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {defense} | {dtype} | {loc} | {cov} | {risk} | {notes} |".format(
                id=md_cell(row["id"]),
                defense=md_cell(row["defense"]),
                dtype=md_cell(row["defense_type"]),
                loc=md_cell(row["location"]),
                cov=md_cell(", ".join(row["coverage"])),
                risk=md_cell(row["reversal_risk"]),
                notes=md_cell(row["notes"]),
            )
        )
    lines.append("")
    return "\n".join(lines)


def render_progress(payload: Dict[str, Any]) -> str:
    data = payload["data"]
    rows = data["items"]
    lines = [
        "# 审计进度追踪",
        "",
        f"- 生成时间: {payload['generated_at']}",
        "",
        "总入口数: {total} | 已完成: {completed} | 跳过: {skipped} | 待分析: {pending}".format(
            total=data["total_sources"],
            completed=data["completed"],
            skipped=data["skipped"],
            pending=data["pending"],
        ),
        "",
        "| # | 入口点 | 位置 | 风险 | 状态 | 发现漏洞 | 备注 |",
        "|---|--------|------|------|------|----------|------|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {entry} | {loc} | {risk} | {status} | {cnt} | {notes} |".format(
                id=md_cell(row["id"]),
                entry=md_cell(row["entry_point"]),
                loc=md_cell(row["location"]),
                risk=md_cell(SOURCE_RISK_LABEL[row["risk"]]),
                status=md_cell(STATUS_LABEL[row["status"]]),
                cnt=md_cell(row["findings_count"]),
                notes=md_cell(row["notes"]),
            )
        )
    lines.append("")
    return "\n".join(lines)


def render_findings(payload: Dict[str, Any]) -> str:
    rows = payload["data"]["findings"]
    rows = sorted(rows, key=lambda x: (SEVERITY_ORDER[x["severity"]], x["id"]))
    lines = [
        "# 漏洞发现汇总",
        "",
        f"- 生成时间: {payload['generated_at']}",
        f"- 总发现数: {len(rows)}",
        "",
        "| ID | 标题 | 严重性 | 状态 | evidence_score | 位置 | 类型 | Source | Sink | 摘要 |",
        "|----|------|--------|------|----------------|------|------|--------|------|------|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {title} | {sev} | {status} | {score} | {loc} | {typ} | {src} | {sink} | {summary} |".format(
                id=md_cell(row["id"]),
                title=md_cell(row["title"]),
                sev=md_cell(SEVERITY_LABEL[row["severity"]]),
                status=md_cell(row["status"]),
                score=md_cell(row["evidence_score"]),
                loc=md_cell(row["location"]),
                typ=md_cell(row["type"]),
                src=md_cell(row["source"]),
                sink=md_cell(row["sink"]),
                summary=md_cell(row["summary"]),
            )
        )
    lines.append("")
    return "\n".join(lines)


def render_interaction_matrix(payload: Dict[str, Any]) -> str:
    data = payload["data"]
    rows = data["interactions"]
    lines = [
        "# 交互矩阵分析",
        "",
        f"- 生成时间: {payload['generated_at']}",
        f"- 已检查配对数量: {data['pairs_checked']}",
        f"- 发现交互数量: {data['interactions_found']}",
        "",
        "| # | 漏洞A | 漏洞B | 交互效应 | 严重性 | 可串联 | 描述 |",
        "|---|-------|-------|----------|--------|--------|------|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {a} | {b} | {effect} | {sev} | {chain} | {desc} |".format(
                id=md_cell(row["id"]),
                a=md_cell(row["vulnerability_a"]),
                b=md_cell(row["vulnerability_b"]),
                effect=md_cell(row["effect"]),
                sev=md_cell(SEVERITY_LABEL[row["severity"]]),
                chain=md_cell("是" if row["chainable"] else "否"),
                desc=md_cell(row["description"]),
            )
        )
    lines.append("")
    return "\n".join(lines)


def render_markdown(validated_payload: Dict[str, Any]) -> str:
    kind = validated_payload["kind"]
    renderer = {
        "project_summary": render_project_summary,
        "source_index": render_source_index,
        "sink_index": render_sink_index,
        "defense_catalog": render_defense_catalog,
        "progress": render_progress,
        "findings": render_findings,
        "interaction_matrix": render_interaction_matrix,
    }[kind]
    return renderer(validated_payload)


def write_markdown_atomic(path: str, content: str) -> None:
    dir_path = os.path.dirname(path) or "."
    os.makedirs(dir_path, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", suffix=".md", dir=dir_path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write structured code-audit markdown docs from JSON payloads")
    parser.add_argument("--kind", choices=sorted(KIND_TO_FILENAME.keys()), required=True, help="Document kind")
    parser.add_argument("--input-json", required=True, help="Path to JSON payload file")
    parser.add_argument("--output-dir", default="./out", help="Output directory (default: ./out)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        with open(args.input_json, "r", encoding="utf-8") as f:
            payload = json.load(f)
        validated = validate_payload(args.kind, payload)
        markdown = render_markdown(validated)
        output_path = os.path.join(args.output_dir, KIND_TO_FILENAME[args.kind])
        write_markdown_atomic(output_path, markdown)
        print(f"Wrote {args.kind} to {output_path}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: file not found: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {args.input_json}: {e}", file=sys.stderr)
        return 1
    except ValidationError as e:
        print(f"Error: payload validation failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: unexpected failure: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
