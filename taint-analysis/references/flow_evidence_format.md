# 数据流证据统一格式（flow_evidence_format）

目标：让每条路径证据可复核、可追溯、可比较。

## 1. 证据对象结构

```yaml
flow_id: BWD-0001
kind: cmd
source:
  location: api/user.py:42
  snippet: user_input = request.args.get("name")
sink:
  location: core/runner.py:118
  snippet: subprocess.run(hook_cmd, shell=True)
function_stack:
  - api/user.py:update_profile:42
  - service/profile.py:save_profile:77
  - core/runner.py:run_hook:118
variable_chain:
  - user_input
  - profile_name
  - hook_cmd
guards:
  - core/runner.py:110 if has_role(user, "admin")
sanitizers:
  - core/runner.py:109 hook_cmd = sanitize_cmd(user_input)
path_decision:
  - branch: user.is_admin == True
  - conclusion: guard 存在但可绕过（租户绑定缺失）
confidence:
  evidence_score: 76
  status: Likely
assumptions:
  - sanitize_cmd 仅做字符黑名单
```

## 2. 函数栈（Function Stack）

- 格式：`文件:函数:行号`
- 最短包含：source 所在函数 + sink 所在函数
- 若只有局部证据，写 `<global>` 并注明原因

## 3. 变量链（Variable Chain）

- 记录从 source 到 sink 的关键变量名
- 明确别名映射/字段传递（如 `req.name -> dto.name -> cmd`）
- 无法确定时写“近似链”，并标不确定点

## 4. 关键分支与 Guard 结论

- 至少记录一个关键条件分支
- 结论必须是以下之一：
  - `guard 生效`（降低风险）
  - `guard 不生效`（路径不受限）
  - `guard 不确定`（需人工确认）

## 5. 证据片段格式

- 建议格式：
  - `[role] 文件:行号 | 代码片段`
- role 取值：`source` `sink` `call` `guard` `sanitizer`

示例：
```markdown
- [source] api/user.py:42 | user_input = request.args.get("name")
- [call] service/profile.py:77 | save_profile(profile_name)
- [sink] core/runner.py:118 | subprocess.run(hook_cmd, shell=True)
```

## 6. 证据充分性最低要求

- Source 与 Sink 都可定位到 `文件:行号`
- 至少 2 个路径节点（可含调用点）
- 至少 1 条 guard/sanitizer 判断（即使为“未发现”）
- 明确假设与局限
