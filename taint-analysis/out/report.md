# 静态污点审计报告 (report)

- 生成时间: 2026-02-28T16:06:20+08:00
- 参数: `{"repo_root": "/Users/xuziqiang/Workspace/my-skills/taint-analysis", "output_dir": "/Users/xuziqiang/Workspace/my-skills/taint-analysis/out", "focus_paths": ["<repo-root>"], "kinds": ["cmd", "path", "query", "template", "ssrf", "deser", "memory", "authz"], "depth": 2, "budget": 200, "cache": true}`
- 扫描范围: <repo-root>
- 局限说明: 本报告基于离线静态启发式分析，建议将高风险项纳入代码复核与测试验证。

## 摘要
- 总发现: 8
- 严重性分布: {'critical': 1, 'high': 4, 'medium': 3}
- 状态分布: {'Confirmed': 1, 'Likely': 6, 'Possible': 1}
- 高危 Confirmed: 1

## 方法与范围
- Phase0: 工程画像、函数索引、近似调用图
- Phase1: 入口面与 sink 面静态扫描
- Phase2: 高危 sink 反向追踪、路径敏感与净化器检查
- Phase2.5: 代表 source 正向补漏
- Phase3: authz 语义提取与越权提示
- Phase3.5: 交叉验证、去重与证据评分
- Phase4: 攻击链规则组合
- Phase5: 结构化报告生成
- 扫描文件数: 3
- 语言分布: {'.py': 3}

## 发现列表（Top）
- F-002 | critical | Confirmed | score=100 | 命令执行 / 进程启动 潜在污点传播 (cmd) | scripts/run_taint_audit.py:275
- F-003 | high | Likely | score=76 | 动态执行 / eval 潜在污点传播 (cmd) | scripts/sink_scan.py:75
- F-004 | high | Likely | score=76 | SQL 原生拼接/执行 潜在污点传播 (query) | scripts/sink_scan.py:77
- F-005 | high | Likely | score=76 | 反序列化 潜在污点传播 (deser) | scripts/sink_scan.py:78
- F-001 | high | Likely | score=74 | 反序列化 潜在污点传播 (deser) | scripts/run_taint_audit.py:88
- F-007 | medium | Likely | score=62 | 文件写入/路径拼接 潜在污点传播 (path) | scripts/sink_scan.py:79
- F-008 | medium | Likely | score=62 | 危险配置 潜在污点传播 (authz) | scripts/sink_scan.py:82
- F-006 | medium | Possible | score=56 | 模板渲染 潜在污点传播 (template) | scripts/sink_scan.py:76

## 攻击链
- CHAIN-01 | 写文件 -> 加载/执行 | 影响: 可能导致持久化控制、远程代码执行或供应链污染。

## 修复路线图
1. 先修复 critical/high 且 Confirmed/Likely 的命令执行、反序列化、越权链路。
2. 为高风险 sink 引入统一输入校验、参数化接口与显式权限绑定。
3. 将本次 finding 转化为单元测试/集成测试，建立回归基线。
4. 对 Possible 项做定向人工复核，更新 taint policy 与误报抑制规则。

## 假设与局限
- 假设代码仓库可代表主要执行路径，未动态加载的外部插件默认不可见。
- 局限: 近似调用图与正则模式可能漏报动态分发、反射、宏展开、多态序列化路径。
- 局限: 未执行真实请求与运行时探针，证据链以静态可复核为目标。
