---
name: taint-analysis
description: 通用、语言/框架无关的离线静态污点分析审计 Skill。用于在只读前提下对任意仓库执行入口/Source 发现、Sink 扫描、污点策略建模、反向与正向数据流追踪、净化器与路径敏感校验、业务逻辑与越权审计、交叉验证、攻击链组合和最终 Markdown 报告输出，并落盘可复核中间产物。
---

# taint-analysis

将本 Skill 作为“静态污点审计流程引擎”使用，而不是简单包装现成 SAST。默认先给出可复核第一版结果，再在报告中显式标注假设与不确定性。

## 1) Skill 概述

适用范围：
- Web 服务（HTTP router/handler）
- CLI 工具
- RPC/gRPC/Thrift 服务
- 文件解析与导入流程
- MQ consumer/callback
- 插件与脚本执行入口
- 反序列化路径
- 配置驱动执行路径

核心目标：
- 执行通用静态污点审计流程（Phase0~5）
- 输出结构化证据链与误报控制结论
- 落盘完整中间产物，便于人工复核与增量复跑

## 2) 触发条件（Triggers / Anti-triggers）

Triggers：
- 用户要求“做一次 taint analysis / 污点分析 / 数据流安全审计”。
- 用户要求“离线、只读、快速出第一版安全发现”。
- 用户要求“输出可复核证据链（source/sink/path/guard）”。
- 用户要求“跨语言、框架无关的安全审计流程”。

Anti-triggers：
- 用户仅需要动态渗透、在线扫描、实时攻击脚本。
- 用户明确要求进攻性利用、武器化 PoC 或越权攻击实施。
- 用户只需要单点 lint/格式化，不需要安全审计流程。

## 3) 输入（Inputs / Assumptions）

必选/默认输入：
- `repo_root`：默认当前目录 `.`
- `focus_paths`：可选；默认空（先全局粗扫后聚焦）
- `taint_kinds`：默认 `cmd,path,query,template,ssrf,deser,memory,authz`
- `depth`：默认 `3`（优先高危 sink 反向追踪）
- `budget`：默认不限制；若提供则作为扫描文件预算上限
- `output_dir`：默认 `./out`

假设：
- 审计以静态信息为主，不执行目标业务逻辑。
- 代码库可代表主要执行路径；运行时动态加载可能不可见。
- 信息不足时先产出第一版结果，并在报告写明不确定性。

## 4) 输出（Outputs / Artifacts）

默认输出目录：`out/`

主要产物：
- `out/entries.md`
- `out/sinks.md`
- `out/taint_policy.md`
- `out/flows_backward.md`
- `out/flows_forward.md`
- `out/authz_model.md`
- `out/findings.md`
- `out/attack_chains.md`
- `out/report.md`
- `out/cache.json`

要求：
- 所有 Markdown 均包含生成时间、参数、扫描范围、局限说明。
- `findings.md` 按严重性排序，包含 evidence_score 与状态。

## 5) 核心流程（Phase0~5）

### Phase 0: 工程理解与准备
执行：`project-profiler / symbol-indexer / callgraph / cfg-ir`（近似）
- 统计语言分布、扫描文件范围。
- 建立函数定义与调用点索引（启发式调用图）。
- 明确信任边界（外部输入 -> 内部敏感操作）。

### Phase 1: 资产发现
执行：`entry-surface-discovery / sink-point-scanner / security-asset / trust-boundary`
- 调用 `scripts/entry_scan.py` 生成入口清单。
- 调用 `scripts/sink_scan.py` 生成 sink 清单。
- 对入口面与 sink 面按类别分组并定位到 `文件:行号`。

### Phase 1.5: 入口功能分析
执行：`entry-function-analyzer`
- 对重点入口做业务摘要。
- 记录输入契约（参数、格式、来源可信度）。
- 记录权限上下文（是否绑定用户/租户/角色）。
- 记录副作用（写文件、发请求、执行命令、跨服务调用）。

### Phase 2: 技术漏洞审计（反向追踪优先）
执行：
- `taint-policy-builder`
- `backward-dataflow-tracer`
- `path-sensitivity-refiner`
- `sanitizer-checker`
- `vulnerability-validator`（静态可利用性）

方法：
- 先从高危 sink 反向追踪 source 候选与调用链。
- 优先同文件/同模块，再跨模块；优先 direct call 再 callers。
- 输出可复核路径证据（source/sink/函数栈/变量链/guard/sanitizer）。

### Phase 2.5: 正向数据流追踪
执行：`forward-flow-tracer`
- 从代表性 source 正向追踪到敏感区。
- 补漏未覆盖 sink，并发现未知风险调用模式。

