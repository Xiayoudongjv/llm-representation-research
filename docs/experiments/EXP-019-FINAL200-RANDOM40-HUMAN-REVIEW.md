# EXP-019 Final-200 随机40条人工审核

## 审核方式

对每条进行综合判断，只填写：

* `Y` = 通过
* `N` = 有明显问题
* `?` = 不确定

`Y` 表示综合认为：

1. 当前 task_class 基本合理；
2. 英语至少达到正常、可接受的短回答水平；
3. 句子脱离原始 prompt 后仍能独立理解；
4. 不存在明显的类别歧义。

注意：

* `Y` 不代表句子必须完美；
* 不需要为了措辞不够优美而判 N；
* 不需要进行系统事实查证；
* 如果类别功能明显不清楚，可以填 `?` 或 `N`；
* 不要修改原始 Response；
* 正常样本只写 Decision 即可；
* 只有 N 或 ? 建议写简短备注。

---

## 类别参考

**logic**
前提、条件、规则、排除、比较或关系能够支持某个结论。

**causality**
表达原因产生结果，或描述作用机制。

**analogy**
表达两组事物或关系之间的对应。

**definition**
说明一个概念是什么、属于什么类别、或其定义性功能/属性。

提醒：

* 普通事实陈述不自动等于 logic；
* 带有 `is` 不自动等于 definition；
* 重点判断整句话主要承担什么功能。

---
## 01

**ID:** `SRC-CAU-008`

**Class:** `causality`

**Response:** Chlorophyll absorbs light for photosynthesis.

**Decision:**

**Reason:**

---

## 02

**ID:** `SRC-CAU-012`

**Class:** `causality`

**Response:** Water vapor rises into cooler air and condenses to form cloud droplets.

**Decision:**

**Reason:**

---

## 03

**ID:** `GAP-LOG-007`

**Class:** `logic`

**Response:** A book on the left is not on the right of the cup.

**Decision:**

**Reason:**

---

## 04

**ID:** `GAP-DEF-024`

**Class:** `definition`

**Response:** A cloud is a visible collection of water droplets or ice crystals.

**Decision:**

**Reason:**

---

## 05

**ID:** `GAP-ANA-020`

**Class:** `analogy`

**Response:** A cloud stores condensed water, and a tank stores liquid water.

**Decision:**

**Reason:**

---

## 06

**ID:** `GAP-ANA-013`

**Class:** `analogy`

**Response:** An immune barrier blocks harmful agents, and a fence blocks unwanted entry.

**Decision:**

**Reason:**

---

## 07

**ID:** `GAP-DEF-011`

**Class:** `definition`

**Response:** Probability is a measure of how likely an event is.

**Decision:**

**Reason:**

---

## 08

**ID:** `GAP-LOG-036`

**Class:** `logic`

**Response:** Gravity and pressure can drive groundwater downward or sideways.

**Decision:**

**Reason:**

---

## 09

**ID:** `GAP-ANA-006`

**Class:** `analogy`

**Response:** A pump moves water, and a conveyor moves packages.

**Decision:**

**Reason:**

---

## 10

**ID:** `GAP-LOG-005`

**Class:** `logic`

**Response:** A square has four equal sides.

**Decision:**

**Reason:**

---

## 11

**ID:** `SRC-ANA-014`

**Class:** `analogy`

**Response:** Zero net external force conserves momentum, and isolation keeps total momentum unchanged; the conditions are equivalent.

**Decision:**

**Reason:**

---

## 12

**ID:** `SRC-CAU-004`

**Class:** `causality`

**Response:** External forces cause a change in the total momentum of a system.

**Decision:**

**Reason:**

---

## 13

**ID:** `GAP-CAU-010`

**Class:** `causality`

**Response:** Blocking a light sensor prevents it from detecting light.

**Decision:**

**Reason:**

---

## 14

**ID:** `SRC-DEF-023`

**Class:** `definition`

**Response:** Aquifer is the water-bearing geological layer that stores and transmits available groundwater.

**Decision:**

**Reason:**

---

## 15

**ID:** `GAP-DEF-008`

**Class:** `definition`

**Response:** A lever is a rigid bar that turns around a pivot.

**Decision:**

**Reason:**

---

## 16

**ID:** `GAP-DEF-004`

**Class:** `definition`

**Response:** A polygon is a closed shape made of straight sides.

**Decision:**

**Reason:**

---

## 17

**ID:** `GAP-CAU-005`

**Class:** `causality`

**Response:** Covering a hot pot reduces heat loss.

**Decision:**

