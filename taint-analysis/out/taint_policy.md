# 污点策略草案 (taint_policy)

- 生成时间: 2026-02-28T16:06:20+08:00
- 参数: `{"repo_root": "/Users/xuziqiang/Workspace/my-skills/taint-analysis", "output_dir": "/Users/xuziqiang/Workspace/my-skills/taint-analysis/out", "focus_paths": ["<repo-root>"], "kinds": ["cmd", "path", "query", "template", "ssrf", "deser", "memory", "authz"], "depth": 2, "budget": 200, "cache": true}`
- 扫描范围: <repo-root>
- 局限说明: 策略由启发式自动生成，需结合业务语义与代码审阅人工修订。

## TaintKinds
- 启用类型: cmd, path, query, template, ssrf, deser, memory, authz

## Sources
- main 入口: scripts/run_taint_audit.py:1278, scripts/sink_scan.py:262, scripts/entry_scan.py:257
- RPC service 注册: scripts/run_taint_audit.py:83, scripts/entry_scan.py:75
- MQ consumer/callback: scripts/run_taint_audit.py:84, scripts/entry_scan.py:76
- CLI flag/参数入口: scripts/run_taint_audit.py:1078, scripts/sink_scan.py:213, scripts/entry_scan.py:77, scripts/entry_scan.py:209
- 环境变量/配置加载: scripts/run_taint_audit.py:86, scripts/entry_scan.py:78
- 文件解析入口: scripts/run_taint_audit.py:87, scripts/run_taint_audit.py:218, scripts/run_taint_audit.py:242, scripts/entry_scan.py:79

## Sinks
- 命令执行 / 进程启动: scripts/run_taint_audit.py:275
- 动态执行 / eval: scripts/sink_scan.py:75
- 模板渲染: scripts/sink_scan.py:76
- SQL 原生拼接/执行: scripts/sink_scan.py:77
- 反序列化: scripts/run_taint_audit.py:88, scripts/sink_scan.py:78
- 文件写入/路径拼接: scripts/sink_scan.py:79
- 危险配置: scripts/sink_scan.py:82

## Sanitizers (候选)
- scripts/run_taint_audit.py:92 | re.compile(r"\b(escape|sanitize|validate|clean|safe_\w+|quote|encodeURIComponent|html\.EscapeString|xss\.Escape)\b", re.IGNORECASE),
- scripts/run_taint_audit.py:93 | re.compile(r"\b(realpath|normpath|filepath\.Clean|path\.normalize|canonicalize)\b", re.IGNORECASE),
- scripts/run_taint_audit.py:94 | re.compile(r"\b(preparedStatement|parameterized|bindParam|QueryBuilder|allowlist|whitelist|regex)\b", re.IGNORECASE),
- scripts/sink_scan.py:70 | regex: re.Pattern[str]
- scripts/sink_scan.py:157 | if rule.regex.search(line):
- scripts/entry_scan.py:69 | regex: re.Pattern[str]
- scripts/entry_scan.py:154 | if rule.regex.search(line):

## TrustBoundaries
- 外部请求 -> 应用入口 (HTTP/RPC/MQ/CLI)
- 应用内部 -> 文件系统/数据库/模板引擎/命令执行
- 跨租户/跨权限域调用边界
