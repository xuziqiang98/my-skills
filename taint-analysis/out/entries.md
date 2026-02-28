# 入口面扫描结果 (entries)

- 生成时间: 2026-02-28T16:06:20+08:00
- repo_root: `/Users/xuziqiang/Workspace/my-skills/taint-analysis`
- 扫描范围: <repo-root>
- 扫描文件数: 3
- 文件预算: 200
- 局限说明: 基于静态正则与关键字启发式，无法完整覆盖动态路由、运行时反射与代码生成。

- 命中总数: 17

## main 入口 (3)
- `scripts/run_taint_audit.py:1278` | `if __name__ == "__main__":`
- `scripts/sink_scan.py:262` | `if __name__ == "__main__":`
- `scripts/entry_scan.py:257` | `if __name__ == "__main__":`

## Web handler/router 注册 (0)
- 无命中

## RPC service 注册 (2)
- `scripts/run_taint_audit.py:83` | `("rpc_input", re.compile(r"\b(request\s*\*?\w+Request|grpc\.|thrift|protobuf|rpc\.Call)")),`
- `scripts/entry_scan.py:75` | `Rule("rpc", "RPC service 注册", re.compile(r"\bgrpc\.NewServer\s*\(|\bRegister\w*Server\s*\(|\brpc\.Register\s*\(|\bthrift\b|@GrpcService\b|\bprotobuf\b")),`

## MQ consumer/callback (2)
- `scripts/run_taint_audit.py:84` | `("mq_input", re.compile(r"\b(message|msg|payload|consumer|subscribe|consume|event)\b", re.IGNORECASE)),`
- `scripts/entry_scan.py:76` | `Rule("mq", "MQ consumer/callback", re.compile(r"\b(subscribe|consume|on_message|onMessage|RabbitListener|KafkaListener)\b|\bamqp\.Channel\.Consume\s*\(|\bkafka\.(Consumer|Reader)\b`

## CLI flag/参数入口 (4)
- `scripts/run_taint_audit.py:1078` | `parser = argparse.ArgumentParser(description="通用静态污点审计统一入口")`
- `scripts/sink_scan.py:213` | `parser = argparse.ArgumentParser(description="敏感 sink 快速扫描（只读）")`
- `scripts/entry_scan.py:77` | `Rule("cli", "CLI flag/参数入口", re.compile(r"\b(argparse\.ArgumentParser|click\.(command|option)|cobra\.Command|urfave/cli|flag\.(String|Int|Bool)|commander\.)\b")),`
- `scripts/entry_scan.py:209` | `parser = argparse.ArgumentParser(description="入口点快速扫描（只读）")`

## 环境变量/配置加载 (2)
- `scripts/run_taint_audit.py:86` | `("env_input", re.compile(r"\b(getenv\s*\(|os\.environ|process\.env|dotenv|viper\.Get)")),`
- `scripts/entry_scan.py:78` | `Rule("env_cfg", "环境变量/配置加载", re.compile(r"\b(os\.environ|getenv\s*\(|process\.env|dotenv|viper\.Get\w*\(|config\.(get|load)|yaml\.(safe_)?load\s*\(|toml\.load\s*\(|json\.load\s*\()`

## 文件解析入口 (4)
- `scripts/run_taint_audit.py:87` | `("file_input", re.compile(r"\b(read(File|_to_string)?|ReadFile|fs\.readFile|ioutil\.ReadFile|Path\.(read_text|read_bytes)|yaml\.load|json\.load|xml\.)")),`
- `scripts/run_taint_audit.py:218` | `chunk = f.read(1024 * 1024)`
- `scripts/run_taint_audit.py:242` | `return json.loads(path.read_text(encoding="utf-8"))`
- `scripts/entry_scan.py:79` | `Rule("file_parse", "文件解析入口", re.compile(r"\b(read(File|_to_string)?|ReadFile|fs\.readFile|ioutil\.ReadFile|Path\.(read_text|read_bytes))\b|\b(json\.loads|yaml\.(safe_)?load|xml\.|p`
