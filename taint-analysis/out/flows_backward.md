# 反向数据流追踪 (flows_backward)

- 生成时间: 2026-02-28T16:06:20+08:00
- 参数: `{"repo_root": "/Users/xuziqiang/Workspace/my-skills/taint-analysis", "output_dir": "/Users/xuziqiang/Workspace/my-skills/taint-analysis/out", "focus_paths": ["<repo-root>"], "kinds": ["cmd", "path", "query", "template", "ssrf", "deser", "memory", "authz"], "depth": 2, "budget": 200, "cache": true}`
- 扫描范围: <repo-root>
- 局限说明: 反向追踪优先高危 sink，采用调用点近似与邻域 source 搜索，不是完整 SSA。

- 流数量: 8

## BWD-0001 | deser | scripts/run_taint_audit.py:88
- Sink: `反序列化` | `("deser_input", re.compile(r"\b(pickle\.loads|yaml\.load|ObjectInputStream|BinaryFormatter|gob\.NewDecoder)")),`
- Source: `scripts/run_taint_audit.py:87` | `("file_input", re.compile(r"\b(read(File|_to_string)?|ReadFile|fs\.readFile|ioutil\.ReadFile|Path\.(read_text|read_bytes)|yaml\.load|json\.load|xml\.)")),`
- 函数栈: scripts/run_taint_audit.py:<global>:88
- 变量链: load, compile, yaml
- Guard: <none>
- Sanitizer: L92: re.compile(r"\b(escape|sanitize|validate|clean|safe_\w+|quote|encodeURIComponent|html\.EscapeString|xss\.Escape)\b", re.IGNORECASE),, L93: re.compile(r"\b(realpath|normpath|filepath\.Clean|path\.normalize|canonicalize)\b", re.IGNORECASE),, L94: re.compile(r"\b(preparedStatement|parameterized|bindParam|QueryBuilder|allowlist|whitelist|regex)\b", re.IGNORECASE),
- 备注:
  - 未解析到明显调用者，函数栈证据以当前函数为主。
  - 检测到疑似净化器，需人工确认净化是否覆盖到 sink 参数。
- 证据片段:
  - [sink] `scripts/run_taint_audit.py:88` | `("deser_input", re.compile(r"\b(pickle\.loads|yaml\.load|ObjectInputStream|BinaryFormatter|gob\.NewDecoder)")),`
  - [source] `scripts/run_taint_audit.py:87` | `("file_input", re.compile(r"\b(read(File|_to_string)?|ReadFile|fs\.readFile|ioutil\.ReadFile|Path\.(read_text|read_bytes)|yaml\.load|json\.load|xml\.)")),`

## BWD-0002 | cmd | scripts/run_taint_audit.py:275
- Sink: `命令执行 / 进程启动` | `proc = subprocess.run(cmd, capture_output=True, text=True)`
- Source: `scripts/run_taint_audit.py:242` | `return json.loads(path.read_text(encoding="utf-8"))`
- 函数栈: scripts/run_taint_audit.py:run_child_script:275 -> scripts/run_taint_audit.py:<callsite>:273 -> scripts/run_taint_audit.py:<callsite>:1189
- 变量链: cmd, run, text, proc
- Guard: <none>
- Sanitizer: <none>
- 证据片段:
  - [sink] `scripts/run_taint_audit.py:275` | `proc = subprocess.run(cmd, capture_output=True, text=True)`
  - [source] `scripts/run_taint_audit.py:242` | `return json.loads(path.read_text(encoding="utf-8"))`
  - [call] `scripts/run_taint_audit.py:273` | `def run_child_script(script: Path, argv: List[str], verbose: bool = False) -> None:`
  - [call] `scripts/run_taint_audit.py:1189` | `run_child_script(entry_script, entry_argv, verbose=args.verbose)`

## BWD-0003 | cmd | scripts/sink_scan.py:75
- Sink: `动态执行 / eval` | `Rule("eval", "动态执行 / eval", "high", re.compile(r"\b(eval\s*\(|exec\s*\(|new\s+Function\s*\(|vm\.runIn\w+\s*\(|ScriptEngineManager\b)")),`
- Source: `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`
- 函数栈: scripts/sink_scan.py:<global>:75
- 变量链: compile, runIn, Function, Rule
- Guard: <none>
- Sanitizer: L70: regex: re.Pattern[str]
- 备注:
  - 未解析到明显调用者，函数栈证据以当前函数为主。
  - 检测到疑似净化器，需人工确认净化是否覆盖到 sink 参数。
- 证据片段:
  - [sink] `scripts/sink_scan.py:75` | `Rule("eval", "动态执行 / eval", "high", re.compile(r"\b(eval\s*\(|exec\s*\(|new\s+Function\s*\(|vm\.runIn\w+\s*\(|ScriptEngineManager\b)")),`
  - [source] `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`

