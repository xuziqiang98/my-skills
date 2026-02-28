# 正向数据流追踪 (flows_forward)

- 生成时间: 2026-02-28T16:06:20+08:00
- 参数: `{"repo_root": "/Users/xuziqiang/Workspace/my-skills/taint-analysis", "output_dir": "/Users/xuziqiang/Workspace/my-skills/taint-analysis/out", "focus_paths": ["<repo-root>"], "kinds": ["cmd", "path", "query", "template", "ssrf", "deser", "memory", "authz"], "depth": 2, "budget": 200, "cache": true}`
- 扫描范围: <repo-root>
- 局限说明: 正向追踪用于补漏与发现未知 sink，覆盖同文件窗口与风险调用关键词。

- 流数量: 6

## FWD-0001 | Source `scripts/run_taint_audit.py:1278`
- Source 片段: `if __name__ == "__main__":`
- 命中候选 sinks: 0
- 未知风险调用: 1
  - `scripts/run_taint_audit.py:1279` | `raise SystemExit(main())`
- 备注: 正向追踪基于同文件窗口与风险调用关键词，主要用于补漏与发现未知 sink。

## FWD-0002 | Source `scripts/run_taint_audit.py:83`
- Source 片段: `("rpc_input", re.compile(r"\b(request\s*\*?\w+Request|grpc\.|thrift|protobuf|rpc\.Call)")),`
- 命中候选 sinks: 2
  - `scripts/run_taint_audit.py:275` | `命令执行 / 进程启动` | `proc = subprocess.run(cmd, capture_output=True, text=True)`
  - `scripts/run_taint_audit.py:88` | `反序列化` | `("deser_input", re.compile(r"\b(pickle\.loads|yaml\.load|ObjectInputStream|BinaryFormatter|gob\.NewDecoder)")),`
- 未知风险调用: 6
  - `scripts/run_taint_audit.py:216` | `with path.open("rb") as f:`
  - `scripts/run_taint_audit.py:241` | `def load_json(path: Path) -> dict:`
  - `scripts/run_taint_audit.py:242` | `return json.loads(path.read_text(encoding="utf-8"))`
  - `scripts/run_taint_audit.py:247` | `path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")`
  - `scripts/run_taint_audit.py:250` | `def load_cache(path: Path) -> dict:`
  - `scripts/run_taint_audit.py:254` | `return load_json(path)`
- 备注: 正向追踪基于同文件窗口与风险调用关键词，主要用于补漏与发现未知 sink。

## FWD-0003 | Source `scripts/run_taint_audit.py:84`
- Source 片段: `("mq_input", re.compile(r"\b(message|msg|payload|consumer|subscribe|consume|event)\b", re.IGNORECASE)),`
- 命中候选 sinks: 2
  - `scripts/run_taint_audit.py:275` | `命令执行 / 进程启动` | `proc = subprocess.run(cmd, capture_output=True, text=True)`
  - `scripts/run_taint_audit.py:88` | `反序列化` | `("deser_input", re.compile(r"\b(pickle\.loads|yaml\.load|ObjectInputStream|BinaryFormatter|gob\.NewDecoder)")),`
- 未知风险调用: 6
  - `scripts/run_taint_audit.py:216` | `with path.open("rb") as f:`
  - `scripts/run_taint_audit.py:241` | `def load_json(path: Path) -> dict:`
  - `scripts/run_taint_audit.py:242` | `return json.loads(path.read_text(encoding="utf-8"))`
  - `scripts/run_taint_audit.py:247` | `path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")`
  - `scripts/run_taint_audit.py:250` | `def load_cache(path: Path) -> dict:`
  - `scripts/run_taint_audit.py:254` | `return load_json(path)`
- 备注: 正向追踪基于同文件窗口与风险调用关键词，主要用于补漏与发现未知 sink。

## FWD-0004 | Source `scripts/run_taint_audit.py:1078`
- Source 片段: `parser = argparse.ArgumentParser(description="通用静态污点审计统一入口")`
- 命中候选 sinks: 0
- 未知风险调用: 8
  - `scripts/run_taint_audit.py:1127` | `cache = {} if args.no_cache else load_cache(cache_path)`
  - `scripts/run_taint_audit.py:1153` | `write_text(output_dir / "entries.md", entries_md_text)`
  - `scripts/run_taint_audit.py:1154` | `write_text(output_dir / "sinks.md", sinks_md_text)`
  - `scripts/run_taint_audit.py:1155` | `write_text(output_dir / "taint_policy.md", taint_policy_text)`
  - `scripts/run_taint_audit.py:1156` | `write_text(output_dir / "flows_backward.md", flows_backward_text)`
  - `scripts/run_taint_audit.py:1157` | `write_text(output_dir / "flows_forward.md", flows_forward_text)`
- 备注: 正向追踪基于同文件窗口与风险调用关键词，主要用于补漏与发现未知 sink。

## FWD-0005 | Source `scripts/run_taint_audit.py:86`
- Source 片段: `("env_input", re.compile(r"\b(getenv\s*\(|os\.environ|process\.env|dotenv|viper\.Get)")),`
- 命中候选 sinks: 2
  - `scripts/run_taint_audit.py:275` | `命令执行 / 进程启动` | `proc = subprocess.run(cmd, capture_output=True, text=True)`
  - `scripts/run_taint_audit.py:88` | `反序列化` | `("deser_input", re.compile(r"\b(pickle\.loads|yaml\.load|ObjectInputStream|BinaryFormatter|gob\.NewDecoder)")),`
- 未知风险调用: 6
  - `scripts/run_taint_audit.py:216` | `with path.open("rb") as f:`
  - `scripts/run_taint_audit.py:241` | `def load_json(path: Path) -> dict:`
  - `scripts/run_taint_audit.py:242` | `return json.loads(path.read_text(encoding="utf-8"))`
  - `scripts/run_taint_audit.py:247` | `path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")`
  - `scripts/run_taint_audit.py:250` | `def load_cache(path: Path) -> dict:`
  - `scripts/run_taint_audit.py:254` | `return load_json(path)`
- 备注: 正向追踪基于同文件窗口与风险调用关键词，主要用于补漏与发现未知 sink。

## FWD-0006 | Source `scripts/run_taint_audit.py:87`
- Source 片段: `("file_input", re.compile(r"\b(read(File|_to_string)?|ReadFile|fs\.readFile|ioutil\.ReadFile|Path\.(read_text|read_bytes)|yaml\.load|json\.load|xml\.)")),`
- 命中候选 sinks: 2
  - `scripts/run_taint_audit.py:275` | `命令执行 / 进程启动` | `proc = subprocess.run(cmd, capture_output=True, text=True)`
  - `scripts/run_taint_audit.py:88` | `反序列化` | `("deser_input", re.compile(r"\b(pickle\.loads|yaml\.load|ObjectInputStream|BinaryFormatter|gob\.NewDecoder)")),`
- 未知风险调用: 6
  - `scripts/run_taint_audit.py:216` | `with path.open("rb") as f:`
  - `scripts/run_taint_audit.py:241` | `def load_json(path: Path) -> dict:`
  - `scripts/run_taint_audit.py:242` | `return json.loads(path.read_text(encoding="utf-8"))`
  - `scripts/run_taint_audit.py:247` | `path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")`
  - `scripts/run_taint_audit.py:250` | `def load_cache(path: Path) -> dict:`
  - `scripts/run_taint_audit.py:254` | `return load_json(path)`
- 备注: 正向追踪基于同文件窗口与风险调用关键词，主要用于补漏与发现未知 sink。