### Phase 3: 业务逻辑审计
执行：`authz-model-extractor / access-control / business-logic`
- 提取鉴权与租户绑定语义（check/permit/authorize/owner/tenant）。
- 对 findings 补充“是否缺权限绑定”的静态提示。

### Phase 3.5: 交叉验证
执行：`flow-cross-validator`
- 对齐反向/正向流，做去重与证据强度评分。
- 为每条 finding 给 `evidence_score(0-100)` 与状态。

### Phase 4: 攻击链分析
执行：`attack-chain-analyzer`
- 组合规则：写文件->加载执行、越权->敏感 sink、外联/泄露->绕过校验。
- 输出前置条件、影响面与不确定性。

### Phase 5: 报告生成
执行：`report-generator`
- 按 Markdown 模板输出摘要、方法、发现、攻击链、修复路线图、假设与局限。

## 6) 误报控制与证据标准

每条 finding 必须包含：
- Source
- Sink
- 传播路径（函数栈 + 变量链）
- 关键 guard/sanitizer 判断
- 文件:行号证据片段

状态标准：
- `Confirmed`：证据链闭环，source/sink/路径明确，guard/sanitizer 不足以阻断或可绕过。
- `Likely`：source 与 sink 明确，路径基本成立，但 guard/sanitizer 真实性仍需验证。
- `Possible`：命中可疑 sink 或路径片段，证据不完整或依赖较强假设。

常见误报来源与对策：
- 别名/引用传播：记录变量别名映射，必要时人工展开调用参数。
- 动态分发：在报告标注动态分发点，降低自动确认等级。
- 宏/模板生成代码：回溯到展开前模板上下文核对输入来源。
- 反射：标注反射目标来源与可控性，不直接判 Confirmed。
- 字符串拼接：判断拼接参与变量是否含不可信输入。
- 序列化多态：确认反序列化类型白名单和绑定关系。
- 错误处理分支：校验异常分支是否绕过校验逻辑。

降误报 checklist：
- 输入长度/范围限制是否存在。
- 编码/解码顺序与次数是否正确。
- 权限/租户绑定是否在 sink 前有效执行。
- 来源签名/完整性校验是否覆盖当前路径。
- 二次污染检查（净化后再拼接/再污染）是否存在。

## 7) 安全与合规边界

- 仅执行防御性审计与修复建议。
- PoC 仅允许最小复现/单元测试式复现。
- 不编写面向真实目标的攻击脚本。
- 若用户要求进攻性利用，明确提示需合法授权与范围界定。

## 8) 快速上手

最短命令：
```bash
python scripts/run_taint_audit.py
```

常用参数：
```bash
python scripts/run_taint_audit.py \
  --repo-root . \
  --focus-path src,internal/api \
  --kinds cmd,path,query,template,ssrf,deser,memory,authz \
  --depth 3 \
  --budget 1500 \
  --output-dir .audit
```

示例输出片段（证据链）：
```markdown
## F-003 | high | Likely | score=76
- Source: `api/user_handler.py:42`
- Sink: `core/exec_runner.py:118`
- 函数栈: api/user_handler.py:update_profile:42 -> core/exec_runner.py:run_hook:118
- 变量链: user_input, hook_cmd
- Guard: <none>
- Sanitizer: L109: sanitize_cmd(user_input)
- 证据链:
  - [source] `api/user_handler.py:42` | `user_input = request.args.get("name")`
  - [sink] `core/exec_runner.py:118` | `subprocess.run(hook_cmd, shell=True)`
```

## 执行约定（供 agent 直接执行）

1. 默认执行：
```bash
python scripts/run_taint_audit.py --repo-root . --output-dir ./out
```
2. 优先读取：`out/report.md` 与 `out/findings.md`。
3. 需要复核证据时依次查看：`out/flows_backward.md`、`out/flows_forward.md`、`out/entries.md`、`out/sinks.md`。
4. 增量复跑默认启用缓存；若需全量重跑使用 `--no-cache`。

## Agent 调用示例

用户：`帮我做一次 taint analysis`

agent 执行：
```bash
python scripts/run_taint_audit.py --repo-root . --output-dir ./out --depth 3
```

agent 输出结论时：
- 基于 `out/report.md` 给出风险摘要与优先修复项。
- 基于 `out/findings.md` 引用 Top findings 的 Source/Sink/证据链。
- 明确列出“假设与不确定性”，不把启发式结果当成最终定论。

## 参考资料

- 策略模板：`references/taint_policy_template.md`
- sink 目录：`references/sink_catalog.md`
- 证据格式：`references/flow_evidence_format.md`
- finding 模板：`references/finding_template.md`
- 报告模板：`references/report_template.md`