## BWD-0004 | query | scripts/sink_scan.py:77
- Sink: `SQL 原生拼接/执行` | `Rule("sql", "SQL 原生拼接/执行", "high", re.compile(r"\b(cursor\.execute|db\.query|db\.exec|sequelize\.query|createNativeQuery|Statement\.execute(Query)?|Raw\s*\()\b", re.IGNORECASE)),`
- Source: `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`
- 函数栈: scripts/sink_scan.py:<global>:77
- 变量链: query, IGNORECASE, SQL, compile
- Guard: <none>
- Sanitizer: L70: regex: re.Pattern[str]
- 备注:
  - 未解析到明显调用者，函数栈证据以当前函数为主。
  - 检测到疑似净化器，需人工确认净化是否覆盖到 sink 参数。
- 证据片段:
  - [sink] `scripts/sink_scan.py:77` | `Rule("sql", "SQL 原生拼接/执行", "high", re.compile(r"\b(cursor\.execute|db\.query|db\.exec|sequelize\.query|createNativeQuery|Statement\.execute(Query)?|Raw\s*\()\b", re.IGNORECASE)),`
  - [source] `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`

## BWD-0005 | deser | scripts/sink_scan.py:78
- Sink: `反序列化` | `Rule("deser", "反序列化", "high", re.compile(r"\b(pickle\.loads|yaml\.load\s*\(|ObjectInputStream|BinaryFormatter|gob\.NewDecoder|serde_json::from_(str|slice)|jsonpickle\.decode)\b")),`
- Source: `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`
- 函数栈: scripts/sink_scan.py:<global>:78
- 变量链: load, ObjectInputStream, deser, compile
- Guard: <none>
- Sanitizer: L70: regex: re.Pattern[str]
- 备注:
  - 未解析到明显调用者，函数栈证据以当前函数为主。
  - 检测到疑似净化器，需人工确认净化是否覆盖到 sink 参数。
- 证据片段:
  - [sink] `scripts/sink_scan.py:78` | `Rule("deser", "反序列化", "high", re.compile(r"\b(pickle\.loads|yaml\.load\s*\(|ObjectInputStream|BinaryFormatter|gob\.NewDecoder|serde_json::from_(str|slice)|jsonpickle\.decode)\b")),`
  - [source] `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`

## BWD-0006 | template | scripts/sink_scan.py:76
- Sink: `模板渲染` | `Rule("template", "模板渲染", "medium", re.compile(r"\b(render_template_string|jinja2\.Template|Mustache\.render|handlebars\.compile|template\.Execute|Thymeleaf|freemarker)\b", re.IGNOR`
- Source: `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`
- 函数栈: scripts/sink_scan.py:<global>:76
- 变量链: Mustache, IGNORECASE, compile, medium
- Guard: <none>
- Sanitizer: L70: regex: re.Pattern[str]
- 备注:
  - 未解析到明显调用者，函数栈证据以当前函数为主。
  - 检测到疑似净化器，需人工确认净化是否覆盖到 sink 参数。
- 证据片段:
  - [sink] `scripts/sink_scan.py:76` | `Rule("template", "模板渲染", "medium", re.compile(r"\b(render_template_string|jinja2\.Template|Mustache\.render|handlebars\.compile|template\.Execute|Thymeleaf|freemarker)\b", re.IGNORECASE)),`
  - [source] `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`

## BWD-0007 | path | scripts/sink_scan.py:79
- Sink: `文件写入/路径拼接` | `Rule("file_write", "文件写入/路径拼接", "medium", re.compile(r"\b(open\s*\([^\n]*[\"']w|fs\.writeFile|ioutil\.WriteFile|Files\.write|FileOutputStream|path\.join|os\.path\.join|filepath\.Jo`
- Source: `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`
- 函数栈: scripts/sink_scan.py:<global>:79
- 变量链: path, WriteFile, ioutil, IGNORECASE
- Guard: <none>
- Sanitizer: <none>
- 备注:
  - 未解析到明显调用者，函数栈证据以当前函数为主。
- 证据片段:
  - [sink] `scripts/sink_scan.py:79` | `Rule("file_write", "文件写入/路径拼接", "medium", re.compile(r"\b(open\s*\([^\n]*[\"']w|fs\.writeFile|ioutil\.WriteFile|Files\.write|FileOutputStream|path\.join|os\.path\.join|filepath\.Join)\b", re.IGNORECASE)),`
  - [source] `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`

## BWD-0008 | authz | scripts/sink_scan.py:82
- Sink: `危险配置` | `Rule("dangerous_cfg", "危险配置", "medium", re.compile(r"\b(verify\s*=\s*False|InsecureSkipVerify\s*:\s*true|allow_origins\s*=\s*\[?['\"]\*['\"]\]?|disable_auth|skip_auth|permitAll\s*\`
- Source: `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`
- 函数栈: scripts/sink_scan.py:<global>:82
- 变量链: IGNORECASE, InsecureSkipVerify, compile, allow_origins
- Guard: <none>
- Sanitizer: <none>
- 备注:
  - 未解析到明显调用者，函数栈证据以当前函数为主。
- 证据片段:
  - [sink] `scripts/sink_scan.py:82` | `Rule("dangerous_cfg", "危险配置", "medium", re.compile(r"\b(verify\s*=\s*False|InsecureSkipVerify\s*:\s*true|allow_origins\s*=\s*\[?['\"]\*['\"]\]?|disable_auth|skip_auth|permitAll\s*\()", re.IGNORECASE)),`
  - [source] `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`
