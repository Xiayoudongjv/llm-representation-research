"""Construct the frozen EXP-019 rule-composed dataset without model calls."""

from __future__ import annotations

import csv
import json
import random
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(__file__).with_name("data")
SEED = 20260812
FIELDS = [
    "example_id", "content_family_id", "task_class", "response_text", "split",
    "provenance", "length_tokens", "length_band", "template_family",
    "paraphrase_family_id", "lexical_challenge", "notes",
]

TOPICS = [
    ("kitchen timer", "the countdown reaches zero", "the bell rings", "measures a chosen time interval", "a kettle", "boils", "whistle"),
    ("rain gauge", "rain fills its collector", "the recorded level rises", "measures rainfall amount", "a fuel gauge", "fuel enters", "level rises"),
    ("bicycle light", "the switch closes", "the lamp shines", "provides light for cycling", "a desk lamp", "power arrives", "lamp shines"),
    ("thermometer", "warm air reaches its sensor", "the reading increases", "measures temperature", "a speedometer", "speed increases", "needle rises"),
    ("paper filter", "water passes through its fibers", "small particles remain behind", "separates particles from liquid", "a screen door", "air passes", "insects remain outside"),
    ("seed tray", "moist soil surrounds a seed", "the seed begins to sprout", "holds seeds for early growth", "a sponge", "water reaches it", "it expands"),
    ("traffic signal", "the green light appears", "cars may proceed", "controls movement at an intersection", "a classroom bell", "the bell rings", "students change activity"),
    ("refrigerator", "warm food enters the cabinet", "the cooling system removes heat", "keeps food cold", "an insulated bottle", "ice is added", "the drink stays cool"),
    ("door lock", "the correct key turns", "the latch withdraws", "secures a doorway", "a password screen", "the right code enters", "access opens"),
    ("compass", "its needle aligns north", "a traveler can choose direction", "shows magnetic direction", "a weather vane", "wind changes", "the pointer turns"),
    ("ruler", "one end aligns with an object", "its length can be read", "measures straight distance", "a measuring cup", "liquid reaches a mark", "volume is read"),
    ("watering can", "water pours onto dry soil", "the soil becomes moist", "delivers water to plants", "a soap dispenser", "its pump is pressed", "soap appears"),
    ("solar panel", "sunlight reaches its cells", "electric current is produced", "converts sunlight into electricity", "a windmill", "wind turns blades", "motion is produced"),
    ("pencil sharpener", "a pencil turns against its blade", "wood is removed", "forms a pointed pencil tip", "a cheese grater", "cheese moves across holes", "small pieces form"),
    ("thermos", "a hot drink enters its insulated wall", "heat escapes slowly", "keeps a drink near its starting temperature", "a winter coat", "body heat reaches it", "warmth escapes slowly"),
    ("calendar", "a day passes", "the displayed date changes", "organizes dates", "an odometer", "distance accumulates", "the number changes"),
    ("pulley", "a rope is pulled downward", "a load rises", "changes the direction of a pulling force", "a lever", "one end is pressed", "the other end rises"),
    ("magnet", "iron moves near it", "the iron is pulled closer", "attracts some metal objects", "a vacuum", "dust moves near it", "dust is pulled inside"),
    ("ice cube", "warm water surrounds it", "the cube melts", "a solid piece of frozen water", "a candle", "heat reaches wax", "wax melts"),
]


def length_band(family_number: int) -> str:
    return ("short", "medium", "limited_long")[family_number % 3]


