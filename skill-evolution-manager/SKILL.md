---
name: skill-evolution-manager
description: 专门用于在对话结束时，根据用户反馈和对话内容总结优化并迭代现有 Skills 的核心工具。它通过吸取对话中的“精华”（如成功的解决方案、失败的教训、特定的代码规范）来持续演进 Skills 库。
license: MIT
---

# Skill Evolution Manager

这是整个 AI 技能系统的“进化中枢”。它不仅负责优化单个 Skill，还负责跨 Skill 的经验复盘和沉淀。

## 核心职责

1.  **复盘诊断 (Session Review)**：在对话结束时，分析所有被调用的 Skill 的表现。
2.  **经验提取 (Experience Extraction)**：将非结构化的用户反馈转化为结构化的 JSON 数据（`evolution.json`）。
3.  **智能缝合 (Smart Stitching)**：将沉淀的经验自动写入 `references/evolution_learned.md`，并在 `SKILL.md` 末尾维护引用区块，确保持久化且不被版本更新覆盖。

## 使用场景

**Trigger**: 
- `/evolve`
- "复盘一下刚才的对话"
- "我觉得刚才那个工具不太好用，记录一下"
- "把这个经验保存到 Skill 里"

## 工作流 (The Evolution Workflow)

### 1. 经验复盘 (Review & Extract)
当用户触发复盘时，Agent 必须执行：
1.  **扫描上下文**：找出用户不满意的点（报错、风格不对、参数错误）或满意的点（特定 Prompt 效果好）。
2.  **定位 Skill**：确定是哪个 Skill 需要进化（例如 `yt-dlp` 或 `baoyu-comic`）。
3.  **生成 JSON**：在内存中构建如下 JSON 结构：
    ```json
    {
      "preferences": ["用户希望下载默认静音"],
      "fixes": ["Windows 下 ffmpeg 路径需转义"],
      "custom_prompts": "在执行前总是先打印预估耗时"
    }
    ```

### Evolution JSON Schema Contract (MUST)
Agent 在调用持久化脚本前，必须构造符合以下契约的 JSON：

```json
{
  "preferences": ["string, optional"],
  "fixes": ["string, optional"],
  "custom_prompts": "string, optional"
}
```

字段约束：
- `preferences` / `fixes` 必须是字符串数组（可选）。
- `custom_prompts` 必须是字符串（可选）。
- 允许只提交部分字段，脚本执行增量合并。

### 三字段语义分类（Generic, MUST）

`skill-evolution-manager` 是通用 Skill，三字段语义必须保持通用，不绑定单一业务域：

- `preferences`：稳定偏好类约束（风格、流程、输出偏好、风险偏好）。
- `fixes`：经过验证的纠偏规则（历史失败/遗漏后的可执行修正）。
- `custom_prompts`：高杠杆指令块（可复用、对目标 skill 行为有显著影响）。

写入内容时，先判断“属于哪一类”，再写入对应字段；同一条内容不要跨字段重复。

### 写入执行约束 (MUST Use Scripts)

- **禁止** Agent 直接手工改写 `evolution.json`、`references/evolution_learned.md`、`SKILL.md` 的演进引用区块。
- **必须** 调用 `scripts/merge_evolution.py` 写入 `.json`（经验持久化）。
- **每一次使用本 Skill** 都必须走“草稿优化闭环”（`prepare_evolution_draft.py` -> Agent 优化 -> `apply_evolution_draft.py`），不得跳过。
- **必须** 调用 `scripts/smart_stitch.py` 写入 `.md`（生成/更新 `references/evolution_learned.md` 并刷新 `SKILL.md` 引用区块）。
- 若需要批量对齐多个 Skill，调用 `scripts/align_all.py`，而不是逐文件手写。

### 2. 经验持久化 (Persist)
Agent **必须调用** `scripts/merge_evolution.py`，将上述 JSON 增量写入目标 Skill 的 `evolution.json` 文件中。
- **命令**: `python scripts/merge_evolution.py <skill_path> <json_string>`

### 2.5 经验质量优化 (Optimize, Mandatory)
每次使用本 Skill 时，都必须执行以下闭环：

1. 导出待优化草稿（仅三字段）：
   - **命令**: `python scripts/prepare_evolution_draft.py <skill_path> --out <draft_path>`
2. Agent 基于草稿进行去重/合并/优化（只编辑 `preferences` / `fixes` / `custom_prompts`）。
3. 应用优化结果并覆写 `evolution.json`（默认清理草稿）：
   - **命令**: `python scripts/apply_evolution_draft.py <skill_path> <draft_path>`
   - 若需保留草稿：`python scripts/apply_evolution_draft.py <skill_path> <draft_path> --keep-draft`

### 2.6 标准执行顺序 (Mandatory Sequence)
每次执行按以下顺序，禁止跳步：

1. `python scripts/merge_evolution.py <skill_path> <json_string>`
2. `python scripts/prepare_evolution_draft.py <skill_path> --out <draft_path>`
3. Agent 优化 `<draft_path>`（只改三字段）
4. `python scripts/apply_evolution_draft.py <skill_path> <draft_path>`
5. `python scripts/smart_stitch.py <skill_path>`

### 3. 文档缝合 (Stitch)
Agent **必须调用** `scripts/smart_stitch.py`，将 `evolution.json` 的内容转化为 Markdown 写入 `references/evolution_learned.md`，并在 `SKILL.md` 末尾追加或更新引用区块。
- **命令**: `python scripts/smart_stitch.py <skill_path>`

### 4. 跨版本对齐 (Align)
当 `skill-manager` 更新了某个 Skill 后，Agent 应主动运行 `smart_stitch.py`，将之前保存的经验“重新缝合”到新版文档中。

## 核心脚本

- `scripts/merge_evolution.py`: **增量合并工具**。负责读取旧 JSON，去重合并新 List，保存。
- `scripts/prepare_evolution_draft.py`: **优化草稿导出工具**。读取 `evolution.json`，抽取三字段并预去重，输出可供 Agent 优化的 draft。
- `scripts/apply_evolution_draft.py`: **优化结果回写工具**。校验并应用 draft，仅保留三字段覆写 `evolution.json`，默认清理 draft。
- `scripts/smart_stitch.py`: **文档生成工具**。负责读取 JSON，生成/更新 `references/evolution_learned.md`，并在 `SKILL.md` 末尾维护引用区块。
- `scripts/align_all.py`: **全量对齐工具**。一键遍历所有 Skill 文件夹，将存在的 `evolution.json` 经验重新缝合回对应 Skill 的 `references/evolution_learned.md`，并刷新 `SKILL.md` 引用区块。常用于 `skill-manager` 批量更新后的经验还原。

## 最佳实践

- **不要直接修改 SKILL.md 的正文**：除非是明显的拼写错误。所有的经验修正应通过 `evolution.json` 通道进行，这样可以保证在 Skill 升级时经验不丢失。
- **多 Skill 协同**：如果一次对话涉及多个 Skill，请依次为每个 Skill 执行上述流程。
