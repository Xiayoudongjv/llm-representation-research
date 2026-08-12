# EXP-019 Final-200 Similarity Review

This compact packet contains only mechanically flagged pairs or repeated-prefix groups.

`Y` = distinct enough; `N` = substantially redundant; `?` = uncertain.

All Decision and Reason fields are intentionally blank.

## 01 - repeated three-word prefix

**ID A:** `GAP-ANA-018`

**Text A:** A food web links feeding relationships, and a transit map links travel routes.

**ID B:** `GAP-DEF-016`

**Text B:** A food web represents feeding relationships in an ecosystem.

**Flag type:** repeated three-word prefix (`a food web`)

**Decision:**Y

**Reason:**

---

## 02 - repeated three-word prefix

**ID A:** `GAP-ANA-005`

**Text A:** A thermostat regulates temperature, and a traffic signal regulates movement.

**ID B:** `GAP-ANA-024`

**Text B:** A thermostat regulates room temperature, and a metronome regulates timing.

**Flag type:** repeated three-word prefix (`a thermostat regulates`)

**Decision:**Y

**Reason:**

---

## 03 - repeated three-word prefix

**ID A:** `SRC-CAU-008`

**Text A:** Chlorophyll absorbs light for photosynthesis.

**ID B:** `SRC-ANA-004`

**Text B:** Chlorophyll absorbs light energy for photosynthesis, while solar panels receive sunlight to generate electricity; the principles are similar.

**Flag type:** repeated three-word prefix (`chlorophyll absorbs light`)

**Decision:**Y

**Reason:**

---

## 04 - repeated three-word prefix

**ID A:** `GAP-CAU-012`

**Text A:** Earth's tilt changes seasonal sunlight exposure.

**ID B:** `GAP-ANA-015`

**Text B:** Earth's tilt changes seasonal sunlight, and a dimmer changes lamp brightness.

**Flag type:** repeated three-word prefix (`earth's tilt changes`)

**Decision:**Y

**Reason:**

---

## 05 - repeated three-word prefix

**ID A:** `SRC-DEF-002`

**Text A:** Evaporation is the phase change that turns liquid water into water vapor.

**ID B:** `GAP-DEF-025`

**Text B:** Evaporation is the change of liquid water into vapor.

**Flag type:** repeated three-word prefix (`evaporation is the`)

**Decision:**N

**Reason:**两句几乎完全同义（蒸发是液态水变为水蒸气），仅措辞微差。

---

## 06 - repeated three-word prefix

**ID A:** `GAP-CAU-001`

**Text A:** Friction slows a rolling ball on the floor.

**ID B:** `GAP-ANA-023`

**Text B:** Friction slows a wheel, and a brake slows a bicycle.

**Flag type:** repeated three-word prefix (`friction slows a`)

**Decision:**Y

**Reason:**

---

## 07 - repeated three-word prefix

**ID A:** `SRC-DEF-003`

**Text A:** Photosynthesis is a biological energy process that uses light energy to help synthesize carbohydrates.

**ID B:** `GAP-DEF-014`

**Text B:** Photosynthesis is a process that converts light energy into chemical energy.

**Flag type:** repeated three-word prefix (`photosynthesis is a`)

**Decision:**Y

**Reason:**

---

## 08 - repeated three-word prefix

**ID A:** `SRC-ANA-025`

**Text A:** The immune system forms barriers against bacteria, while fences block foreign substances; both protect against intrusion.

**ID B:** `GAP-DEF-019`

**Text B:** The immune system is a group of cells, tissues, and organs that protects the body.

**Flag type:** repeated three-word prefix (`the immune system`)

**Decision:**Y

**Reason:**

---

## 09 - char TF-IDF similarity

**ID A:** `SRC-CAU-006`

**Text A:** Photosynthesis absorbs solar energy and can store chemical energy in carbohydrates.

**ID B:** `GAP-CAU-014`

**Text B:** Photosynthesis stores solar energy in carbohydrates.

**Flag type:** char TF-IDF cosine >= 0.55

**Similarity score:** 0.6939

**Decision:**N

**Reason:**B 是 A 的简化版本，核心信息完全相同（光合作用将太阳能储存在碳水化合物中）。



---

## 10 - char TF-IDF similarity

**ID A:** `SRC-CAU-009`

**Text A:** Closing stomata reduces water loss in plants.

**ID B:** `GAP-CAU-023`

**Text B:** Closing plant stomata reduces water loss.

**Flag type:** char TF-IDF cosine >= 0.55

**Similarity score:** 0.7506

**Decision:**N

**Reason:**两句完全同义（关闭气孔减少水分损失），仅词序微调。



---

## 11 - char TF-IDF similarity

**ID A:** `SRC-DEF-002`

**Text A:** Evaporation is the phase change that turns liquid water into water vapor.

**ID B:** `GAP-DEF-025`

**Text B:** Evaporation is the change of liquid water into vapor.

**Flag type:** char TF-IDF cosine >= 0.55

**Similarity score:** 0.6370

**Decision:**N

**Reason:**与 #05 相同，实质重复。

---

## 12 - char TF-IDF similarity

**ID A:** `SRC-DEF-009`

**Text A:** Force is the physical interaction that can change motion.

**ID B:** `GAP-DEF-012`

**Text B:** A force is an interaction that can change motion.

**Flag type:** char TF-IDF cosine >= 0.55

**Similarity score:** 0.7687

**Decision:**N

**Reason:**两句关于力的定义几乎完全一致（力是能改变运动的相互作用）。

---

## 13 - char TF-IDF similarity

**ID A:** `GAP-LOG-027`

**Text A:** If photosynthesis stores energy in carbohydrates, those molecules contain captured energy.

**ID B:** `GAP-CAU-014`

**Text B:** Photosynthesis stores solar energy in carbohydrates.

**Flag type:** char TF-IDF cosine >= 0.55

**Similarity score:** 0.5674

**Decision:**Y

**Reason:**

---

## 14 - char TF-IDF similarity

**ID A:** `GAP-LOG-033`

**Text A:** If an unbalanced force acts, an object's velocity can change.

**ID B:** `GAP-CAU-017`

**Text B:** An unbalanced force changes an object's velocity.

**Flag type:** char TF-IDF cosine >= 0.55

**Similarity score:** 0.7512

**Decision:**N

**Reason:**A 的条件句与 B 的直陈句核心关系相同（不平衡力改变速度），实质重复

---

## 15 - char TF-IDF similarity

**ID A:** `GAP-CAU-012`

**Text A:** Earth's tilt changes seasonal sunlight exposure.

**ID B:** `GAP-ANA-015`

**Text B:** Earth's tilt changes seasonal sunlight, and a dimmer changes lamp brightness.

**Flag type:** char TF-IDF cosine >= 0.55

**Similarity score:** 0.6123

**Decision:**Y

**Reason:**

---

## 16 - char TF-IDF similarity

**ID A:** `GAP-ANA-005`

**Text A:** A thermostat regulates temperature, and a traffic signal regulates movement.

**ID B:** `GAP-ANA-024`

**Text B:** A thermostat regulates room temperature, and a metronome regulates timing.

**Flag type:** char TF-IDF cosine >= 0.55

**Similarity score:** 0.6572

**Decision:**Y

**Reason:**

---