def response(topic, task_class: str, band: str, family_number: int, challenge: bool) -> tuple[str, str]:
    name, condition, result, definition, analog_name, analog_condition, analog_result = topic
    variant = family_number % 5
    label = name.split()[-1]
    analog_label = analog_name.split()[-1]
    outcome = result.split()[-1].rstrip(".")
    modifier = ("routine", "nearby", "observed", "ordinary", "shared", "familiar", "simple", "daily", "local", "practical")[(family_number - 1) // len(TOPICS)]
    if task_class == "logic":
        templates = {
            "short": [f"{modifier.capitalize()} {label} entails {outcome}.", f"{modifier.capitalize()} {label} condition entails {outcome}."],
            "medium": [f"If the {modifier} {label} condition holds, {outcome} follows under the rule.", f"The {modifier} {label} condition holds, so {outcome} follows."],
            "limited_long": [f"When the {modifier} {label} condition holds, the stated rule requires {outcome} as its conclusion."],
        }
        family = f"logic_{band}_{variant}"
    elif task_class == "causality":
        templates = {
            "short": [f"{modifier.capitalize()} {label} triggers {outcome}.", f"{modifier.capitalize()} {label} state yields outcome."],
            "medium": [f"The {modifier} {label} condition produces {outcome} through a simple mechanism.", f"{outcome.capitalize()} follows when the {modifier} {label} mechanism activates."],
            "limited_long": [f"A change in the {modifier} {label} condition leads to {outcome} through the system's ordinary mechanism."],
        }
        family = f"causality_{band}_{variant}"
    elif task_class == "analogy":
        templates = {
            "short": [f"{modifier.capitalize()} {label} parallels {analog_label}.", f"{modifier.capitalize()} {label} mirrors {analog_label}'s relation."],
            "medium": [f"The {modifier} {label} relation matches the {analog_label} relation in structure.", f"Like the {analog_label}, the {modifier} {label} connects condition and outcome."],
            "limited_long": [f"The {modifier} {label} relation corresponds to the {analog_label} relation because both connect a condition with an outcome."],
        }
        family = f"analogy_{band}_{variant}"
    else:
        templates = {
            "short": [f"A {modifier} {label} has purpose.", f"{modifier.capitalize()} {label} denotes purpose."],
            "medium": [f"A {modifier} {label} is an object with a stated practical role.", f"The {modifier} {label} refers to an object used for a purpose."],
            "limited_long": [f"A {modifier} {label} is a familiar object whose role is described by its practical use in a system."],
        }
        family = f"definition_{band}_{variant}"
    text = templates[band][variant % len(templates[band])]
    if challenge:
        text = text.replace("therefore", "so").replace("because", "as a result")
    return text, family


def build_rows() -> list[dict[str, str]]:
    family_ids = [f"cf_{number:03d}" for number in range(1, 191)]
    random.Random(SEED).shuffle(family_ids)
    splits = {family_id: "train" for family_id in family_ids[:120]}
    splits.update({family_id: "validation" for family_id in family_ids[120:150]})
    splits.update({family_id: "test" for family_id in family_ids[150:]})
    rows = []
    for number, family_id in enumerate(sorted(family_ids), start=1):
        topic = TOPICS[(number - 1) % len(TOPICS)]
        band = length_band(number)
        challenge = number <= 20
        for task_class in ("logic", "causality", "analogy", "definition"):
            text, template = response(topic, task_class, band, number, challenge)
            rows.append({
                "example_id": f"exp019_{task_class}_{number:03d}",
                "content_family_id": family_id,
                "task_class": task_class,
                "response_text": text,
                "split": splits[family_id],
                "provenance": "rule_composed",
                "length_tokens": str(len(text.rstrip(".").replace(":", " ").split())),
                "length_band": band,
                "template_family": template,
                "paraphrase_family_id": family_id,
                "lexical_challenge": str(challenge).lower(),
                "notes": "label_quality=clear; constructed from a balanced content family",
            })
    return rows


def main() -> None:
    """Write only rule-composed dataset artifacts; no model or classifier is used."""
    rows = build_rows()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dataset_path = DATA_DIR / "behavioral_targetness_dataset.csv"
    with dataset_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with (DATA_DIR / "rejected_candidates.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["candidate_id", "proposed_class", "response_text", "reason_rejected"])
        writer.writeheader()
    summary = {
        "total_examples": len(rows),
        "examples_per_class": dict(Counter(row["task_class"] for row in rows)),
        "examples_per_split": dict(Counter(row["split"] for row in rows)),
        "content_family_count": len({row["content_family_id"] for row in rows}),
        "families_per_split": dict(Counter(splits for splits in {row["content_family_id"]: row["split"] for row in rows}.values())),
        "length_band_by_class": {task: dict(Counter(row["length_band"] for row in rows if row["task_class"] == task)) for task in ("logic", "causality", "analogy", "definition")},
        "provenance_by_class": {task: dict(Counter(row["provenance"] for row in rows if row["task_class"] == task)) for task in ("logic", "causality", "analogy", "definition")},
        "template_family_counts": dict(Counter(row["template_family"] for row in rows)),
        "lexical_challenge_counts": {task: sum(row["lexical_challenge"] == "true" for row in rows if row["task_class"] == task) for task in ("logic", "causality", "analogy", "definition")},
        "rejected_candidate_count": 0,
        "construction": "deterministic rule_composed templates; no Qwen, Gemma, steering output, model generation, or classifier training",
        "seed": SEED,
    }
    (DATA_DIR / "dataset_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    sample = list(rows)
    random.Random(SEED).shuffle(sample)
    with (DATA_DIR / "manual_audit_sample.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["example_id", "task_class", "response_text", "length_band", "provenance"])
        writer.writeheader()
        writer.writerows([{key: row[key] for key in writer.fieldnames} for row in sample[:76]])
    print(f"constructed_rows={len(rows)}")


if __name__ == "__main__":
    main()
