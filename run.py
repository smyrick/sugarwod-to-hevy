#!/usr/bin/env python3
"""Guided SugarWod → Hevy migration orchestrator.

Interactive for humans (prompts when stdin is a TTY). Non-interactive for agents
and scripts when given --yes or when stdin is not a TTY.

Usage:
  python3 run.py                                    # auto-locate, prompt
  python3 run.py ~/Downloads/workouts.csv --yes     # agent / CI
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from convert_sugarwod_to_hevy import (
    STRONG_HEADERS,
    convert_file,
    is_sugarwod_export,
)

DEFAULT_INPUT = Path("input/workouts.csv")
DEFAULT_OUTPUT = Path("output/workouts_hevy.csv")
EXPORT_HELP_URL = "docs/EXPORT_SUGARWOD.md"
IMPORT_HELP_URL = "docs/IMPORT_HEVY.md"


def is_interactive() -> bool:
    return sys.stdin.isatty()


def prompt_yes_no(message: str, *, default: bool = True) -> bool:
    suffix = " [Y/n] " if default else " [y/N] "
    while True:
        answer = input(message + suffix).strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please enter y or n.")


def prompt_choice(message: str, choices: tuple[str, ...], default: str) -> str:
    choices_display = "/".join(choices)
    while True:
        answer = input(f"{message} ({choices_display}) [{default}]: ").strip().lower()
        if not answer:
            return default
        if answer in choices:
            return answer
        print(f"Please enter one of: {', '.join(choices)}")


def prompt_path(message: str) -> Path:
    while True:
        raw = input(message).strip()
        if not raw:
            print("A path is required.")
            continue
        path = Path(raw).expanduser()
        if path.exists():
            return path
        print(f"File not found: {path}")


def find_downloads_export() -> Path | None:
    downloads = Path.home() / "Downloads"
    if not downloads.is_dir():
        return None
    candidates = sorted(
        downloads.glob("*workouts*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def locate_input(
    explicit: Path | None,
    *,
    assume_yes: bool,
    interactive: bool,
) -> Path:
    if explicit is not None:
        path = explicit.expanduser()
        if not path.exists():
            print(f"Error: input file not found: {path}", file=sys.stderr)
            raise SystemExit(1)
        return path

    if DEFAULT_INPUT.exists():
        if assume_yes or not interactive:
            return DEFAULT_INPUT
        if prompt_yes_no(f"Use {DEFAULT_INPUT}?"):
            return DEFAULT_INPUT

    found = find_downloads_export()
    if found is not None:
        if assume_yes or not interactive:
            print(f"Using export: {found}")
            return found
        if prompt_yes_no(f"Use {found}?"):
            return found

    if assume_yes or not interactive:
        print(
            "Error: no SugarWod export found. Pass a path or save to input/workouts.csv.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return prompt_path("Path to your SugarWod workouts.csv: ")


def verify_export(path: Path) -> None:
    if is_sugarwod_export(path):
        return
    print(f"Error: {path} does not look like a SugarWod workout export.", file=sys.stderr)
    print(
        f"Expected header: date,title,description,... (see {EXPORT_HELP_URL})",
        file=sys.stderr,
    )
    print(f"How to export from SugarWOD: {EXPORT_HELP_URL}", file=sys.stderr)
    raise SystemExit(1)


def confirm_input_weight_unit(
    unit: str,
    *,
    assume_yes: bool,
    interactive: bool,
    unit_explicit: bool,
) -> str:
    if unit_explicit or assume_yes or not interactive:
        return unit
    return prompt_choice(
        "What unit are your SugarWod barbell loads in?",
        ("lbs", "kg"),
        unit,
    )


def print_conversion_summary(
    input_count: int,
    unique_count: int,
    output_count: int,
    skipped: int,
    output_path: Path,
) -> None:
    if unique_count < input_count:
        print(
            f"Deduplicated {input_count - unique_count} duplicate workout rows "
            f"({input_count} -> {unique_count} unique workouts)"
        )
    if skipped:
        print(f"Skipped {skipped} unparseable workout rows (see warnings above)")
    print(
        f"Converted {unique_count - skipped} SugarWod workouts -> "
        f"{output_count} Strong-format set rows"
    )
    print(f"Wrote {output_path}")


def print_validation_summary(output_path: Path) -> None:
    print()
    print("--- Validation spot-check ---")

    with output_path.open(newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        header = next(reader)
        rows = list(reader)

    header_ok = header == STRONG_HEADERS
    print(f"Header: {len(header)} columns {'OK' if header_ok else 'MISMATCH'}")

    load_sample: list[str] | None = None
    timed_sample: list[str] | None = None
    for row in rows:
        if len(row) < 9:
            continue
        weight, reps, seconds = row[5], row[6], row[8]
        exercise = row[3] if len(row) > 3 else ""
        if load_sample is None and weight not in ("0", "") and float(weight or 0) > 0:
            load_sample = row
        if timed_sample is None and seconds not in ("0", "") and int(seconds or 0) > 0:
            timed_sample = row
        if load_sample and timed_sample:
            break

    if load_sample:
        print(
            f"Load sample: {load_sample[3]} — Weight={load_sample[5]} kg, "
            f"Reps={load_sample[6]}"
        )
    else:
        print("Load sample: none found (no barbell rows with weight > 0)")

    if timed_sample:
        print(
            f"Timed WOD sample: {timed_sample[3]} — Seconds={timed_sample[8]}, "
            f"Duration={timed_sample[2]}"
        )
    else:
        print("Timed WOD sample: none found")

    print(f"Total set rows: {len(rows)}")


def print_next_steps(output_path: Path) -> None:
    print()
    print("--- Next: import into Hevy ---")
    print("1. Open Hevy → Profile → Settings → Export & Import Data → Import Data")
    print("2. Tap Import Strong CSV (not a generic upload)")
    print(f"3. Select {output_path}")
    print("4. Wait for the import to finish")
    print()
    print("Important:")
    print("- Hevy allows only ONE Strong CSV import per account. Revert any previous import first.")
    print("- After import, you can tap Revert Data Import on the same screen to undo.")
    print(f"- Full guide: {IMPORT_HELP_URL}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guided SugarWod to Hevy migration (locate, verify, convert, validate)."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Path to SugarWod workouts.csv (default: auto-locate)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output CSV path (default: {DEFAULT_OUTPUT})",
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
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Non-interactive: use defaults, never prompt",
    )
    args = parser.parse_args()

    assume_yes = args.yes or not is_interactive()
    interactive = is_interactive() and not args.yes
    unit_explicit = "--input-weight-unit" in sys.argv

    explicit = Path(args.input) if args.input else None
    input_path = locate_input(explicit, assume_yes=assume_yes, interactive=interactive)
    print(f"Input: {input_path}")

    verify_export(input_path)

    input_weight_unit = confirm_input_weight_unit(
        args.input_weight_unit,
        assume_yes=assume_yes,
        interactive=interactive,
        unit_explicit=unit_explicit,
    )
    if interactive and not assume_yes and not unit_explicit:
        print(f"Using --input-weight-unit {input_weight_unit}, --strong-weight-unit kg")

    output_path = Path(args.output)
    input_count, unique_count, output_count, skipped = convert_file(
        input_path,
        output_path,
        input_weight_unit=input_weight_unit,
        strong_weight_unit=args.strong_weight_unit,
    )

    print_conversion_summary(
        input_count, unique_count, output_count, skipped, output_path
    )
    print_validation_summary(output_path)
    print_next_steps(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
