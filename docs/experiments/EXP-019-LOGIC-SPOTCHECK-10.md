# EXP-019 Logic 定向复核（10条）

目的：

随机40条人工审计中，logic 出现2条标签不匹配。
本次仅确认该问题是个别样本，还是 logic 类存在更广泛的构造问题。

只判断：

“这条回答的主要功能是否确实是 logic？”

判断标准：

Y = logic 功能明确
N = 主要不是 logic
? = 边界/不确定

Logic 定义：

前提、条件、规则、排除、比较、空间/数量关系等，能够支持一个推论或结论。

特别注意：

普通事实陈述本身不自动等于 logic。

不要判断：

* 英语是否完美
* 来源是否权威
* evaluator 会不会识别
* 是否有利于后续实验

---

## 冻结解释规则

此规则在人工复核前固定：

* 0 N：`ISOLATED_LOGIC_ERRORS_SUPPORTED`
* 1 N：`LIKELY_ISOLATED_WITH_MINOR_RISK`
* 2 或更多 N：`LOGIC_CLASS_REVIEW_REQUIRED`
* 每个 `?` 视为未解决，不计作 Y；若 N 与 ? 合计达到 2 或更多：`LOGIC_CLASS_REVIEW_REQUIRED`

---
## 01

**ID:** `GAP-LOG-006`

**Response:** A cat is not a reptile.

**Decision:**Y

**Reason:**

---

## 02

**ID:** `GAP-LOG-008`

**Response:** Schedules with no shared time do not overlap.

**Decision:**Y

**Reason:**

---

## 03

**ID:** `GAP-LOG-025`

**Response:** A larger whole divided into equal pieces gives smaller pieces.

**Decision:**Y

**Reason:**

---

## 04

**ID:** `SRC-LOG-014`

**Response:** Low water levels are not high tide.

**Decision:**Y

**Reason:**

---

## 05

**ID:** `GAP-LOG-032`

**Response:** Two equally likely coin outcomes give heads a probability of one half.

**Decision:**Y

**Reason:**

---

## 06

**ID:** `SRC-LOG-012`

**Response:** Processes without light energy are not photosynthesis.

**Decision:**Y

**Reason:**

---

## 07

**ID:** `SRC-LOG-015`

**Response:** Features without survival functions are not adaptations.

**Decision:**Y

**Reason:**

---

## 08

**ID:** `GAP-LOG-021`

**Response:** A ticket dated tomorrow is later than a ticket dated today.

**Decision:**Y

**Reason:**

---

## 09

**ID:** `GAP-LOG-003`

**Response:** A red traffic light signals that cars should stop.

**Decision:**N

**Reason:**这是一条交通规则的事实陈述，没有前提-结论的推导结构，也不涉及条件、排除或比较，主要功能是告知一个约定，而非逻辑推理。

---

## 10

**ID:** `GAP-LOG-038`

**Response:** If Earth's land, air, water, and life interact, change in one part can affect another.

**Decision:**Y

**Reason:**

---
