# 攻击链组合 (attack_chains)

- 生成时间: 2026-02-28T16:06:20+08:00
- 参数: `{"repo_root": "/Users/xuziqiang/Workspace/my-skills/taint-analysis", "output_dir": "/Users/xuziqiang/Workspace/my-skills/taint-analysis/out", "focus_paths": ["<repo-root>"], "kinds": ["cmd", "path", "query", "template", "ssrf", "deser", "memory", "authz"], "depth": 2, "budget": 200, "cache": true}`
- 扫描范围: <repo-root>
- 局限说明: 攻击链为静态组合推演，不代表真实环境可直接利用。

- 攻击链数量: 1

## CHAIN-01 | 写文件 -> 加载/执行
- 前置条件:
  - 攻击者可控文件名或内容
  - 目标存在后续加载/执行路径
- 步骤:
  - 利用 path 类问题写入可控内容或篡改关键文件
  - 触发 cmd/deser/template 路径实现执行或扩展控制
- 影响面: 可能导致持久化控制、远程代码执行或供应链污染。
