# 我的 Skills 仓库

本仓库用于维护自定义 Codex Skills，每个 Skill 以独立目录组织，并通过 `SKILL.md` 暴露能力说明与使用场景。

## 当前统计

当前共 **5** 个 skill。

## Skills 列表

| 名称 | 描述 | 路径 |
| --- | --- | --- |
| a2a-sdk | Agent2Agent (A2A) JavaScript SDK 实战 Skill，覆盖服务端/客户端实现、JSON-RPC/REST/gRPC、流式任务、鉴权与通知。 | a2a-sdk/SKILL.md |
| opencode-sdk | OpenCode SDK 集成 Skill，覆盖 client 创建、session 管理、文件操作、鉴权、实时事件与模板化代码生成。 | opencode-sdk/SKILL.md |
| pwn-exploit | 二进制利用 Skill，覆盖栈溢出、格式化字符串、堆利用、整数溢出等常见漏洞类型与利用思路。 | pwn-exploit/SKILL.md |
| code-audit | 基于LSP的智能代码安全审计Skill，利用OpenCode内置LSP进行代码理解、符号追踪、数据流分析，Agent自主识别项目特点并执行多维度安全审计（污点分析、认证授权、业务逻辑、敏感信息等），输出可验证的漏洞报告与PoC。 | code-audit/SKILL.md |
| taint-analysis | 通用、语言/框架无关的离线静态污点分析审计 Skill，用于在只读前提下执行 Source/Sink 识别、污点传播追踪、净化器校验、攻击链组合与 Markdown 报告输出。 | taint-analysis/SKILL.md |
