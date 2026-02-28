# 权限模型提取 (authz_model)

- 生成时间: 2026-02-28T16:06:20+08:00
- 参数: `{"repo_root": "/Users/xuziqiang/Workspace/my-skills/taint-analysis", "output_dir": "/Users/xuziqiang/Workspace/my-skills/taint-analysis/out", "focus_paths": ["<repo-root>"], "kinds": ["cmd", "path", "query", "template", "ssrf", "deser", "memory", "authz"], "depth": 2, "budget": 200, "cache": true}`
- 扫描范围: <repo-root>
- 局限说明: 关键词扫描不等价于有效授权校验，需人工核验权限绑定与作用域传播。

- 扫描文件数: 3
- 命中数: 12
- 关键词频次: {'auth': 3, 'permission': 3, 'permit': 3, 'owner': 4, 'tenant': 4, 'role': 3, 'policy': 3}

## 命中列表
- `scripts/run_taint_audit.py:98` | `re.compile(r"\b(if\s+.*(auth|authorize|permission|permit|role|tenant|owner|rbac|abac)|check\w*\(|require\w*\()", re.IGNORECASE),`
- `scripts/run_taint_audit.py:99` | `re.compile(r"\b(assert|deny|forbid|is_admin|is_owner|has_role|tenant_id)\b", re.IGNORECASE),`
- `scripts/run_taint_audit.py:103` | `re.compile(r"\b(auth|authorize|authorization|permission|permit|deny|rbac|abac|policy)\b", re.IGNORECASE),`
- `scripts/run_taint_audit.py:104` | `re.compile(r"\b(owner|tenant|tenant_id|org_id|account_id|scope|principal|subject)\b", re.IGNORECASE),`
- `scripts/run_taint_audit.py:558` | `for kw in ["auth", "permission", "permit", "owner", "tenant", "role", "policy"]:`
- `scripts/run_taint_audit.py:762` | `def header_block(title: str, params: dict, scope: Sequence[str], limitations: str) -> List[str]:`
- `scripts/run_taint_audit.py:768` | `f"- 扫描范围: {', '.join(scope) if scope else '<repo-root>'}",`
- `scripts/run_taint_audit.py:1035` | `lines.append("4. 对 Possible 项做定向人工复核，更新 taint policy 与误报抑制规则。")`
- `scripts/sink_scan.py:182` | `scope = [str(p.relative_to(repo_root)) if p.is_relative_to(repo_root) else str(p) for p in focus_paths] if focus_paths else ["<repo-root>"]`
- `scripts/sink_scan.py:190` | `lines.append(f"- 扫描范围: {', '.join(scope)}")`
- `scripts/entry_scan.py:178` | `scope = [str(p.relative_to(repo_root)) if p.is_relative_to(repo_root) else str(p) for p in focus_paths] if focus_paths else ["<repo-root>"]`
- `scripts/entry_scan.py:186` | `lines.append(f"- 扫描范围: {', '.join(scope)}")`
