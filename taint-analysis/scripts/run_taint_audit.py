#!/usr/bin/env python3
"""通用静态污点审计统一入口（默认只读）。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import traceback
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_KINDS = ["cmd", "path", "query", "template", "ssrf", "deser", "memory", "authz"]
IGNORE_DIRS = {
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

SINK_TO_KIND = {
    "exec": "cmd",
    "eval": "cmd",
    "template": "template",
    "sql": "query",
    "deser": "deser",
    "file_write": "path",
    "network": "ssrf",
    "memory": "memory",
    "dangerous_cfg": "authz",
}

SOURCE_PATTERNS = [
    ("http_input", re.compile(r"\b(request\.(args|form|json|get_json|query)|ctx\.(Query|PostForm|Bind|Param)|req\.(Query|Body|URL|Form)|params\[|query\[)")),
    ("rpc_input", re.compile(r"\b(request\s*\*?\w+Request|grpc\.|thrift|protobuf|rpc\.Call)")),
    ("mq_input", re.compile(r"\b(message|msg|payload|consumer|subscribe|consume|event)\b", re.IGNORECASE)),
    ("cli_input", re.compile(r"\b(argparse|sys\.argv|flag\.|cobra\.|click\.|process\.argv|CommandLine)")),
    ("env_input", re.compile(r"\b(getenv\s*\(|os\.environ|process\.env|dotenv|viper\.Get)")),
    ("file_input", re.compile(r"\b(read(File|_to_string)?|ReadFile|fs\.readFile|ioutil\.ReadFile|Path\.(read_text|read_bytes)|yaml\.load|json\.load|xml\.)")),
    ("deser_input", re.compile(r"\b(pickle\.loads|yaml\.load|ObjectInputStream|BinaryFormatter|gob\.NewDecoder)")),
]

SANITIZER_PATTERNS = [
    re.compile(r"\b(escape|sanitize|validate|clean|safe_\w+|quote|encodeURIComponent|html\.EscapeString|xss\.Escape)\b", re.IGNORECASE),
    re.compile(r"\b(realpath|normpath|filepath\.Clean|path\.normalize|canonicalize)\b", re.IGNORECASE),
    re.compile(r"\b(preparedStatement|parameterized|bindParam|QueryBuilder|allowlist|whitelist|regex)\b", re.IGNORECASE),
]

GUARD_PATTERNS = [
    re.compile(r"\b(if\s+.*(auth|authorize|permission|permit|role|tenant|owner|rbac|abac)|check\w*\(|require\w*\()", re.IGNORECASE),
    re.compile(r"\b(assert|deny|forbid|is_admin|is_owner|has_role|tenant_id)\b", re.IGNORECASE),
]

AUTHZ_PATTERNS = [
    re.compile(r"\b(auth|authorize|authorization|permission|permit|deny|rbac|abac|policy)\b", re.IGNORECASE),
    re.compile(r"\b(owner|tenant|tenant_id|org_id|account_id|scope|principal|subject)\b", re.IGNORECASE),
]

FUNC_DEF_PATTERNS = [
    re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
    re.compile(r"^\s*async\s+def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
    re.compile(r"^\s*func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
    re.compile(r"^\s*(?:public|private|protected|static|final|synchronized|inline|virtual|constexpr|unsafe|mut|async|export|internal|extern|\s)+\s*([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*\{"),
    re.compile(r"^\s*fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
]

CALL_PATTERNS = [
    re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\("),
]

KEYWORDS = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "return",
    "new",
    "def",
    "func",
    "fn",
    "class",
    "sizeof",
    "typeof",
    "else",
}


@dataclass
class Flow:
    flow_id: str
    kind: str
    severity: str
    sink: dict
    source: Optional[dict]
    function_stack: List[str]
    variable_chain: List[str]
    guards: List[str]
    sanitizers: List[str]
    evidence: List[dict]
    notes: List[str]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def parse_focus_paths(raw_values: Sequence[str] | None, repo_root: Path) -> List[Path]:
    if not raw_values:
        return []
    out: List[Path] = []
    seen: set[Path] = set()
    for raw in raw_values:
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            p = Path(part)
            if not p.is_absolute():
                p = (repo_root / p).resolve()
            else:
                p = p.resolve()
            if p.exists() and p not in seen:
                out.append(p)
                seen.add(p)
    return out


def is_ignored(path: Path, repo_root: Path) -> bool:
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return True
    for part in rel.parts:
        if part in IGNORE_DIRS:
            return True
    return False


def iter_source_files(repo_root: Path, focus_paths: Sequence[Path], budget: int | None = None) -> Iterable[Path]:
    roots = focus_paths if focus_paths else [repo_root]
    count = 0
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
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
            for filename in filenames:
                fpath = dpath / filename
                if fpath.suffix.lower() not in SOURCE_EXTS:
                    continue
                if is_ignored(fpath, repo_root):
                    continue
                yield fpath
                count += 1
                if budget and count >= budget:
                    return


def hash_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_file_state(repo_root: Path, files: Sequence[Path]) -> Dict[str, dict]:
    state: Dict[str, dict] = {}
    for path in files:
        try:
            st = path.stat()
            rel = str(path.relative_to(repo_root))
            state[rel] = {
                "mtime": st.st_mtime,
                "size": st.st_size,
                "sha1": hash_file(path),
            }
        except OSError:
            continue
    return state


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cache(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return load_json(path)
    except Exception:
        return {}


def params_signature(args: argparse.Namespace, focus_paths: Sequence[Path], kinds: Sequence[str]) -> dict:
    return {
        "repo_root": str(Path(args.repo_root).resolve()),
        "focus_paths": [str(p) for p in focus_paths],
        "kinds": list(kinds),
        "depth": int(args.depth),
        "budget": int(args.budget) if args.budget else 0,
    }


def same_signature(a: dict, b: dict) -> bool:
    return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)


def run_child_script(script: Path, argv: List[str], verbose: bool = False) -> None:
    cmd = [sys.executable, str(script)] + argv
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if verbose and proc.stdout.strip():
        print(proc.stdout)
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or proc.stdout.strip() or "未知错误"
        raise RuntimeError(f"执行脚本失败: {' '.join(cmd)}\n{stderr}")


def parse_entries_or_sinks(payload: dict) -> List[dict]:
    hits: List[dict] = []
    for cat in payload.get("categories", []):
        for item in cat.get("hits", []):
            merged = dict(item)
            merged.setdefault("category", cat.get("id", "unknown"))
            merged.setdefault("title", cat.get("title", merged.get("category", "unknown")))
            if "severity" in cat and "severity" not in merged:
                merged["severity"] = cat["severity"]
            hits.append(merged)
    return hits


def read_file_lines(repo_root: Path, rel_path: str) -> List[str]:
    try:
        return (repo_root / rel_path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []


def enclosing_function(lines: Sequence[str], line_no: int) -> str:
    idx = min(max(line_no - 1, 0), max(len(lines) - 1, 0))
    for i in range(idx, -1, -1):
        line = lines[i]
        for pat in FUNC_DEF_PATTERNS:
            m = pat.search(line)
            if m:
                return m.group(1)
    return "<global>"


def extract_identifiers(text: str) -> List[str]:
    ids = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", text)
    return [x for x in ids if x not in KEYWORDS and len(x) > 2]


def nearby_lines(lines: Sequence[str], center: int, radius: int = 6) -> List[Tuple[int, str]]:
    out: List[Tuple[int, str]] = []
    start = max(1, center - radius)
    end = min(len(lines), center + radius)
    for i in range(start, end + 1):
        out.append((i, lines[i - 1]))
    return out


def find_nearby_sources(entries: Sequence[dict], rel_file: str, sink_line: int, depth: int) -> List[dict]:
    window = max(80, 80 * depth)
    same_file = [e for e in entries if e.get("file") == rel_file]
    scored = []
    for e in same_file:
        dist = abs(int(e.get("line", 0)) - sink_line)
        if dist <= window:
            scored.append((dist, e))
    scored.sort(key=lambda x: x[0])
    return [e for _, e in scored[:5]]


def index_functions(repo_root: Path, files: Sequence[Path]) -> Tuple[Dict[str, List[dict]], Dict[str, List[dict]]]:
    defs: Dict[str, List[dict]] = defaultdict(list)
    calls: Dict[str, List[dict]] = defaultdict(list)
    for fpath in files:
        rel = str(fpath.relative_to(repo_root))
        lines = read_file_lines(repo_root, rel)
        for lineno, line in enumerate(lines, start=1):
            for pat in FUNC_DEF_PATTERNS:
                m = pat.search(line)
                if m:
                    defs[m.group(1)].append({"file": rel, "line": lineno})
                    break
            for pat in CALL_PATTERNS:
                for m in pat.finditer(line):
                    name = m.group(1)
                    if name in KEYWORDS:
                        continue
                    calls[name].append({"file": rel, "line": lineno, "snippet": line.strip()[:180]})
    return defs, calls


def find_callers(func_name: str, calls_index: Dict[str, List[dict]], max_items: int = 3) -> List[dict]:
    return calls_index.get(func_name, [])[:max_items]


def collect_sanitizers_and_guards(lines: Sequence[str], line_no: int) -> Tuple[List[str], List[str]]:
    sanitizers: List[str] = []
    guards: List[str] = []
    for ln, line in nearby_lines(lines, line_no, radius=8):
        for p in SANITIZER_PATTERNS:
            if p.search(line):
                sanitizers.append(f"L{ln}: {line.strip()[:140]}")
                break
        for p in GUARD_PATTERNS:
            if p.search(line):
                guards.append(f"L{ln}: {line.strip()[:140]}")
                break
    return sanitizers, guards


def kind_from_sink(sink: dict) -> str:
    return SINK_TO_KIND.get(sink.get("category", ""), "unknown")


def gen_flow_id(prefix: str, idx: int) -> str:
    return f"{prefix}-{idx:04d}"


def build_backward_flows(
    repo_root: Path,
    sinks: Sequence[dict],
    entries: Sequence[dict],
    defs_index: Dict[str, List[dict]],
    calls_index: Dict[str, List[dict]],
    depth: int,
    kinds: Sequence[str],
) -> List[Flow]:
    prioritized = sorted(sinks, key=lambda s: (0 if s.get("severity") == "high" else 1, str(s.get("file", "")), int(s.get("line", 0))))
    flows: List[Flow] = []
    for i, sink in enumerate(prioritized, start=1):
        kind = kind_from_sink(sink)
        if kind not in kinds:
            continue
        rel = sink.get("file", "")
        line_no = int(sink.get("line", 0))
        lines = read_file_lines(repo_root, rel)
        if not lines:
            continue

        near_sources = find_nearby_sources(entries, rel, line_no, depth)
        source = near_sources[0] if near_sources else (entries[0] if entries else None)

        sink_line = lines[line_no - 1].strip() if 0 < line_no <= len(lines) else ""
        sink_func = enclosing_function(lines, line_no)

        function_stack = [f"{rel}:{sink_func}:{line_no}"]
        callers = find_callers(sink_func, calls_index, max_items=max(1, depth))
        for c in callers:
            function_stack.append(f"{c['file']}:<callsite>:{c['line']}")

        variable_chain: List[str] = []
        if source:
            source_line = read_file_lines(repo_root, source.get("file", ""))
            src_line_no = int(source.get("line", 0))
            src_text = source_line[src_line_no - 1] if source_line and 0 < src_line_no <= len(source_line) else source.get("snippet", "")
        else:
            src_text = ""
        src_ids = set(extract_identifiers(src_text))
        sink_ids = set(extract_identifiers(sink_line or sink.get("snippet", "")))
        overlap = [x for x in src_ids.intersection(sink_ids)]
        if overlap:
            variable_chain.extend(overlap[:6])
        else:
            variable_chain.extend(list(sink_ids)[:4])

        sanitizers, guards = collect_sanitizers_and_guards(lines, line_no)

        evidence = [
            {
                "role": "sink",
                "file": rel,
                "line": line_no,
                "snippet": sink_line or sink.get("snippet", ""),
            }
        ]
        if source:
            evidence.append(
                {
                    "role": "source",
                    "file": source.get("file", ""),
                    "line": int(source.get("line", 0)),
                    "snippet": source.get("snippet", ""),
                }
            )

        for c in callers:
            evidence.append(
                {
                    "role": "call",
                    "file": c["file"],
                    "line": c["line"],
                    "snippet": c.get("snippet", ""),
                }
            )

        notes = []
        if not near_sources:
            notes.append("未在同文件邻域发现明确 source，当前 source 为全局近似候选。")
        if not callers:
            notes.append("未解析到明显调用者，函数栈证据以当前函数为主。")
        if sanitizers:
            notes.append("检测到疑似净化器，需人工确认净化是否覆盖到 sink 参数。")
        if guards:
            notes.append("检测到 guard/authz 分支，需确认是否对当前路径生效。")

        flows.append(
            Flow(
                flow_id=gen_flow_id("BWD", i),
                kind=kind,
                severity=sink.get("severity", "medium"),
                sink=sink,
                source=source,
                function_stack=function_stack,
                variable_chain=variable_chain,
                guards=guards,
                sanitizers=sanitizers,
                evidence=evidence,
                notes=notes,
            )
        )
    return flows


def build_forward_flows(
    repo_root: Path,
    entries: Sequence[dict],
    sinks: Sequence[dict],
    depth: int,
    kinds: Sequence[str],
) -> List[dict]:
    sink_by_file: Dict[str, List[dict]] = defaultdict(list)
    for s in sinks:
        sink_by_file[s.get("file", "")].append(s)

    picked_by_category: Dict[str, dict] = {}
    for e in entries:
        cat = e.get("category", "unknown")
        if cat not in picked_by_category:
            picked_by_category[cat] = e

    flows = []
    idx = 1
    window = max(80, 120 * depth)
    risky_call = re.compile(r"\b(exec|system|query|render|deserialize|template|load|open|write|http|fetch|dial)\w*\s*\(", re.IGNORECASE)

    for source in picked_by_category.values():
        rel = source.get("file", "")
        line_no = int(source.get("line", 0))
        lines = read_file_lines(repo_root, rel)
        if not lines:
            continue

        start = line_no
        end = min(len(lines), line_no + window)
        local_sinks = [s for s in sink_by_file.get(rel, []) if start <= int(s.get("line", 0)) <= end and kind_from_sink(s) in kinds]

        unknown_calls = []
        for ln in range(start, end + 1):
            line = lines[ln - 1]
            if risky_call.search(line):
                unknown_calls.append({"file": rel, "line": ln, "snippet": line.strip()[:180]})

        flows.append(
            {
                "flow_id": gen_flow_id("FWD", idx),
                "source": source,
                "candidate_sinks": local_sinks[:8],
                "unknown_risky_calls": unknown_calls[:8],
                "notes": [
                    "正向追踪基于同文件窗口与风险调用关键词，主要用于补漏与发现未知 sink。",
                ],
            }
        )
        idx += 1
    return flows


def scan_authz_model(repo_root: Path, files: Sequence[Path], budget: int | None = None) -> dict:
    hits = []
    keyword_counter = Counter()
    scanned = 0
    for fpath in files:
        rel = str(fpath.relative_to(repo_root))
        lines = read_file_lines(repo_root, rel)
        for lineno, line in enumerate(lines, start=1):
            for p in AUTHZ_PATTERNS:
                if p.search(line):
                    hits.append({"file": rel, "line": lineno, "snippet": line.strip()[:180]})
                    for kw in ["auth", "permission", "permit", "owner", "tenant", "role", "policy"]:
                        if kw in line.lower():
                            keyword_counter[kw] += 1
                    break
        scanned += 1
        if budget and scanned >= budget:
            break
    model = {
        "generated_at": now_iso(),
        "hits": hits,
        "summary": {
            "files_scanned": scanned,
            "hits": len(hits),
            "keywords": keyword_counter,
        },
    }
    return model


def severity_rank(sev: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(sev, 4)


def normalize_severity(sink_sev: str, kind: str, score: int) -> str:
    if sink_sev == "high" and (kind in {"cmd", "memory", "deser"} and score >= 85):
        return "critical"
    if sink_sev == "high":
        return "high"
    if sink_sev == "medium":
        return "medium"
    return "low"


def status_from_score(score: int) -> str:
    if score >= 80:
        return "Confirmed"
    if score >= 60:
        return "Likely"
    return "Possible"


def calc_evidence_score(flow: Flow, forward_flows: Sequence[dict], authz_hits_by_file: Dict[str, List[dict]]) -> Tuple[int, List[str]]:
    score = 0
    reasoning = []
    if flow.severity == "high":
        score += 60
        reasoning.append("高危 sink 基础分 +60")
    else:
        score += 40
        reasoning.append("中危 sink 基础分 +40")

    if flow.source:
        score += 15
        reasoning.append("存在 source 候选 +15")
    else:
        reasoning.append("未定位明确 source +0")

    if flow.function_stack and len(flow.function_stack) > 1:
        score += 8
        reasoning.append("存在调用栈证据 +8")

    if flow.variable_chain:
        score += 7
        reasoning.append("变量链线索 +7")

    sink_file = flow.sink.get("file", "")
    sink_line = int(flow.sink.get("line", 0))

    corroborated = False
    for f in forward_flows:
        for s in f.get("candidate_sinks", []):
            if s.get("file") == sink_file and int(s.get("line", 0)) == sink_line:
                corroborated = True
                break
        if corroborated:
            break
    if corroborated:
        score += 10
        reasoning.append("正向追踪命中同一 sink +10")

    if flow.sanitizers:
        score -= min(20, 6 * len(flow.sanitizers))
        reasoning.append("检测到净化器，降低可利用性")

    if flow.guards:
        score -= min(20, 5 * len(flow.guards))
        reasoning.append("检测到 guard/authz，降低可利用性")

    authz_hits = authz_hits_by_file.get(sink_file, [])
    if not authz_hits:
        score += 8
        reasoning.append("sink 文件未见 authz 语义，越权风险加分 +8")

    score = max(0, min(100, score))
    return score, reasoning


def build_findings(flows: Sequence[Flow], forward_flows: Sequence[dict], authz_model: dict) -> List[dict]:
    authz_hits_by_file: Dict[str, List[dict]] = defaultdict(list)
    for hit in authz_model.get("hits", []):
        authz_hits_by_file[hit.get("file", "")].append(hit)

    findings = []
    dedup = set()
    idx = 1
    for flow in flows:
        sink_file = flow.sink.get("file", "")
        sink_line = int(flow.sink.get("line", 0))
        key = (sink_file, sink_line, flow.kind)
        if key in dedup:
            continue
        dedup.add(key)

        score, score_reasoning = calc_evidence_score(flow, forward_flows, authz_hits_by_file)
        status = status_from_score(score)
        severity = normalize_severity(flow.severity, flow.kind, score)

        source_loc = "未知"
        if flow.source:
            source_loc = f"{flow.source.get('file','?')}:{flow.source.get('line','?')}"

        sink_loc = f"{sink_file}:{sink_line}"
        sink_title = flow.sink.get("title", flow.sink.get("category", "sink"))

        finding = {
            "id": f"F-{idx:03d}",
            "title": f"{sink_title} 潜在污点传播 ({flow.kind})",
            "severity": severity,
            "status": status,
            "evidence_score": score,
            "source": source_loc,
            "sink": sink_loc,
            "kind": flow.kind,
            "impact": "未经充分净化与权限绑定的数据可进入敏感操作，可能导致命令执行、越权、数据破坏或泄露。",
            "path": {
                "function_stack": flow.function_stack,
                "variable_chain": flow.variable_chain,
            },
            "guards": flow.guards,
            "sanitizers": flow.sanitizers,
            "evidence": flow.evidence,
            "score_reasoning": score_reasoning,
            "notes": flow.notes,
            "exploitability": "静态可利用性判定：需结合运行时参数控制度、认证上下文与净化器有效性进行最终确认。",
            "authz_gap_hint": "可能缺少权限/租户绑定" if not authz_hits_by_file.get(sink_file) else "检测到部分 authz 语义，需核验是否覆盖当前路径",
            "fix_hint": "优先采用白名单校验、参数化接口、上下文权限绑定与输出编码；为关键路径补充单测/安全回归测试。",
        }
        findings.append(finding)
        idx += 1

    findings.sort(key=lambda x: (severity_rank(x["severity"]), -x["evidence_score"], x["id"]))
    return findings


def build_attack_chains(findings: Sequence[dict]) -> List[dict]:
    by_kind: Dict[str, List[dict]] = defaultdict(list)
    for f in findings:
        by_kind[f.get("kind", "unknown")].append(f)

    chains = []
    cid = 1

    if by_kind.get("path") and (by_kind.get("cmd") or by_kind.get("deser") or by_kind.get("template")):
        chains.append(
            {
                "id": f"CHAIN-{cid:02d}",
                "name": "写文件 -> 加载/执行",
                "preconditions": ["攻击者可控文件名或内容", "目标存在后续加载/执行路径"],
                "steps": [
                    "利用 path 类问题写入可控内容或篡改关键文件",
                    "触发 cmd/deser/template 路径实现执行或扩展控制",
                ],
                "impact": "可能导致持久化控制、远程代码执行或供应链污染。",
            }
        )
        cid += 1

    high_authz = [f for f in findings if f.get("authz_gap_hint", "").startswith("可能缺少") and f.get("severity") in {"critical", "high"}]
    if high_authz:
        chains.append(
            {
                "id": f"CHAIN-{cid:02d}",
                "name": "越权 -> 高危 sink",
                "preconditions": ["权限绑定缺失或租户校验不完整", "攻击者可访问入口接口"],
                "steps": ["绕过/缺失鉴权进入业务入口", "调用高危 sink 完成越权操作"],
                "impact": "跨租户访问、敏感操作越权、核心数据破坏。",
            }
        )
        cid += 1

    if by_kind.get("ssrf") and (by_kind.get("authz") or by_kind.get("cmd")):
        chains.append(
            {
                "id": f"CHAIN-{cid:02d}",
                "name": "信息探测/外联 -> 校验绕过",
                "preconditions": ["可控外联地址或请求目标", "内部网络/元数据服务可达"],
                "steps": ["通过 ssrf 风险探测内部资产", "结合配置缺陷或命令路径扩大影响"],
                "impact": "内部信息泄露、访问控制绕过与横向利用。",
            }
        )

    return chains


def header_block(title: str, params: dict, scope: Sequence[str], limitations: str) -> List[str]:
    return [
        f"# {title}",
        "",
        f"- 生成时间: {now_iso()}",
        f"- 参数: `{json.dumps(params, ensure_ascii=False)}`",
        f"- 扫描范围: {', '.join(scope) if scope else '<repo-root>'}",
        f"- 局限说明: {limitations}",
        "",
    ]


def render_taint_policy_md(params: dict, kinds: Sequence[str], entries: Sequence[dict], sinks: Sequence[dict], discovered_sanitizers: Sequence[str]) -> str:
    source_groups = defaultdict(list)
    for e in entries[:120]:
        source_groups[e.get("title", e.get("category", "source"))].append(f"{e.get('file')}:{e.get('line')}")

    sink_groups = defaultdict(list)
    for s in sinks[:200]:
        k = kind_from_sink(s)
        if k in kinds:
            sink_groups[s.get("title", s.get("category", "sink"))].append(f"{s.get('file')}:{s.get('line')}")

    lines = header_block(
        "污点策略草案 (taint_policy)",
        params,
        params.get("focus_paths", []),
        "策略由启发式自动生成，需结合业务语义与代码审阅人工修订。",
    )
    lines.append("## TaintKinds")
    lines.append(f"- 启用类型: {', '.join(kinds)}")
    lines.append("")

    lines.append("## Sources")
    if not source_groups:
        lines.append("- 未自动识别到明确 Source，请人工补充入口与不可信来源。")
    else:
        for k, v in source_groups.items():
            lines.append(f"- {k}: {', '.join(v[:8])}")
    lines.append("")

    lines.append("## Sinks")
    if not sink_groups:
        lines.append("- 未命中已启用 kinds 的 sink。")
    else:
        for k, v in sink_groups.items():
            lines.append(f"- {k}: {', '.join(v[:10])}")
    lines.append("")

    lines.append("## Sanitizers (候选)")
    if discovered_sanitizers:
        for item in discovered_sanitizers:
            lines.append(f"- {item}")
    else:
        lines.append("- 未发现明显净化器调用；不代表不存在。")
    lines.append("")

    lines.append("## TrustBoundaries")
    lines.append("- 外部请求 -> 应用入口 (HTTP/RPC/MQ/CLI)")
    lines.append("- 应用内部 -> 文件系统/数据库/模板引擎/命令执行")
    lines.append("- 跨租户/跨权限域调用边界")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_backward_md(params: dict, flows: Sequence[Flow]) -> str:
    lines = header_block(
        "反向数据流追踪 (flows_backward)",
        params,
        params.get("focus_paths", []),
        "反向追踪优先高危 sink，采用调用点近似与邻域 source 搜索，不是完整 SSA。",
    )
    lines.append(f"- 流数量: {len(flows)}")
    lines.append("")

    for flow in flows:
        sink = flow.sink
        lines.append(f"## {flow.flow_id} | {flow.kind} | {sink.get('file')}:{sink.get('line')}")
        lines.append(f"- Sink: `{sink.get('title', sink.get('category'))}` | `{sink.get('snippet', '')}`")
        if flow.source:
            lines.append(f"- Source: `{flow.source.get('file')}:{flow.source.get('line')}` | `{flow.source.get('snippet', '')}`")
        else:
            lines.append("- Source: 未定位")
        lines.append(f"- 函数栈: {' -> '.join(flow.function_stack) if flow.function_stack else '<none>'}")
        lines.append(f"- 变量链: {', '.join(flow.variable_chain) if flow.variable_chain else '<none>'}")
        lines.append(f"- Guard: {', '.join(flow.guards) if flow.guards else '<none>'}")
        lines.append(f"- Sanitizer: {', '.join(flow.sanitizers) if flow.sanitizers else '<none>'}")
        if flow.notes:
            lines.append("- 备注:")
            for n in flow.notes:
                lines.append(f"  - {n}")
        lines.append("- 证据片段:")
        for ev in flow.evidence[:8]:
            lines.append(f"  - [{ev.get('role')}] `{ev.get('file')}:{ev.get('line')}` | `{ev.get('snippet', '')}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_forward_md(params: dict, flows: Sequence[dict]) -> str:
    lines = header_block(
        "正向数据流追踪 (flows_forward)",
        params,
        params.get("focus_paths", []),
        "正向追踪用于补漏与发现未知 sink，覆盖同文件窗口与风险调用关键词。",
    )
    lines.append(f"- 流数量: {len(flows)}")
    lines.append("")
    for f in flows:
        src = f.get("source", {})
        lines.append(f"## {f.get('flow_id')} | Source `{src.get('file')}:{src.get('line')}`")
        lines.append(f"- Source 片段: `{src.get('snippet', '')}`")
        sinks = f.get("candidate_sinks", [])
        lines.append(f"- 命中候选 sinks: {len(sinks)}")
        for s in sinks[:6]:
            lines.append(f"  - `{s.get('file')}:{s.get('line')}` | `{s.get('title', s.get('category'))}` | `{s.get('snippet', '')}`")
        unknown = f.get("unknown_risky_calls", [])
        lines.append(f"- 未知风险调用: {len(unknown)}")
        for u in unknown[:6]:
            lines.append(f"  - `{u.get('file')}:{u.get('line')}` | `{u.get('snippet', '')}`")
        for note in f.get("notes", []):
            lines.append(f"- 备注: {note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_authz_md(params: dict, model: dict) -> str:
    lines = header_block(
        "权限模型提取 (authz_model)",
        params,
        params.get("focus_paths", []),
        "关键词扫描不等价于有效授权校验，需人工核验权限绑定与作用域传播。",
    )
    summary = model.get("summary", {})
    lines.append(f"- 扫描文件数: {summary.get('files_scanned', 0)}")
    lines.append(f"- 命中数: {summary.get('hits', 0)}")
    lines.append(f"- 关键词频次: {dict(summary.get('keywords', {}))}")
    lines.append("")
    lines.append("## 命中列表")
    hits = model.get("hits", [])
    if not hits:
        lines.append("- 无命中")
    else:
        for h in hits[:200]:
            lines.append(f"- `{h.get('file')}:{h.get('line')}` | `{h.get('snippet', '')}`")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_findings_md(params: dict, findings: Sequence[dict]) -> str:
    lines = header_block(
        "漏洞发现清单 (findings)",
        params,
        params.get("focus_paths", []),
        "证据评分为静态估算，Confirmed 仍需结合运行时验证与业务上下文确认。",
    )
    sev_counter = Counter([f["severity"] for f in findings])
    status_counter = Counter([f["status"] for f in findings])
    lines.append(f"- 总发现数: {len(findings)}")
    lines.append(f"- 严重性分布: {dict(sev_counter)}")
    lines.append(f"- 状态分布: {dict(status_counter)}")
    lines.append("")

    for f in findings:
        lines.append(f"## {f['id']} | {f['severity']} | {f['status']} | score={f['evidence_score']}")
        lines.append(f"- 标题: {f['title']}")
        lines.append(f"- 影响: {f['impact']}")
        lines.append(f"- Source: `{f['source']}`")
        lines.append(f"- Sink: `{f['sink']}`")
        lines.append(f"- 函数栈: {' -> '.join(f['path']['function_stack']) if f['path']['function_stack'] else '<none>'}")
        lines.append(f"- 变量链: {', '.join(f['path']['variable_chain']) if f['path']['variable_chain'] else '<none>'}")
        lines.append(f"- Guard: {', '.join(f.get('guards', [])) if f.get('guards') else '<none>'}")
        lines.append(f"- Sanitizer: {', '.join(f.get('sanitizers', [])) if f.get('sanitizers') else '<none>'}")
        lines.append(f"- 权限绑定提示: {f['authz_gap_hint']}")
        lines.append(f"- 静态可利用性: {f['exploitability']}")
        lines.append(f"- 修复建议: {f['fix_hint']}")
        lines.append("- 评分依据:")
        for r in f.get("score_reasoning", []):
            lines.append(f"  - {r}")
        lines.append("- 证据链:")
        for ev in f.get("evidence", [])[:10]:
            lines.append(f"  - [{ev.get('role')}] `{ev.get('file')}:{ev.get('line')}` | `{ev.get('snippet', '')}`")
        if f.get("notes"):
            lines.append("- 备注:")
            for n in f["notes"]:
                lines.append(f"  - {n}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_attack_chains_md(params: dict, chains: Sequence[dict]) -> str:
    lines = header_block(
        "攻击链组合 (attack_chains)",
        params,
        params.get("focus_paths", []),
        "攻击链为静态组合推演，不代表真实环境可直接利用。",
    )
    lines.append(f"- 攻击链数量: {len(chains)}")
    lines.append("")
    if not chains:
        lines.append("- 当前未组合出高可信攻击链。")
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    for c in chains:
        lines.append(f"## {c['id']} | {c['name']}")
        lines.append("- 前置条件:")
        for p in c.get("preconditions", []):
            lines.append(f"  - {p}")
        lines.append("- 步骤:")
        for s in c.get("steps", []):
            lines.append(f"  - {s}")
        lines.append(f"- 影响面: {c.get('impact', '')}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_report_md(params: dict, findings: Sequence[dict], chains: Sequence[dict], profile: dict) -> str:
    lines = header_block(
        "静态污点审计报告 (report)",
        params,
        params.get("focus_paths", []),
        "本报告基于离线静态启发式分析，建议将高风险项纳入代码复核与测试验证。",
    )
    sev_counter = Counter([f["severity"] for f in findings])
    status_counter = Counter([f["status"] for f in findings])
    high_confirmed = [f for f in findings if f["status"] == "Confirmed" and f["severity"] in {"critical", "high"}]

    lines.append("## 摘要")
    lines.append(f"- 总发现: {len(findings)}")
    lines.append(f"- 严重性分布: {dict(sev_counter)}")
    lines.append(f"- 状态分布: {dict(status_counter)}")
    lines.append(f"- 高危 Confirmed: {len(high_confirmed)}")
    lines.append("")

    lines.append("## 方法与范围")
    lines.append("- Phase0: 工程画像、函数索引、近似调用图")
    lines.append("- Phase1: 入口面与 sink 面静态扫描")
    lines.append("- Phase2: 高危 sink 反向追踪、路径敏感与净化器检查")
    lines.append("- Phase2.5: 代表 source 正向补漏")
    lines.append("- Phase3: authz 语义提取与越权提示")
    lines.append("- Phase3.5: 交叉验证、去重与证据评分")
    lines.append("- Phase4: 攻击链规则组合")
    lines.append("- Phase5: 结构化报告生成")
    lines.append(f"- 扫描文件数: {profile.get('file_count', 0)}")
    lines.append(f"- 语言分布: {profile.get('languages', {})}")
    lines.append("")

    lines.append("## 发现列表（Top）")
    if not findings:
        lines.append("- 无发现")
    else:
        for f in findings[:20]:
            lines.append(
                f"- {f['id']} | {f['severity']} | {f['status']} | score={f['evidence_score']} | {f['title']} | {f['sink']}"
            )
    lines.append("")

    lines.append("## 攻击链")
    if not chains:
        lines.append("- 未形成高置信攻击链")
    else:
        for c in chains:
            lines.append(f"- {c['id']} | {c['name']} | 影响: {c.get('impact', '')}")
    lines.append("")

    lines.append("## 修复路线图")
    lines.append("1. 先修复 critical/high 且 Confirmed/Likely 的命令执行、反序列化、越权链路。")
    lines.append("2. 为高风险 sink 引入统一输入校验、参数化接口与显式权限绑定。")
    lines.append("3. 将本次 finding 转化为单元测试/集成测试，建立回归基线。")
    lines.append("4. 对 Possible 项做定向人工复核，更新 taint policy 与误报抑制规则。")
    lines.append("")

    lines.append("## 假设与局限")
    lines.append("- 假设代码仓库可代表主要执行路径，未动态加载的外部插件默认不可见。")
    lines.append("- 局限: 近似调用图与正则模式可能漏报动态分发、反射、宏展开、多态序列化路径。")
    lines.append("- 局限: 未执行真实请求与运行时探针，证据链以静态可复核为目标。")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def profile_project(repo_root: Path, files: Sequence[Path]) -> dict:
    lang_counter = Counter()
    for f in files:
        lang_counter[f.suffix.lower() or "<none>"] += 1
    return {
        "file_count": len(files),
        "languages": dict(lang_counter.most_common(12)),
    }


def discover_sanitizers(repo_root: Path, files: Sequence[Path], limit: int = 80) -> List[str]:
    out: List[str] = []
    for fpath in files:
        rel = str(fpath.relative_to(repo_root))
        lines = read_file_lines(repo_root, rel)
        for lineno, line in enumerate(lines, start=1):
            for p in SANITIZER_PATTERNS:
                if p.search(line):
                    out.append(f"{rel}:{lineno} | {line.strip()[:150]}")
                    break
            if len(out) >= limit:
                return out
    return out


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="通用静态污点审计统一入口")
    parser.add_argument("--repo-root", default=".", help="仓库根目录，默认当前目录")
    parser.add_argument("--output-dir", default="./out", help="输出目录，默认 ./out")
    parser.add_argument("--focus-path", action="append", default=[], help="可重复，支持逗号分隔")
    parser.add_argument(
        "--kinds",
        default=",".join(DEFAULT_KINDS),
        help="污点类型，逗号分隔。默认 cmd,path,query,template,ssrf,deser,memory,authz",
    )
    parser.add_argument("--depth", type=int, default=3, help="追踪深度，默认 3")
    parser.add_argument("--budget", type=int, default=0, help="扫描文件预算上限，0 表示不限制")
    parser.add_argument("--no-cache", action="store_true", help="禁用增量缓存")
    parser.add_argument("--verbose", action="store_true", help="输出详细日志")
    return parser.parse_args()


def log(msg: str, verbose: bool) -> None:
    if verbose:
        print(f"[taint-audit] {msg}")


def main() -> int:
    args = parse_args()
    try:
        repo_root = Path(args.repo_root).resolve()
        output_dir = Path(args.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        focus_paths = parse_focus_paths(args.focus_path, repo_root)
        kinds = [k.strip() for k in args.kinds.split(",") if k.strip()]
        depth = max(1, int(args.depth))
        budget = int(args.budget) if args.budget and int(args.budget) > 0 else None

        files = list(iter_source_files(repo_root, focus_paths, budget))
        profile = profile_project(repo_root, files)

        params = {
            "repo_root": str(repo_root),
            "output_dir": str(output_dir),
            "focus_paths": [str(p.relative_to(repo_root)) if p.is_relative_to(repo_root) else str(p) for p in focus_paths] if focus_paths else ["<repo-root>"],
            "kinds": kinds,
            "depth": depth,
            "budget": budget or 0,
            "cache": not args.no_cache,
        }

        cache_path = output_dir / "cache.json"
        curr_sig = params_signature(args, focus_paths, kinds)
        curr_state = build_file_state(repo_root, files)
        cache = {} if args.no_cache else load_cache(cache_path)
        cache_ok = bool(cache) and same_signature(cache.get("params_signature", {}), curr_sig) and cache.get("file_state", {}) == curr_state

        # Phase 0
        log("Phase0: 工程理解与准备", args.verbose)

        if cache_ok:
            log("命中增量缓存，复用上次中间产物", args.verbose)
            artifacts = cache.get("artifacts", {})
            entries_data = artifacts.get("entries_data", {})
            sinks_data = artifacts.get("sinks_data", {})
            backward_flows = [Flow(**f) for f in artifacts.get("backward_flows", [])]
            forward_flows = artifacts.get("forward_flows", [])
            authz_model = artifacts.get("authz_model", {})
            findings = artifacts.get("findings", [])
            attack_chains = artifacts.get("attack_chains", [])
            taint_policy_text = artifacts.get("taint_policy_text", "")
            entries_md_text = artifacts.get("entries_md_text", "")
            sinks_md_text = artifacts.get("sinks_md_text", "")
            flows_backward_text = artifacts.get("flows_backward_text", "")
            flows_forward_text = artifacts.get("flows_forward_text", "")
            authz_model_text = artifacts.get("authz_model_text", "")
            findings_text = artifacts.get("findings_text", "")
            chains_text = artifacts.get("chains_text", "")
            report_text = artifacts.get("report_text", "")

            write_text(output_dir / "entries.md", entries_md_text)
            write_text(output_dir / "sinks.md", sinks_md_text)
            write_text(output_dir / "taint_policy.md", taint_policy_text)
            write_text(output_dir / "flows_backward.md", flows_backward_text)
            write_text(output_dir / "flows_forward.md", flows_forward_text)
            write_text(output_dir / "authz_model.md", authz_model_text)
            write_text(output_dir / "findings.md", findings_text)
            write_text(output_dir / "attack_chains.md", chains_text)
            write_text(output_dir / "report.md", report_text)

            high_confirmed = [f for f in findings if f.get("status") == "Confirmed" and f.get("severity") in {"critical", "high"}]
            return 2 if high_confirmed else 0

        # Phase 1
        log("Phase1: 入口面与 sink 扫描", args.verbose)
        scripts_dir = Path(__file__).resolve().parent
        entry_script = scripts_dir / "entry_scan.py"
        sink_script = scripts_dir / "sink_scan.py"

        entries_md = output_dir / "entries.md"
        entries_json = output_dir / "entries.json"
        sinks_md = output_dir / "sinks.md"
        sinks_json = output_dir / "sinks.json"

        entry_argv = ["--repo-root", str(repo_root), "--output", str(entries_md), "--json-out", str(entries_json)]
        sink_argv = ["--repo-root", str(repo_root), "--output", str(sinks_md), "--json-out", str(sinks_json)]
        for fp in args.focus_path:
            entry_argv.extend(["--focus-path", fp])
            sink_argv.extend(["--focus-path", fp])
        if budget:
            entry_argv.extend(["--budget", str(budget)])
            sink_argv.extend(["--budget", str(budget)])
        if args.verbose:
            entry_argv.append("--verbose")
            sink_argv.append("--verbose")

        run_child_script(entry_script, entry_argv, verbose=args.verbose)
        run_child_script(sink_script, sink_argv, verbose=args.verbose)

        entries_data = load_json(entries_json)
        sinks_data = load_json(sinks_json)
        entry_hits = parse_entries_or_sinks(entries_data)
        sink_hits = parse_entries_or_sinks(sinks_data)

        # Phase 2
        log("Phase2: 污点策略建模与反向追踪", args.verbose)
        discovered_sanitizers = discover_sanitizers(repo_root, files)
        taint_policy_text = render_taint_policy_md(params, kinds, entry_hits, sink_hits, discovered_sanitizers)
        write_text(output_dir / "taint_policy.md", taint_policy_text)

        defs_index, calls_index = index_functions(repo_root, files)
        backward_flows = build_backward_flows(repo_root, sink_hits, entry_hits, defs_index, calls_index, depth, kinds)
        flows_backward_text = render_backward_md(params, backward_flows)
        write_text(output_dir / "flows_backward.md", flows_backward_text)

        # Phase 2.5
        log("Phase2.5: 正向追踪补漏", args.verbose)
        forward_flows = build_forward_flows(repo_root, entry_hits, sink_hits, depth, kinds)
        flows_forward_text = render_forward_md(params, forward_flows)
        write_text(output_dir / "flows_forward.md", flows_forward_text)

        # Phase 3
        log("Phase3: 业务逻辑/越权审计", args.verbose)
        authz_model = scan_authz_model(repo_root, files, budget=budget)
        authz_model_text = render_authz_md(params, authz_model)
        write_text(output_dir / "authz_model.md", authz_model_text)

        # Phase 3.5
        log("Phase3.5: 交叉验证与评分", args.verbose)
        findings = build_findings(backward_flows, forward_flows, authz_model)
        findings_text = render_findings_md(params, findings)
        write_text(output_dir / "findings.md", findings_text)

        # Phase 4
        log("Phase4: 攻击链组合", args.verbose)
        attack_chains = build_attack_chains(findings)
        chains_text = render_attack_chains_md(params, attack_chains)
        write_text(output_dir / "attack_chains.md", chains_text)

        # Phase 5
        log("Phase5: 报告生成", args.verbose)
        report_text = render_report_md(params, findings, attack_chains, profile)
        write_text(output_dir / "report.md", report_text)

        if not args.no_cache:
            cache_payload = {
                "version": 1,
                "generated_at": now_iso(),
                "params_signature": curr_sig,
                "file_state": curr_state,
                "artifacts": {
                    "entries_data": entries_data,
                    "sinks_data": sinks_data,
                    "backward_flows": [f.__dict__ for f in backward_flows],
                    "forward_flows": forward_flows,
                    "authz_model": authz_model,
                    "findings": findings,
                    "attack_chains": attack_chains,
                    "entries_md_text": entries_md.read_text(encoding="utf-8") if entries_md.exists() else "",
                    "sinks_md_text": sinks_md.read_text(encoding="utf-8") if sinks_md.exists() else "",
                    "taint_policy_text": taint_policy_text,
                    "flows_backward_text": flows_backward_text,
                    "flows_forward_text": flows_forward_text,
                    "authz_model_text": authz_model_text,
                    "findings_text": findings_text,
                    "chains_text": chains_text,
                    "report_text": report_text,
                },
            }
            save_json(cache_path, cache_payload)

        high_confirmed = [f for f in findings if f["status"] == "Confirmed" and f["severity"] in {"critical", "high"}]
        return 2 if high_confirmed else 0

    except Exception as exc:
        err_path = Path(args.output_dir).resolve() / "runtime_error.log"
        err_path.parent.mkdir(parents=True, exist_ok=True)
        err_path.write_text(
            f"[{now_iso()}] run_taint_audit failed\n{exc}\n\n{traceback.format_exc()}",
            encoding="utf-8",
        )
        print(f"[taint-audit] 运行失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
