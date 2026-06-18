#!/usr/bin/env python3
"""Convert SugarWod workout export CSV to Strong app format for Hevy import.

Input schema: docs/SUGARWOD_FORMAT.md
Output schema: docs/STRONG_FORMAT.md
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Strong app export schema accepted by Hevy's "Import Strong CSV".
# Full column semantics and examples: docs/STRONG_FORMAT.md
STRONG_HEADERS = [
    "Date",
    "Workout Name",
    "Duration",
    "Exercise Name",
    "Set Order",
    "Weight",
    "Reps",
    "Distance",
    "Seconds",
    "Notes",
    "Workout Notes",
    "RPE",
]

# SugarWod export CSV header (11 lowercase columns). Canonical source for input validation.
SUGARWOD_HEADERS = [
    "date",
    "title",
    "description",
    "best_result_raw",
    "best_result_display",
    "score_type",
    "barbell_lift",
    "set_details",
    "notes",
    "rx_or_scaled",
    "pr",
]
SUGARWOD_HEADER_LINE = ",".join(SUGARWOD_HEADERS)

DEFAULT_WORKOUT_DURATION = "45m"
LBS_TO_KG = 0.45359237

# Map SugarWod lift names to Hevy/Strong canonical exercise names where possible.
EXERCISE_NAME_MAP: dict[str, str] = {
    "Back Squat": "Squat (Barbell)",
    "Front Squat": "Front Squat (Barbell)",
    "Front Pause Squat": "Front Squat (Barbell)",
    "Back Pause Squat": "Squat (Barbell)",
    "Box Squat": "Squat (Barbell)",
    "Overhead Squat": "Overhead Squat (Barbell)",
    "Deadlift": "Deadlift (Barbell)",
    "Snatch Grip Deadlift": "Deadlift (Barbell)",
    "Romanian Deadlift": "Romanian Deadlift (Barbell)",
    "Bench Press": "Bench Press (Barbell)",
    "Shoulder Press": "Overhead Press (Barbell)",
    "Push Press": "Push Press (Barbell)",
    "Split Jerk": "Split Jerk (Barbell)",
    "Push Jerk": "Push Jerk (Barbell)",
    "Clean": "Power Clean (Barbell)",
    "Power Clean": "Power Clean (Barbell)",
    "Hang Power Clean": "Hang Power Clean (Barbell)",
    "Hang Squat Clean": "Hang Clean (Barbell)",
    "Squat Clean": "Squat Clean (Barbell)",
    "Muscle Clean": "Muscle Clean (Barbell)",
    "Clean & Jerk": "Clean and Jerk (Barbell)",
    "Power Clean & Jerk": "Clean and Jerk (Barbell)",
    "Snatch": "Snatch (Barbell)",
    "Power Snatch": "Power Snatch (Barbell)",
    "Hang Squat Snatch": "Hang Snatch (Barbell)",
    "Hang Power Snatch": "Hang Power Snatch (Barbell)",
    "Squat Pause Snatch": "Snatch (Barbell)",
    "Bent Over Row": "Bent Over Row (Barbell)",
    "Back Rack Lunges": "Lunge (Barbell)",
    "Split Squat": "Split Squat (Barbell)",
}

REP_PATTERN = re.compile(r"#\d+:\s*(\d+)\s*reps?", re.IGNORECASE)


def is_sugarwod_export(path: Path) -> bool:
    """Return True if the file's first line matches the SugarWod export header."""
    try:
        with path.open(encoding="utf-8") as infile:
            header = infile.readline().strip()
    except OSError:
        return False
    return header == SUGARWOD_HEADER_LINE


def map_exercise_name(name: str) -> str:
    name = name.strip()
    return EXERCISE_NAME_MAP.get(name, name)


def parse_date(date_str: str) -> str:
    parsed = datetime.strptime(date_str.strip(), "%m/%d/%Y")
    return parsed.strftime("%Y-%m-%d 12:00:00")


def parse_set_details(raw: str) -> list[dict]:
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def parse_reps_from_description(description: str) -> list[int]:
    return [int(match) for match in REP_PATTERN.findall(description or "")]


def extract_loads(set_details: list[dict]) -> list[float]:
    loads: list[float] = []
    for entry in set_details:
        if "load" in entry:
            loads.append(float(entry["load"]))
    return loads


def lbs_to_strong_kg(lbs: float) -> str:
    """Format kg so Hevy's kg→lbs display shows the original whole-pound load."""
    lbs = round(lbs)
    if lbs == 0:
        return "0"
    kg = lbs * LBS_TO_KG
    for precision in range(2, 6):
        formatted = f"{kg:.{precision}f}"
        if round(float(formatted) / LBS_TO_KG, 2) == lbs:
            return formatted
    return f"{kg:.4f}"


