#!/usr/bin/env python3
"""敏感 sink 快速扫描（只读）。"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


DEFAULT_IGNORES = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "dist",
    "build",
    "target",
    "vendor",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "out",
    ".audit",
}

SOURCE_EXTS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".java",
    ".kt",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".scala",
    ".cs",
    ".sh",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".json",
    ".xml",
}


@dataclass
class Rule:
    category: str
    title: str
    severity: str
    regex: re.Pattern[str]


RULES: Sequence[Rule] = [
    Rule("exec", "命令执行 / 进程启动", "high", re.compile(r"\b(os\.system|popen\s*\(|subprocess\.(run|Popen|call)|execve?\s*\(|Runtime\.getRuntime\(\)\.exec|exec\.Command\s*\()")),
    Rule("eval", "动态执行 / eval", "high", re.compile(r"\b(eval\s*\(|exec\s*\(|new\s+Function\s*\(|vm\.runIn\w+\s*\(|ScriptEngineManager\b)")),
    Rule("template", "模板渲染", "medium", re.compile(r"\b(render_template_string|jinja2\.Template|Mustache\.render|handlebars\.compile|template\.Execute|Thymeleaf|freemarker)\b", re.IGNORECASE)),
    Rule("sql", "SQL 原生拼接/执行", "high", re.compile(r"\b(cursor\.execute|db\.query|db\.exec|sequelize\.query|createNativeQuery|Statement\.execute(Query)?|Raw\s*\()\b", re.IGNORECASE)),
    Rule("deser", "反序列化", "high", re.compile(r"\b(pickle\.loads|yaml\.load\s*\(|ObjectInputStream|BinaryFormatter|gob\.NewDecoder|serde_json::from_(str|slice)|jsonpickle\.decode)\b")),
    Rule("file_write", "文件写入/路径拼接", "medium", re.compile(r"\b(open\s*\([^\n]*[\"']w|fs\.writeFile|ioutil\.WriteFile|Files\.write|FileOutputStream|path\.join|os\.path\.join|filepath\.Join)\b", re.IGNORECASE)),
    Rule("network", "外联请求/网络发起", "medium", re.compile(r"\b(requests\.(get|post|put|delete)|httpx\.(get|post)|axios\.(get|post)|fetch\s*\(|http\.(Get|Post|Do)|urllib\.request\.|net\.Dial|grpc\.Dial)\b")),
    Rule("memory", "格式化与内存边界", "high", re.compile(r"\b(strcpy\s*\(|strcat\s*\(|sprintf\s*\(|vsprintf\s*\(|gets\s*\(|memcpy\s*\([^,]+,[^,]+,[^\)]+\)|unsafe\.Pointer)")),
    Rule("dangerous_cfg", "危险配置", "medium", re.compile(r"\b(verify\s*=\s*False|InsecureSkipVerify\s*:\s*true|allow_origins\s*=\s*\[?['\"]\*['\"]\]?|disable_auth|skip_auth|permitAll\s*\()", re.IGNORECASE)),
]


def parse_focus_paths(raw_values: Sequence[str] | None, repo_root: Path) -> List[Path]:
    if not raw_values:
        return []
    paths: List[Path] = []
    seen: set[Path] = set()
    for raw in raw_values:
        for item in raw.split(","):
            item = item.strip()
            if not item:
                continue
            p = Path(item)
            if not p.is_absolute():
                p = (repo_root / p).resolve()
            else:
                p = p.resolve()
            if p.exists() and p not in seen:
                paths.append(p)
                seen.add(p)
    return paths


def is_ignored(path: Path, repo_root: Path) -> bool:
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return True
    for part in rel.parts:
        if part in DEFAULT_IGNORES:
            return True
    return False


def iter_files(repo_root: Path, focus_paths: Sequence[Path], budget: int | None) -> Iterable[Path]:
    count = 0
    roots = focus_paths if focus_paths else [repo_root]
    for root in roots:
        if root.is_file():
            if root.suffix.lower() in SOURCE_EXTS and not is_ignored(root, repo_root):
                yield root
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dpath = Path(dirpath)
            if is_ignored(dpath, repo_root):
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if d not in DEFAULT_IGNORES]
            for filename in filenames:
                p = dpath / filename
                if p.suffix.lower() not in SOURCE_EXTS:
                    continue
                if is_ignored(p, repo_root):
                    continue
                yield p
                count += 1
                if budget and count >= budget:
                    return


def scan(repo_root: Path, files: Sequence[Path], verbose: bool = False) -> Dict[str, List[dict]]:
    results: Dict[str, List[dict]] = {rule.category: [] for rule in RULES}
    for fpath in files:
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(fpath.relative_to(repo_root))
        for lineno, line in enumerate(text.splitlines(), start=1):
            snippet = line.strip()
            if not snippet:
                continue
            for rule in RULES:
                if rule.regex.search(line):
                    results[rule.category].append(
                        {
                            "file": rel,
                            "line": lineno,
                            "snippet": snippet[:180],
                            "category": rule.category,
                            "title": rule.title,
                            "severity": rule.severity,
                        }
                    )
                    if verbose:
                        print(f"[sink][{rule.category}] {rel}:{lineno}")
                    break
    return results


def render_markdown(
    repo_root: Path,
    focus_paths: Sequence[Path],
    budget: int | None,
    scanned_files: int,
    hits: Dict[str, List[dict]],
) -> str:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    scope = [str(p.relative_to(repo_root)) if p.is_relative_to(repo_root) else str(p) for p in focus_paths] if focus_paths else ["<repo-root>"]
    total_hits = sum(len(v) for v in hits.values())

    lines: List[str] = []
    lines.append("# Sink 扫描结果 (sinks)")
    lines.append("")
    lines.append(f"- 生成时间: {now}")
    lines.append(f"- repo_root: `{repo_root}`")
    lines.append(f"- 扫描范围: {', '.join(scope)}")
    lines.append(f"- 扫描文件数: {scanned_files}")
    lines.append(f"- 文件预算: {budget if budget else '无上限'}")
    lines.append("- 局限说明: 命中表示“可疑 sink 位置”，需结合数据流、guard、净化器再判定是否可利用。")
    lines.append("")
    lines.append(f"- 命中总数: {total_hits}")
    lines.append("")

    for rule in RULES:
        section_hits = hits.get(rule.category, [])
        lines.append(f"## {rule.title} [{rule.severity}] ({len(section_hits)})")
        if not section_hits:
            lines.append("- 无命中")
            lines.append("")
            continue
        for item in section_hits:
            lines.append(f"- `{item['file']}:{item['line']}` | `{item['snippet']}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")
    parser.add_argument("--repo-root", default=".", help="仓库根目录，默认当前目录")
    parser.add_argument("--output", required=True, help="Markdown 输出路径")
    parser.add_argument("--json-out", default="", help="JSON 输出路径（可选）")
    parser.add_argument("--focus-path", action="append", default=[], help="可重复，或逗号分隔")
    parser.add_argument("--budget", type=int, default=0, help="扫描文件上限，0 表示不限制")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_path = Path(args.output).resolve()
    json_path = Path(args.json_out).resolve() if args.json_out else None
    budget = args.budget if args.budget and args.budget > 0 else None

    focus_paths = parse_focus_paths(args.focus_path, repo_root)
    files = list(iter_files(repo_root, focus_paths, budget))
    hits = scan(repo_root, files, verbose=args.verbose)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    md = render_markdown(repo_root, focus_paths, budget, len(files), hits)
    out_path.write_text(md, encoding="utf-8")

    if json_path:
        payload = {
            "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "repo_root": str(repo_root),
            "output": str(out_path),
            "scan_scope": [str(p) for p in focus_paths] if focus_paths else [str(repo_root)],
            "scanned_files": len(files),
            "budget": budget,
            "categories": [
                {
                    "id": rule.category,
                    "title": rule.title,
                    "severity": rule.severity,
                    "count": len(hits.get(rule.category, [])),
                    "hits": hits.get(rule.category, []),
                }
                for rule in RULES
            ],
            "total_hits": sum(len(v) for v in hits.values()),
            "limitations": "启发式关键词扫描，需结合上下文做真实性判定。",
        }
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
