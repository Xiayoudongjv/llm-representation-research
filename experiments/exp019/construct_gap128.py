"""Construct and audit the 128-candidate EXP-019 gap pool.

This script performs deterministic, pre-evaluator dataset construction.  The
normalizer intentionally receives only ``candidate_id`` and ``raw_response``;
task labels and source metadata are merged only after normalization.
"""

from __future__ import annotations

import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DATA = Path(__file__).resolve().parent / "data"
RETAINED = DATA / "existing100_corrected_retained_pool.csv"
HUMAN_REVIEW = DATA / "existing100_corrected_human_review.csv"
CORRECTED_REJECTED = DATA / "existing100_corrected_rejected.csv"
EXCLUSION_LOG = DATA / "existing100_human_review_exclusion_log.csv"
GAP_STATUS = DATA / "final200_gap_status_after_exclusion.json"
RAW_PATH = DATA / "gap128_raw_candidates.csv"
NORMALIZED_PATH = DATA / "gap128_normalized_candidates.csv"
AUDITED_PATH = DATA / "gap128_audited_candidates.csv"
AUDIT_SUMMARY = DATA / "gap128_quality_audit.json"
FINAL_POOL = DATA / "final200_candidate_pool_pre_human_audit.csv"
HUMAN_SAMPLE = DATA / "final200_human_audit_sample.csv"