def format_strong_weight(
    value: float | str | None,
    *,
    input_weight_unit: str = "lbs",
    strong_weight_unit: str = "kg",
) -> str:
    if value is None or value == "":
        return "0"
    weight = float(value)
    if weight == 0:
        return "0"
    if input_weight_unit == "lbs" and strong_weight_unit == "kg":
        return lbs_to_strong_kg(weight)
    if input_weight_unit == "lbs":
        return f"{round(weight):.0f}"
    if input_weight_unit == "kg" and strong_weight_unit == "lbs":
        return f"{round(weight / LBS_TO_KG):.0f}"
    return f"{weight:.2f}"


def format_strong_reps(value: int | str | None) -> str:
    if value is None or value == "":
        return "0"
    try:
        return str(int(float(value)))
    except (ValueError, TypeError):
        return "0"


def format_strong_duration(seconds: int | None) -> str:
    """Format workout duration the way Strong exports it (e.g. 2h 38m, 45m)."""
    if not seconds:
        return DEFAULT_WORKOUT_DURATION
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    if minutes:
        return f"{minutes}m"
    return "1m"


def estimate_lift_duration(num_sets: int) -> str:
    minutes = min(120, max(15, num_sets * 4))
    return f"{minutes}m"


def dedupe_rows(rows: list[dict]) -> list[dict]:
    """Keep one row per (date, title), preferring the richest set_details."""
    deduped: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row["date"], row["title"])
        if key not in deduped:
            deduped[key] = row
            continue
        existing = deduped[key]
        if len(parse_set_details(row.get("set_details", ""))) > len(
            parse_set_details(existing.get("set_details", ""))
        ):
            deduped[key] = row
    return list(deduped.values())


def build_workout_notes(row: dict) -> str:
    parts: list[str] = []
    notes = (row.get("notes") or "").strip()
    if notes:
        parts.append(notes)

    rx_scaled = (row.get("rx_or_scaled") or "").strip()
    if rx_scaled:
        parts.append(rx_scaled)

    if (row.get("pr") or "").strip() == "PR":
        parts.append("PR")

    return " | ".join(parts) if parts else ""


def build_wod_notes(row: dict) -> str:
    parts: list[str] = []
    description = (row.get("description") or "").strip()
    if description:
        parts.append(description)

    display = (row.get("best_result_display") or "").strip()
    if display:
        parts.append(f"result: {display}")

    rx_scaled = (row.get("rx_or_scaled") or "").strip()
    if rx_scaled:
        parts.append(rx_scaled)

    return " | ".join(parts) if parts else ""


def build_load_sets(row: dict) -> list[tuple[float | None, int | None]]:
    """Return list of (weight, reps) for each set."""
    set_details = parse_set_details(row.get("set_details", ""))
    loads = extract_loads(set_details)
    reps = parse_reps_from_description(row.get("description", ""))

    if not loads and not reps:
        return [(None, None)]

    if not loads:
        return [(None, rep) for rep in reps] if reps else [(None, None)]

    if not reps:
        return [(load, None) for load in loads]

    if len(reps) == len(loads):
        return [(loads[i], reps[i]) for i in range(len(loads))]

    if len(loads) == 1 and len(reps) >= 1:
        return [(loads[0], rep) for rep in reps]

    if len(loads) > 1 and len(reps) > 1 and len(loads) != len(reps):
        pairs: list[tuple[float | None, int | None]] = []
        last_load = loads[0]
        for i, rep in enumerate(reps):
            if i < len(loads):
                last_load = loads[i]
            pairs.append((last_load, rep))
        return pairs

    return [(loads[0], reps[0])]


def time_seconds_from_details(set_details: list[dict]) -> int | None:
    for entry in set_details:
        if "mins" in entry or "secs" in entry:
            mins = int(entry.get("mins", 0) or 0)
            secs = int(entry.get("secs", 0) or 0)
            return mins * 60 + secs
    return None


def make_row(
    *,
    date: str,
    workout_name: str,
    duration: str,
    exercise_name: str,
    set_order: int,
    weight: str = "0",
    reps: str = "0",
    distance: str = "0",
    seconds: str = "0",
    notes: str = "",
    workout_notes: str = "",
) -> list[str]:
    return [
        date,
        workout_name,
        duration,
        exercise_name,
        str(set_order),
        weight,
        reps,
        distance,
        seconds,
        notes,
        workout_notes,
        "",
    ]


def convert_load_row(
    row: dict,
    date: str,
    workout_notes: str,
    *,
    input_weight_unit: str = "lbs",
    strong_weight_unit: str = "kg",
) -> list[list[str]]:
    exercise = map_exercise_name(row.get("barbell_lift") or row.get("title", ""))
    sets = build_load_sets(row)
    duration = estimate_lift_duration(len(sets))
    output: list[list[str]] = []

    for idx, (weight, reps) in enumerate(sets, start=1):
        output.append(
            make_row(
                date=date,
                workout_name=row["title"],
                duration=duration,
                exercise_name=exercise,
                set_order=idx,
                weight=format_strong_weight(
                    weight,
                    input_weight_unit=input_weight_unit,
                    strong_weight_unit=strong_weight_unit,
                ),
                reps=format_strong_reps(reps),
                workout_notes=workout_notes,
            )
        )

    return output


