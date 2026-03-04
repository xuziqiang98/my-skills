# User-Learned Best Practices & Constraints

> **Auto-Generated**: This file is maintained by `skill-evolution-manager`. Do not edit manually.

## User Preferences

- 审计时必须逐项执行检查清单，不能只依赖迭代分析发现
- 发现的漏洞之间必须做交叉分析，检查是否存在组合放大效应（如慢散列×SQL注入=时序盲注）
- 每发现一个安全机制，必须反向评估该机制自身能否被武器化
- 状态机完整性检查：不仅检查「谁有权操作」，还要检查「已完成的操作能否被重复执行」
- 业务逻辑漏洞完全可以通过静态代码审计发现，不应声称需要动态渗透测试

## Known Fixes & Workarounds

- 在逐源深入分析（Phase 3-4）完成后，强制执行交互矩阵分析（Phase 5）：将已发现的漏洞两两配对，分析组合效应
- 在Phase 2 Sink发现后，新增「防御机制反转检查」：对每个安全机制问「攻击者能否利用此机制攻击其他用户？」
- 在IDOR检查中新增「幂等性/状态校验」：已支付订单能否再次支付？已退款能否再次退款？状态转换是否有前置条件检查？
- 添加条件竞争漏洞检测：检查并发操作是否有正确的锁机制
