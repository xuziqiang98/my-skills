# Sink 扫描结果 (sinks)

- 生成时间: 2026-02-28T16:06:20+08:00
- repo_root: `/Users/xuziqiang/Workspace/my-skills/taint-analysis`
- 扫描范围: <repo-root>
- 扫描文件数: 3
- 文件预算: 200
- 局限说明: 命中表示“可疑 sink 位置”，需结合数据流、guard、净化器再判定是否可利用。

- 命中总数: 8

## 命令执行 / 进程启动 [high] (1)
- `scripts/run_taint_audit.py:275` | `proc = subprocess.run(cmd, capture_output=True, text=True)`

## 动态执行 / eval [high] (1)
- `scripts/sink_scan.py:75` | `Rule("eval", "动态执行 / eval", "high", re.compile(r"\b(eval\s*\(|exec\s*\(|new\s+Function\s*\(|vm\.runIn\w+\s*\(|ScriptEngineManager\b)")),`

## 模板渲染 [medium] (1)
- `scripts/sink_scan.py:76` | `Rule("template", "模板渲染", "medium", re.compile(r"\b(render_template_string|jinja2\.Template|Mustache\.render|handlebars\.compile|template\.Execute|Thymeleaf|freemarker)\b", re.IGNOR`

## SQL 原生拼接/执行 [high] (1)
- `scripts/sink_scan.py:77` | `Rule("sql", "SQL 原生拼接/执行", "high", re.compile(r"\b(cursor\.execute|db\.query|db\.exec|sequelize\.query|createNativeQuery|Statement\.execute(Query)?|Raw\s*\()\b", re.IGNORECASE)),`

## 反序列化 [high] (2)
- `scripts/run_taint_audit.py:88` | `("deser_input", re.compile(r"\b(pickle\.loads|yaml\.load|ObjectInputStream|BinaryFormatter|gob\.NewDecoder)")),`
- `scripts/sink_scan.py:78` | `Rule("deser", "反序列化", "high", re.compile(r"\b(pickle\.loads|yaml\.load\s*\(|ObjectInputStream|BinaryFormatter|gob\.NewDecoder|serde_json::from_(str|slice)|jsonpickle\.decode)\b")),`

## 文件写入/路径拼接 [medium] (1)
- `scripts/sink_scan.py:79` | `Rule("file_write", "文件写入/路径拼接", "medium", re.compile(r"\b(open\s*\([^\n]*[\"']w|fs\.writeFile|ioutil\.WriteFile|Files\.write|FileOutputStream|path\.join|os\.path\.join|filepath\.Jo`

## 外联请求/网络发起 [medium] (0)
- 无命中

## 格式化与内存边界 [high] (0)
- 无命中

## 危险配置 [medium] (1)
- `scripts/sink_scan.py:82` | `Rule("dangerous_cfg", "危险配置", "medium", re.compile(r"\b(verify\s*=\s*False|InsecureSkipVerify\s*:\s*true|allow_origins\s*=\s*\[?['\"]\*['\"]\]?|disable_auth|skip_auth|permitAll\s*\`
