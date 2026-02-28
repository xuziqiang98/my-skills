# 污点策略模板（taint_policy_template）

用途：定义 Source/Sink/Sanitizer/TaintKinds/TrustBoundaries，作为静态分析与人工复核共同基线。

## 元信息

- 项目名：
- 版本/提交：
- 审计范围：
- 审计时间：
- 负责人：

## TaintKinds

- [ ] cmd（命令执行）
- [ ] path（路径/文件系统）
- [ ] query（数据库查询）
- [ ] template（模板渲染）
- [ ] ssrf（外联请求）
- [ ] deser（反序列化）
- [ ] memory（内存边界/格式化）
- [ ] authz（鉴权/越权）

## Sources（不可信输入）

按入口面列举：
- HTTP：
- RPC：
- MQ：
- CLI：
- ENV/Config：
- File Parse：
- Plugin/Script：

记录格式：
- `source_id`：
- `位置`：`文件:行号`
- `输入契约`：参数名/类型/可控性
- `备注`：

## Sinks（敏感操作）

- 命令执行：
- SQL 原生执行：
- 模板执行/渲染：
- 反序列化：
- 文件写入/路径拼接：
- 网络外联：
- 内存危险 API：
- 危险配置点：

记录格式：
- `sink_id`：
- `位置`：`文件:行号`
- `敏感动作`：
- `前置 guard`：
- `备注`：

## Sanitizers（净化器/校验器）

- 输入校验：
- 编码/转义：
- 路径规范化：
- 参数化查询：
- 权限绑定：

记录格式：
- `sanitizer_id`：
- `位置`：`文件:行号`
- `覆盖对象`：变量/字段
- `是否可绕过`：是/否/未知

## TrustBoundaries（信任边界）

- 边界 A：外部请求 -> 服务入口
- 边界 B：服务逻辑 -> 文件系统/数据库/网络
- 边界 C：跨租户/跨角色上下文
- 边界 D：配置平面 -> 执行平面

## 路径敏感规则

- 分支条件需明确：
- 早返回/异常分支是否绕过：
- guard 与 sink 是否同一路径：
- 净化后是否二次污染：

## 示例（跨场景：CLI + 文件解析 + RPC）

```markdown
TaintKinds: cmd,path,deser,authz

Sources:
- SRC-CLI-01: cli/main.py:23  `cmd = args.user_cmd`
- SRC-FILE-01: parser/importer.py:58 `doc = yaml.load(fp, Loader=yaml.Loader)`
- SRC-RPC-01: rpc/service.go:41 `req.Payload`

Sinks:
- SNK-CMD-01: runner/hook.py:91 `subprocess.run(cmd, shell=True)`
- SNK-PATH-01: storage/save.go:77 `os.WriteFile(path, data, 0o644)`
- SNK-DESER-01: parser/importer.py:58 `yaml.load(...)`

Sanitizers:
- SAN-CMD-01: runner/sanitize.py:18 `sanitize_cmd(cmd)`（仅过滤分号，可能不充分）
- SAN-PATH-01: storage/path.py:12 `filepath.Clean(path)`（需确认目录约束）

TrustBoundaries:
- 外部 CLI/RPC 输入 -> 内部执行器
- 文件解析输入 -> 业务对象 -> 执行/写入
```
