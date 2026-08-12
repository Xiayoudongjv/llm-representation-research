# EXP-019 前 50 条人工语言复核指南

请按以下顺序操作：

1. 先打开 `language_qa_first50_rewrite_required.csv`，处理其中 16 条：自行改写并填写 `human_final_response`，或选择 `reject`。
2. 再打开 `language_qa_first50_attention_only.csv`，复核所有需要注意的条目。
3. 对 `MINOR_GRAMMAR_FIX` 和 `MINOR_NATURALNESS_FIX`：若建议表达不改变原意，可选择 `accept`；若需要改写，请填写 `human_final_response`；若不采用，请选择 `reject`。
4. 最后确认 19 条 `PASS`。确认原句可用时，可选择 `accept`。

`human_decision` 只允许填写：`accept`、`rewrite`、`reject`。

- `PASS`：通常在人工确认原句后才填写 `accept`。
- `MINOR_GRAMMAR_FIX` / `MINOR_NATURALNESS_FIX`：`accept` 表示接受 `proposed_response`；`rewrite` 表示人工填写 `human_final_response`；`reject` 表示排除该候选项。
- `HUMAN_REWRITE_REQUIRED`：只能选择 `rewrite` 并填写 `human_final_response`，或选择 `reject`。

不要自动批准任何条目。无需担心高级英语；优先检查句子是否自然、可独立理解、符合任务功能，并且不改变原有事实含义。