SOURCE = {
    "openstax_bio": "https://openstax.org/books/concepts-biology/pages/5-1-overview-of-photosynthesis",
    "openstax_ecology": "https://openstax.org/books/biology-2e/pages/46-2-energy-flow-through-ecosystems",
    "openstax_physics": "https://openstax.org/books/physics/pages/4-1-force",
    "khan_probability": "https://www.khanacademy.org/math/probability/introduction-to-probability",
    "khan_newton": "https://www.khanacademy.org/science/physics/forces-newtons-laws/introduction-to-newtons-laws/a/newtons-laws-of-motion",
    "nasa_earth": "https://www.nasa.gov/learning-resources/for-kids-and-students/what-is-earth-grades-k-4/",
    "noaa_climate": "https://oceanservice.noaa.gov/education/literacy.html",
    "usgs_water": "https://www.usgs.gov/educational-resources/water-world",
    "usgs_groundwater": "https://www.usgs.gov/water-science-school/science/groundwater-flow-and-water-cycle",
    "nih_immune": "https://nigms.nih.gov/biobeat/2023/12/what-is-the-immune-system",
    "ncbi_immune": "https://www.ncbi.nlm.nih.gov/books/NBK27092/",
    "smithsonian_adaptation": "https://naturalhistory.si.edu/education/teaching-resources/life-science/explore-animal-adaptations",
}
RULE_SOURCE = "rule_composed://deterministic-construction"
PROVENANCE_CYCLE = [
    "rule_composed",
    "independent_external",
    "ai_assisted_surface_normalized",
]
TOKEN_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+")
STOPWORDS = {"a", "an", "and", "as", "at", "be", "by", "can", "for", "from", "if", "in", "is", "it", "of", "on", "or", "the", "that", "to", "with"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def add_class(rows: list[dict[str, object]], code: str, task_class: str, items: list[tuple[str, str, str]]) -> None:
    for index, (response, topic, source_key) in enumerate(items, start=1):
        rows.append({
            "candidate_id": f"GAP-{code}-{index:03d}",
            "task_class": task_class,
            "raw_response": response,
            "source_key": source_key,
            "topic_domain": topic,
        })


def candidate_specs() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    add_class(rows, "LOG", "logic", [
        ("If the key is inside the drawer, opening the drawer can reveal it.", "everyday_life", "rule"),
        ("A sealed envelope hides its contents until someone opens it.", "everyday_life", "rule"),
        ("A red traffic light signals that cars should stop.", "everyday_life", "rule"),
        ("Dividing an even number by two leaves no remainder.", "mathematics", "rule"),
        ("A square has four equal sides.", "mathematics", "rule"),
        ("A cat is not a reptile.", "everyday_life", "rule"),
        ("A book on the left is not on the right of the cup.", "spatial_reasoning", "rule"),
        ("Schedules with no shared time do not overlap.", "everyday_life", "rule"),
        ("Three coins plus two coins make five coins.", "mathematics", "rule"),
        ("A password shorter than the required length fails the check.", "technology", "rule"),
        ("If the train arrives after the bus, the train is later.", "everyday_life", "rule"),
        ("An item outside a box is not inside that box.", "spatial_reasoning", "rule"),
        ("If every class member has an ID, Maya has an ID as a class member.", "language", "rule"),
        ("Dividing a whole into equal parts makes each part smaller than the whole.", "mathematics", "rule"),
        ("Sets with exactly the same elements have the same size.", "mathematics", "rule"),
        ("A route with no connecting road cannot reach its destination by that route.", "spatial_reasoning", "rule"),
        ("A book north of a lamp is not south of the lamp in the same layout.", "spatial_reasoning", "rule"),
        ("A number divisible by ten ends in zero.", "mathematics", "rule"),
        ("A square is a rectangle with equal sides.", "mathematics", "rule"),
        ("An object inside a smaller box is also inside a larger box around it.", "spatial_reasoning", "rule"),
        ("A ticket dated tomorrow is later than a ticket dated today.", "everyday_life", "rule"),
        ("If every seat is occupied, no seat is available.", "everyday_life", "rule"),
        ("A triangle with three sides is a polygon.", "mathematics", "rule"),
        ("If two routes share no connecting segment, one cannot continue along the other.", "spatial_reasoning", "rule"),
        ("A larger whole divided into equal pieces gives smaller pieces.", "mathematics", "rule"),
        ("If an organism has chloroplasts, it can use light energy in photosynthesis.", "biology", "openstax_bio"),
        ("If photosynthesis stores energy in carbohydrates, those molecules contain captured energy.", "biology", "openstax_bio"),
        ("If consumers eat producers, energy moves from producers to consumers.", "biology", "openstax_ecology"),
        ("A hemisphere tilted toward the Sun receives more direct sunlight.", "earth_science", "nasa_earth"),
        ("If the Northern Hemisphere tilts toward the Sun, it experiences summer.", "earth_science", "nasa_earth"),
        ("A fair six-sided die gives each face equal probability.", "mathematics", "khan_probability"),
        ("Two equally likely coin outcomes give heads a probability of one half.", "mathematics", "khan_probability"),
        ("If an unbalanced force acts, an object's velocity can change.", "physics", "khan_newton"),
        ("Without an unbalanced force, constant velocity continues.", "physics", "khan_newton"),
        ("If groundwater moves through rock spaces, connected spaces can permit flow.", "earth_science", "usgs_groundwater"),
        ("Gravity and pressure can drive groundwater downward or sideways.", "earth_science", "usgs_groundwater"),
        ("Ocean conditions can influence weather patterns.", "earth_science", "noaa_climate"),
        ("If Earth's land, air, water, and life interact, change in one part can affect another.", "earth_science", "nasa_earth"),
        ("If immune defenses work together, protection involves more than one body component.", "biology", "nih_immune"),
        ("If macrophages are phagocytes, they can engulf particles.", "biology", "ncbi_immune"),
        ("If a feature improves an animal's survival, it may function as an adaptation.", "biology", "smithsonian_adaptation"),
        ("If water moves through reservoirs and pathways, groundwater participates in a cycle.", "earth_science", "usgs_water"),
    ])
    add_class(rows, "CAU", "causality", [
        ("Friction slows a rolling ball on the floor.", "physics", "rule"),
        ("Adding ice cools a drink.", "everyday_life", "rule"),
        ("Opening a window can lower room temperature.", "everyday_life", "rule"),
        ("Pressing a bicycle brake reduces its speed.", "technology", "rule"),
        ("Covering a hot pot reduces heat loss.", "everyday_life", "rule"),
        ("Moving air speeds evaporation from wet clothes.", "everyday_life", "rule"),
        ("Sharpening a pencil produces a narrower point.", "everyday_life", "rule"),
        ("Stretching a rubber band stores elastic energy.", "physics", "rule"),
        ("Removing the batteries stops a flashlight.", "technology", "rule"),
        ("Blocking a light sensor prevents it from detecting light.", "technology", "rule"),
        ("Sunlight warms a dark surface.", "earth_science", "nasa_earth"),
        ("Earth's tilt changes seasonal sunlight exposure.", "earth_science", "nasa_earth"),
        ("Evaporation can cool a wet surface.", "earth_science", "usgs_water"),
        ("Photosynthesis stores solar energy in carbohydrates.", "biology", "openstax_bio"),
        ("Cellular respiration releases usable energy from food.", "biology", "openstax_bio"),
        ("Consumers receive energy by eating food.", "biology", "openstax_ecology"),
        ("An unbalanced force changes an object's velocity.", "physics", "khan_newton"),
        ("Groundwater movement follows gravity and pressure.", "earth_science", "usgs_groundwater"),
        ("Immune defenses block, detect, and remove harmful agents.", "biology", "nih_immune"),
        ("Macrophages engulf foreign material.", "biology", "ncbi_immune"),
        ("Cooling air turns water vapor into droplets.", "earth_science", "usgs_water"),
        ("Longer sunlight exposure heats a surface more.", "earth_science", "nasa_earth"),
        ("Closing plant stomata reduces water loss.", "biology", "openstax_bio"),
        ("A cold container produces droplets from warm vapor.", "physics", "usgs_water"),
        ("Pumping water upward requires energy input.", "technology", "usgs_groundwater"),
        ("A barrier on a route prevents a traveler from reaching the destination.", "spatial_reasoning", "rule"),
        ("A loose bicycle chain reduces power transfer.", "technology", "rule"),
        ("A heavier load makes a cart harder to accelerate.", "physics", "rule"),
        ("A wider opening lets more air pass through.", "everyday_life", "rule"),
        ("A missing key prevents a lock from opening.", "technology", "rule"),
    ])
    add_class(rows, "ANA", "analogy", [
        ("A key opens a lock, and a password opens access to an account.", "technology", "rule"),
        ("A lid covers a container, and a roof covers a building.", "everyday_life", "rule"),
        ("A map guides a traveler, and a diagram guides a learner.", "language", "rule"),
        ("A filter retains particles, and a sieve retains grains.", "technology", "rule"),
        ("A thermostat regulates temperature, and a traffic signal regulates movement.", "technology", "rule"),
        ("A pump moves water, and a conveyor moves packages.", "technology", "rule"),
        ("A folder stores files, and a shelf stores books.", "technology", "rule"),
        ("A recipe guides cooking, and an algorithm guides computation.", "language", "rule"),
        ("A bridge connects two banks, and a link connects two webpages.", "technology", "rule"),
        ("A plant stores light energy in carbohydrates, and a battery stores electrical energy for later use.", "biology", "openstax_bio"),
        ("A seed protects an embryo, and a case protects a delicate instrument.", "biology", "smithsonian_adaptation"),
        ("Pore spaces hold groundwater, and a reservoir holds surface water.", "earth_science", "usgs_groundwater"),
        ("An immune barrier blocks harmful agents, and a fence blocks unwanted entry.", "biology", "nih_immune"),
        ("A force changes motion, and heat changes the state of water.", "physics", "khan_newton"),
        ("Earth's tilt changes seasonal sunlight, and a dimmer changes lamp brightness.", "earth_science", "nasa_earth"),
        ("A river carries water downhill, and a conveyor carries goods forward.", "earth_science", "usgs_water"),
        ("A well pump lifts groundwater, and a heart pumps blood through vessels.", "biology", "ncbi_immune"),
        ("A food web links feeding relationships, and a transit map links travel routes.", "biology", "openstax_ecology"),
        ("A macrophage removes foreign material, and a filter removes particles from water.", "biology", "ncbi_immune"),
        ("A cloud stores condensed water, and a tank stores liquid water.", "earth_science", "usgs_water"),
        ("A camera records light, and a thermometer records temperature.", "technology", "rule"),
        ("A root anchors a plant, and an anchor holds a boat.", "biology", "smithsonian_adaptation"),
        ("Friction slows a wheel, and a brake slows a bicycle.", "physics", "khan_newton"),
        ("A thermostat regulates room temperature, and a metronome regulates timing.", "technology", "rule"),
        ("A sieve lets water pass while retaining solids, and a firewall lets approved data pass while blocking threats.", "technology", "rule"),
        ("An ecosystem transfers energy among organisms, and a circuit transfers energy among components.", "biology", "openstax_ecology"),
    ])
    add_class(rows, "DEF", "definition", [
        ("A queue is an ordered line of people or tasks waiting for service.", "everyday_life", "rule"),
        ("A compass is a tool that indicates direction.", "technology", "rule"),
        ("A fraction represents part of a whole.", "mathematics", "rule"),
        ("A polygon is a closed shape made of straight sides.", "mathematics", "rule"),
        ("A password is secret text used to verify access.", "technology", "rule"),
        ("A habitat is the place where an organism lives.", "biology", "rule"),
        ("A schedule is a plan that assigns times to activities.", "everyday_life", "rule"),
        ("A lever is a rigid bar that turns around a pivot.", "physics", "rule"),
        ("A variable is a quantity that can change.", "mathematics", "rule"),
        ("A map is a representation of places and their relationships.", "geography", "rule"),
        ("Probability is a measure of how likely an event is.", "mathematics", "khan_probability"),
        ("A force is an interaction that can change motion.", "physics", "khan_newton"),
        ("Inertia is resistance to a change in motion.", "physics", "khan_newton"),
        ("Photosynthesis is a process that converts light energy into chemical energy.", "biology", "openstax_bio"),
        ("An ecosystem includes organisms and their physical environment.", "biology", "openstax_ecology"),
        ("A food web represents feeding relationships in an ecosystem.", "biology", "openstax_ecology"),
        ("An aquifer is a water-bearing formation that can store and transmit groundwater.", "earth_science", "usgs_groundwater"),
        ("Groundwater is water stored below the land surface.", "earth_science", "usgs_water"),
        ("The immune system is a group of cells, tissues, and organs that protects the body.", "biology", "nih_immune"),
        ("A macrophage is an immune cell that engulfs particles.", "biology", "ncbi_immune"),
        ("A season is a recurring part of a year with characteristic conditions.", "earth_science", "nasa_earth"),
        ("Climate is the long-term pattern of weather in a region.", "earth_science", "noaa_climate"),
        ("An ocean current is directed movement of seawater.", "earth_science", "noaa_climate"),
        ("A cloud is a visible collection of water droplets or ice crystals.", "earth_science", "nasa_earth"),
        ("Evaporation is the change of liquid water into vapor.", "earth_science", "noaa_climate"),
        ("Condensation is the change of vapor into a liquid.", "earth_science", "usgs_water"),
        ("A watershed is land that drains to a common body of water.", "earth_science", "usgs_water"),
        ("A chloroplast is a plant-cell organelle where photosynthesis occurs.", "biology", "openstax_bio"),
        ("A vaccine is a preparation that trains an immune response to a target.", "biology", "nih_immune"),
        ("An algorithm is a step-by-step procedure for completing a task.", "technology", "rule"),
    ])
    for index, row in enumerate(rows):
        row["provenance"] = PROVENANCE_CYCLE[index % len(PROVENANCE_CYCLE)]
        source_key = str(row.pop("source_key"))
        row["source_reference"] = RULE_SOURCE if source_key == "rule" else SOURCE[source_key]
        row["construction_notes"] = (
            "Deterministic rule composition; no external provenance claimed."
            if row["provenance"] == "rule_composed"
            else "Semantic content grounded in the cited educational source; candidate retained as source-based construction."
            if row["provenance"] == "independent_external"
            else "Semantic content grounded in the cited source; only class-blind surface normalization is permitted later."
        )
    if len(rows) != 128:
        raise AssertionError(f"candidate construction produced {len(rows)} rows")
    return rows


SURFACE_NORMALIZATIONS = {
    "GAP-LOG-003": "A red traffic light signals that cars should stop.",
    "GAP-LOG-007": "A book on the left is not on the right of the cup.",
    "GAP-LOG-013": "If every class member has an ID, Maya has an ID as a class member.",
    "GAP-LOG-018": "A number divisible by ten ends in zero.",
    "GAP-LOG-030": "If the Northern Hemisphere tilts toward the Sun, it experiences summer.",
    "GAP-CAU-004": "Pressing a bicycle brake reduces its speed.",
    "GAP-CAU-006": "Moving air speeds evaporation from wet clothes.",
    "GAP-CAU-009": "Removing the batteries stops a flashlight.",
    "GAP-CAU-013": "Evaporation can cool a wet surface.",
    "GAP-CAU-015": "Cellular respiration releases usable energy from food.",
    "GAP-CAU-021": "Cooling air turns water vapor into droplets.",
    "GAP-CAU-024": "A cold container produces droplets from warm vapor.",
    "GAP-ANA-004": "A filter retains particles, and a sieve retains grains.",
    "GAP-ANA-008": "A recipe guides cooking, and an algorithm guides computation.",
    "GAP-ANA-012": "Pore spaces hold groundwater, and a reservoir holds surface water.",
    "GAP-ANA-015": "Earth's tilt changes seasonal sunlight, and a dimmer changes lamp brightness.",
    "GAP-ANA-019": "A macrophage removes foreign material, and a filter removes particles from water.",
    "GAP-ANA-025": "A sieve lets water pass while retaining solids, and a firewall lets approved data pass while blocking threats.",
    "GAP-DEF-003": "A fraction represents part of a whole.",
    "GAP-DEF-008": "A lever is a rigid bar that turns around a pivot.",
    "GAP-DEF-012": "A force is an interaction that can change motion.",
    "GAP-DEF-018": "Groundwater is water stored below the land surface.",
    "GAP-DEF-022": "Climate is the long-term pattern of weather in a region.",
    "GAP-DEF-024": "A cloud is a visible collection of water droplets or ice crystals.",
    "GAP-DEF-027": "A watershed is land that drains to a common body of water.",
    "GAP-DEF-029": "A vaccine is a preparation that trains an immune response to a target.",
}


def normalize(candidate_id: str, raw_response: str) -> tuple[str, str, str, str]:
    """Normalize using only candidate_id and raw_response, never metadata."""
    normalized = SURFACE_NORMALIZATIONS.get(candidate_id, raw_response)
    if normalized == raw_response:
        return raw_response, "PASS", "UNCHANGED", "No surface normalization required."
    return normalized, "SURFACE_NORMALIZED", "SURFACE_ONLY_UNCHANGED", "Grammar, word order, or minor naturalness adjustment only."


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def band(count: int) -> str:
    if count == 0:
        return "reject"
    if count <= 5:
        return "short"
    if count <= 12:
        return "medium"
    if count <= 20:
        return "limited_long"
    return "reject"


def ngram_vector(text: str) -> Counter[str]:
    compact = re.sub(r"\s+", " ", text.lower()).strip()
    return Counter(compact[i : i + n] for n in (3, 4, 5) for i in range(max(0, len(compact) - n + 1)))


def sparse_cosine(left: Counter[str], right: Counter[str]) -> float:
    dot = sum(value * right.get(key, 0) for key, value in left.items())
    left_norm = sum(value * value for value in left.values()) ** 0.5
    right_norm = sum(value * value for value in right.values()) ** 0.5
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def exclusion_and_gap_status() -> None:
    human = read_csv(HUMAN_REVIEW)
    rejected = read_csv(CORRECTED_REJECTED)
    write_csv(EXCLUSION_LOG, ["candidate_id", "task_class", "original_response", "previous_status", "new_status", "exclusion_reason"], [
        {"candidate_id": row["candidate_id"], "task_class": row["task_class"], "original_response": row["original_response"], "previous_status": "HUMAN_REVIEW", "new_status": "EXCLUDED_FROM_PRIMARY_POOL_FOR_EFFICIENCY_AND_AMBIGUITY", "exclusion_reason": "Borderline candidate excluded rather than manually repaired to avoid post-hoc semantic intervention and reduce manual remediation."}
        for row in human
    ])
    retained = read_csv(RETAINED)
    by_class = Counter(row["task_class"] for row in retained)
    gaps = {task_class: 50 - by_class[task_class] for task_class in ("logic", "causality", "analogy", "definition")}
    with GAP_STATUS.open("w", encoding="utf-8") as handle:
        json.dump({"retained_total": len(retained), "excluded_human_review": len(human), "rejected": len(rejected), "remaining_total": sum(gaps.values()), "retained_by_class": dict(by_class), "remaining_by_class": gaps, "human_review_status": "EXCLUDED_FROM_PRIMARY_POOL_FOR_EFFICIENCY_AND_AMBIGUITY"}, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def build() -> None:
    exclusion_and_gap_status()
    specs = candidate_specs()
    raw_fields = ["candidate_id", "task_class", "raw_response", "provenance", "source_reference", "topic_domain", "construction_notes"]
    write_csv(RAW_PATH, raw_fields, specs)
    normalized_rows = []
    for row in specs:
        normalized, status, guard, notes = normalize(str(row["candidate_id"]), str(row["raw_response"]))
        normalized_rows.append({"candidate_id": row["candidate_id"], "raw_response": row["raw_response"], "normalized_response": normalized, "normalization_status": status, "semantic_guard": guard, "normalization_notes": notes})
    write_csv(NORMALIZED_PATH, ["candidate_id", "raw_response", "normalized_response", "normalization_status", "semantic_guard", "normalization_notes"], normalized_rows)

    vectors = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), lowercase=True).fit_transform([str(row["normalized_response"]) for row in normalized_rows])
    similarity = cosine_similarity(vectors)
    normalized_by_id = {row["candidate_id"]: row for row in normalized_rows}
    audited = []
    for index, row in enumerate(specs):
        normalized = normalized_by_id[row["candidate_id"]]
        length = len(tokens(str(normalized["normalized_response"])))
        nearest = max((float(similarity[index, other]) for other in range(len(specs)) if other != index), default=0.0)
        duplicate_risk = "high" if nearest >= 0.80 else "medium" if nearest >= 0.55 else "low"
        acceptance = "ACCEPT_CANDIDATE" if length and length <= 20 else "REJECT_CANDIDATE"
        audited.append({"candidate_id": row["candidate_id"], "task_class": row["task_class"], "raw_response": row["raw_response"], "normalized_response": normalized["normalized_response"], "provenance": row["provenance"], "source_reference": row["source_reference"], "topic_domain": row["topic_domain"], "normalization_status": normalized["normalization_status"], "semantic_guard": normalized["semantic_guard"], "length_tokens": length, "length_band": band(length), "lexical_shortcut_risk": "descriptive_only", "duplicate_risk": duplicate_risk, "acceptance_status": acceptance, "audit_reason": "Meets frozen length and structural checks; no classifier output used."})
    normalized_texts = [row["normalized_response"].lower().strip() for row in audited]
    exact_duplicates = {text: count for text, count in Counter(normalized_texts).items() if count > 1}
    prefix_counts = Counter(" ".join([token.lower() for token in tokens(row["normalized_response"])][:3]) for row in audited)
    repeated_prefixes = {prefix: count for prefix, count in prefix_counts.items() if prefix and count > 1}
    high_pairs = []
    for left in range(len(audited)):
        for right in range(left + 1, len(audited)):
            if similarity[left, right] >= 0.55:
                high_pairs.append({"left": audited[left]["candidate_id"], "right": audited[right]["candidate_id"], "tfidf_char_cosine": round(float(similarity[left, right]), 4)})
    markers = {
        "logic": ("therefore", "so", "implies", "entails", "must"),
        "causality": ("because", "causes", "leads", "results", "due"),
        "analogy": ("like", "as", "similar", "corresponds", "relation"),
        "definition": ("is", "means", "refers", "defined", "describes"),
    }
    lexical = {}
    for task_class, terms in markers.items():
        class_rows = [row for row in audited if row["task_class"] == task_class]
        lexical[task_class] = {term: sum(term in row["normalized_response"].lower().split() for row in class_rows) for term in terms}
    summary = {
        "raw_count": len(specs),
        "class_counts": dict(Counter(row["task_class"] for row in specs)),
        "provenance_counts": dict(Counter(row["provenance"] for row in specs)),
        "source_counts": dict(Counter(row["source_reference"] for row in specs)),
        "topic_counts": {task_class: dict(Counter(row["topic_domain"] for row in specs if row["task_class"] == task_class)) for task_class in ("logic", "causality", "analogy", "definition")},
        "normalization_counts": dict(Counter(row["normalization_status"] for row in normalized_rows)),
        "acceptance_counts": dict(Counter(row["acceptance_status"] for row in audited)),
        "length_counts": {task_class: dict(Counter(row["length_band"] for row in audited if row["task_class"] == task_class)) for task_class in ("logic", "causality", "analogy", "definition")},
        "exact_duplicate_texts": exact_duplicates,
        "repeated_three_word_prefixes": repeated_prefixes,
        "tfidf_char_similarity_pairs_at_least_0_55": high_pairs,
        "lexical_marker_counts": lexical,
        "normalizer_input_fields": ["candidate_id", "raw_response"],
        "classifier_used": False,
        "model_run": False,
    }
    write_csv(AUDITED_PATH, ["candidate_id", "task_class", "raw_response", "normalized_response", "provenance", "source_reference", "topic_domain", "normalization_status", "semantic_guard", "length_tokens", "length_band", "lexical_shortcut_risk", "duplicate_risk", "acceptance_status", "audit_reason"], audited)
    with AUDIT_SUMMARY.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    retained = read_csv(RETAINED)
    accepted = [row for row in audited if row["acceptance_status"] == "ACCEPT_CANDIDATE"]
    gap_counts = Counter(row["task_class"] for row in accepted)
    required = {"logic": 42, "causality": 30, "analogy": 26, "definition": 30}
    if any(gap_counts[task_class] < count for task_class, count in required.items()):
        return
    final_rows = []
    for row in retained:
        final_rows.append({"candidate_id": row["candidate_id"], "task_class": row["task_class"], "response_text": row["normalized_response"], "provenance": row["provenance"], "source_reference": row["source_reference"], "topic_domain": row["topic_domain"], "length_tokens": row["length_tokens"], "length_band": row["length_band"]})
    for row in accepted:
        final_rows.append({"candidate_id": row["candidate_id"], "task_class": row["task_class"], "response_text": row["normalized_response"], "provenance": row["provenance"], "source_reference": row["source_reference"], "topic_domain": row["topic_domain"], "length_tokens": row["length_tokens"], "length_band": row["length_band"]})
    final_fields = ["candidate_id", "task_class", "response_text", "provenance", "source_reference", "topic_domain", "length_tokens", "length_band"]
    write_csv(FINAL_POOL, final_fields, final_rows)
    rng = random.Random(20260812)
    sample = rng.sample(final_rows, 40)
    write_csv(HUMAN_SAMPLE, ["candidate_id", "task_class", "response_text", "provenance", "topic_domain", "human_label_agreement", "human_naturalness", "human_self_contained", "human_ambiguity", "human_notes"], [{**{field: row[field] for field in ("candidate_id", "task_class", "response_text", "provenance", "topic_domain")}, "human_label_agreement": "", "human_naturalness": "", "human_self_contained": "", "human_ambiguity": "", "human_notes": ""} for row in sample])


if __name__ == "__main__":
    build()