**Reason:**

---

## 18

**ID:** `GAP-ANA-007`

**Class:** `analogy`

**Response:** A folder stores files, and a shelf stores books.

**Decision:**

**Reason:**

---

## 19

**ID:** `GAP-LOG-020`

**Class:** `logic`

**Response:** An object inside a smaller box is also inside a larger box around it.

**Decision:**

**Reason:**

---

## 20

**ID:** `SRC-DEF-021`

**Class:** `definition`

**Response:** Adaptability is the biological characteristic that helps organisms survive in their environment.

**Decision:**

**Reason:**

---

## 21

**ID:** `SRC-DEF-022`

**Class:** `definition`

**Response:** Immune system is the body defense system that detects and helps remove harmful substances.

**Decision:**

**Reason:**

---

## 22

**ID:** `GAP-ANA-010`

**Class:** `analogy`

**Response:** A plant stores light energy in carbohydrates, and a battery stores electrical energy for later use.

**Decision:**

**Reason:**

---

## 23

**ID:** `SRC-ANA-004`

**Class:** `analogy`

**Response:** Chlorophyll absorbs light energy for photosynthesis, while solar panels receive sunlight to generate electricity; the principles are similar.

**Decision:**

**Reason:**

---

## 24

**ID:** `SRC-CAU-006`

**Class:** `causality`

**Response:** Photosynthesis absorbs solar energy and can store chemical energy in carbohydrates.

**Decision:**

**Reason:**

---

## 25

**ID:** `GAP-LOG-004`

**Class:** `logic`

**Response:** Dividing an even number by two leaves no remainder.

**Decision:**

**Reason:**

---

## 26

**ID:** `SRC-ANA-022`

**Class:** `analogy`

**Response:** Force changes an object's motion, and heat changes water's solid, liquid, or gas state.

**Decision:**

**Reason:**

---

## 27

**ID:** `SRC-DEF-016`

**Class:** `definition`

**Response:** Satellite precipitation sensor is a remote sensing instrument that measures precipitation information from orbit.

**Decision:**

**Reason:**

---

## 28

**ID:** `GAP-CAU-006`

**Class:** `causality`

**Response:** Moving air speeds evaporation from wet clothes.

**Decision:**

**Reason:**

---

## 29

**ID:** `GAP-CAU-027`

**Class:** `causality`

**Response:** A loose bicycle chain reduces power transfer.

**Decision:**

**Reason:**

---

## 30

**ID:** `GAP-DEF-010`

**Class:** `definition`

**Response:** A map is a representation of places and their relationships.

**Decision:**

**Reason:**

---

## 31

**ID:** `GAP-DEF-003`

**Class:** `definition`

**Response:** A fraction represents part of a whole.

**Decision:**

**Reason:**

---

## 32

**ID:** `GAP-DEF-009`

**Class:** `definition`

**Response:** A variable is a quantity that can change.

**Decision:**

**Reason:**

---

## 33

**ID:** `GAP-CAU-023`

**Class:** `causality`

**Response:** Closing plant stomata reduces water loss.

**Decision:**

**Reason:**

---

## 34

**ID:** `SRC-CAU-011`

**Class:** `causality`

**Response:** Sunlight heats surface water, causing liquid water to evaporate.

**Decision:**

**Reason:**

---

## 35

**ID:** `GAP-CAU-009`

**Class:** `causality`

**Response:** Removing the batteries stops a flashlight.

**Decision:**

**Reason:**

---

## 36

**ID:** `GAP-ANA-015`

**Class:** `analogy`

**Response:** Earth's tilt changes seasonal sunlight, and a dimmer changes lamp brightness.

**Decision:**

**Reason:**

---

## 37

**ID:** `SRC-ANA-012`

**Class:** `analogy`

**Response:** Chloroplasts support photosynthesis, and mesophyll supports gas exchange; both support leaf function.

**Decision:**

**Reason:**

---

## 38

**ID:** `GAP-LOG-016`

**Class:** `logic`

**Response:** A route with no connecting road cannot reach its destination by that route.

**Decision:**

**Reason:**

---

## 39

**ID:** `GAP-DEF-014`

**Class:** `definition`

**Response:** Photosynthesis is a process that converts light energy into chemical energy.

**Decision:**

**Reason:**

---

## 40

**ID:** `GAP-LOG-034`

**Class:** `logic`

**Response:** Without an unbalanced force, constant velocity continues.

**Decision:**

**Reason:**

---

# 审核后汇总

Y：
N：
?：

需要重点说明的问题：

-
-
-
