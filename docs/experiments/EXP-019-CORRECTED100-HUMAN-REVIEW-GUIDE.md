# EXP-019 corrected-100 人工复核指南

请逐条只回答三个问题：

1. 单独看这句话，能理解它在表达什么吗？
2. 它确实属于当前 `task_class` 吗？
3. 英文是否自然到足以作为正常短回答？

判定规则：

- 三个基本都是“是” → `accept`
- 内容正确，但英语或表达需要由人修改 → `rewrite`，并由人工填写 `human_final_response`
- 类别、事实或含义本身有问题 → `reject`

允许的 `human_decision` 只有：`accept`、`rewrite`、`reject`。本文件不要求高级英语；重点是可单独理解、任务功能正确、表达自然，并保持原有事实或关系含义。

## task_class 提醒

- `logic`：由前提或规则推出结论
- `causality`：原因 → 结果或机制
- `analogy`：两个关系之间的对应
- `definition`：说明某概念是什么、属于什么，或其定义性功能

对于 `rewrite`，请人工自己填写完整句子；本复核包不提供自动改写建议。不要仅为了保留样本而改变 task_class，也不要添加新的事实、机制或关系。