def convert_wod_row(row: dict, date: str, workout_notes: str) -> list[list[str]]:
    exercise = row["title"]
    score_type = (row.get("score_type") or "").strip()
    set_details = parse_set_details(row.get("set_details", ""))
    wod_notes = build_wod_notes(row)

    if score_type == "":
        seconds = time_seconds_from_details(set_details)
        if seconds is None and row.get("best_result_raw"):
            try:
                seconds = int(float(row["best_result_raw"]))
            except ValueError:
                seconds = 0
        seconds = seconds or 0
        duration = format_strong_duration(seconds)
        return [
            make_row(
                date=date,
                workout_name=row["title"],
                duration=duration,
                exercise_name=exercise,
                set_order=1,
                seconds=str(seconds),
                notes=wod_notes,
                workout_notes=workout_notes,
            )
        ]

    if score_type == "Reps":
        reps_entries = [entry for entry in set_details if "reps" in entry]
        if not reps_entries:
            reps_entries = [{"reps": row.get("best_result_display", "")}]
        duration = DEFAULT_WORKOUT_DURATION
        output: list[list[str]] = []
        for idx, entry in enumerate(reps_entries, start=1):
            output.append(
                make_row(
                    date=date,
                    workout_name=row["title"],
                    duration=duration,
                    exercise_name=exercise,
                    set_order=idx,
                    reps=format_strong_reps(entry.get("reps")),
                    notes=wod_notes,
                    workout_notes=workout_notes,
                )
            )
        return output

    return [
        make_row(
            date=date,
            workout_name=row["title"],
            duration=DEFAULT_WORKOUT_DURATION,
            exercise_name=exercise,
            set_order=1,
            notes=wod_notes,
            workout_notes=workout_notes,
        )
    ]


def convert_row(
    row: dict,
    *,
    input_weight_unit: str = "lbs",
    strong_weight_unit: str = "kg",
) -> list[list[str]]:
    date = parse_date(row["date"])
    workout_notes = build_workout_notes(row)
    score_type = (row.get("score_type") or "").strip()

    if score_type == "Load":
        return convert_load_row(
            row,
            date,
            workout_notes,
            input_weight_unit=input_weight_unit,
            strong_weight_unit=strong_weight_unit,
        )

    return convert_wod_row(row, date, workout_notes)


def convert_file(
    input_path: Path,
    output_path: Path,
    *,
    input_weight_unit: str = "lbs",
    strong_weight_unit: str = "kg",
) -> tuple[int, int, int, int]:
    with input_path.open(newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)

    input_count = len(rows)
    rows = dedupe_rows(rows)

    output_rows: list[list[str]] = []
    skipped = 0
    for row in rows:
        try:
            output_rows.extend(
                convert_row(
                    row,
                    input_weight_unit=input_weight_unit,
                    strong_weight_unit=strong_weight_unit,
                )
            )
        except (ValueError, KeyError, TypeError) as exc:
            skipped += 1
            label = f"{row.get('date', '?')} {row.get('title', '?')}".strip()
            print(f"Warning: skipped row ({label}): {exc}", file=sys.stderr)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(STRONG_HEADERS)
        writer.writerows(output_rows)

    return input_count, len(rows), len(output_rows), skipped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert SugarWod workout CSV export to Strong format for Hevy import."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="input/workouts.csv",
        help="Path to SugarWod workouts.csv (default: input/workouts.csv)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output/workouts_hevy.csv",
        help="Output CSV path (default: output/workouts_hevy.csv)",
    )
    parser.add_argument(
        "--input-weight-unit",
        choices=["lbs", "kg"],
        default="lbs",
        help="Unit of load values in SugarWod export (default: lbs)",
    )
    parser.add_argument(
        "--strong-weight-unit",
        choices=["lbs", "kg"],
        default="kg",
        help="Unit to write in Strong CSV Weight column (default: kg for Hevy)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    input_count, unique_count, output_count, skipped = convert_file(
        input_path,
        output_path,
        input_weight_unit=args.input_weight_unit,
        strong_weight_unit=args.strong_weight_unit,
    )
    if unique_count < input_count:
        print(
            f"Deduplicated {input_count - unique_count} duplicate workout rows "
            f"({input_count} -> {unique_count} unique workouts)"
        )
    if skipped:
        print(f"Skipped {skipped} unparseable workout rows (see warnings above)")
    print(
        f"Converted {unique_count - skipped} SugarWod workouts -> {output_count} Strong-format set rows"
    )
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
