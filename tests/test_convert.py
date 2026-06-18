"""Regression tests for the SugarWod -> Strong converter.

Run with:  python3 -m pytest

The weight round-trip (lbs_to_strong_kg) is the correctness-critical path: a
regression there silently mis-scales every imported load in Hevy.
"""

from __future__ import annotations

import csv

import pytest

import convert_sugarwod_to_hevy as conv


# --------------------------------------------------------------------------
# lbs_to_strong_kg round-trip (the reason this project exists)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "lbs, expected",
    [
        (320, "145.15"),
        (190, "86.183"),
        (335, "151.953"),
        (225, "102.06"),
        (350, "158.757"),
        (100, "45.36"),
        (45, "20.41"),
        (500, "226.796"),
    ],
)
def test_known_kg_values(lbs, expected):
    assert conv.lbs_to_strong_kg(lbs) == expected


def test_round_trip_every_whole_pound_1_to_1000():
    """Every whole pound must redisplay exactly in Hevy, using <= 3 decimals."""
    max_decimals = 0
    for lbs in range(1, 1001):
        s = conv.lbs_to_strong_kg(lbs)
        displayed = round(float(s) / conv.LBS_TO_KG, 2)
        assert displayed == lbs, f"{lbs} lbs -> {s} kg displays as {displayed}"
        decimals = len(s.split(".")[1]) if "." in s else 0
        max_decimals = max(max_decimals, decimals)
    assert max_decimals <= 3


def test_zero_pounds_returns_zero():
    assert conv.lbs_to_strong_kg(0) == "0"


def test_fractional_load_rounds_to_whole_pound():
    # 187.5 -> 188 (nearest whole pound) before kg conversion
    assert conv.lbs_to_strong_kg(187.5) == conv.lbs_to_strong_kg(188)


# --------------------------------------------------------------------------
# format_strong_weight unit dispatch
# --------------------------------------------------------------------------


def test_weight_lbs_to_kg():
    assert conv.format_strong_weight(320, input_weight_unit="lbs", strong_weight_unit="kg") == "145.15"


def test_weight_lbs_to_lbs_is_whole_number():
    assert conv.format_strong_weight(225.4, input_weight_unit="lbs", strong_weight_unit="lbs") == "225"


def test_weight_kg_to_lbs():
    assert conv.format_strong_weight(100, input_weight_unit="kg", strong_weight_unit="lbs") == "220"


def test_weight_kg_to_kg():
    assert conv.format_strong_weight(100, input_weight_unit="kg", strong_weight_unit="kg") == "100.00"


@pytest.mark.parametrize("value", [None, "", 0, "0"])
def test_weight_zero_like_returns_zero(value):
    assert conv.format_strong_weight(value) == "0"


# --------------------------------------------------------------------------
# format_strong_reps robustness
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value, expected",
    [
        (16, "16"),
        ("16", "16"),
        ("16.0", "16"),
        (None, "0"),
        ("", "0"),
        ("16+1", "0"),  # non-numeric must not crash
    ],
)
def test_format_strong_reps(value, expected):
    assert conv.format_strong_reps(value) == expected


# --------------------------------------------------------------------------
# build_load_sets pairing logic
# --------------------------------------------------------------------------


def _row(set_details: str = "", description: str = "") -> dict:
    return {"set_details": set_details, "description": description}


def test_one_load_many_reps_replicates_load():
    row = _row('[{"load": 275}]', "#1: 5 reps #2: 5 reps #3: 5 reps")
    assert conv.build_load_sets(row) == [(275.0, 5), (275.0, 5), (275.0, 5)]


def test_equal_loads_and_reps_zip():
    row = _row('[{"load": 255}, {"load": 275}]', "#1: 3 reps #2: 2 reps")
    assert conv.build_load_sets(row) == [(255.0, 3), (275.0, 2)]


def test_unequal_counts_carry_forward_last_load():
    row = _row('[{"load": 255}, {"load": 275}]', "#1: 3 reps #2: 3 reps #3: 3 reps")
    assert conv.build_load_sets(row) == [(255.0, 3), (275.0, 3), (275.0, 3)]


def test_loads_only():
    row = _row('[{"load": 135}, {"load": 145}]', "")
    assert conv.build_load_sets(row) == [(135.0, None), (145.0, None)]


def test_neither_loads_nor_reps():
    assert conv.build_load_sets(_row()) == [(None, None)]


# --------------------------------------------------------------------------
# score_type routing
# --------------------------------------------------------------------------


def _full_row(**kw) -> dict:
    base = {
        "date": "12/14/2021",
        "title": "Test",
        "description": "",
        "best_result_raw": "",
        "best_result_display": "",
        "score_type": "",
        "barbell_lift": "",
        "set_details": "",
        "notes": "",
        "rx_or_scaled": "",
        "pr": "",
    }
    base.update(kw)
    return base


def test_load_row_maps_exercise_and_weight():
    row = _full_row(
        title="Back Squat 1x1",
        score_type="Load",
        barbell_lift="Back Squat",
        set_details='[{"load": 335}]',
        description="#1: 1 rep",
    )
    rows = conv.convert_row(row)
    assert len(rows) == 1
    # columns: Date, Workout Name, Duration, Exercise Name, Set Order, Weight, Reps, ...
    assert rows[0][3] == "Squat (Barbell)"
    assert rows[0][5] == "151.953"
    assert rows[0][6] == "1"


def test_timed_wod_populates_seconds():
    row = _full_row(
        title="MURPH",
        score_type="",
        set_details='[{"mins": 46, "secs": 2}]',
    )
    rows = conv.convert_row(row)
    assert len(rows) == 1
    assert rows[0][8] == str(46 * 60 + 2)  # Seconds column
    assert rows[0][5] == "0"  # Weight


def test_reps_wod_populates_reps():
    row = _full_row(title="HSPU 2min", score_type="Reps", set_details='[{"reps": 16}]')
    rows = conv.convert_row(row)
    assert len(rows) == 1
    assert rows[0][6] == "16"


def test_parse_date_to_noon():
    assert conv.parse_date("12/14/2021") == "2021-12-14 12:00:00"


# --------------------------------------------------------------------------
# dedupe
# --------------------------------------------------------------------------


def test_dedupe_keeps_richest_set_details():
    rows = [
        {"date": "1/1/2022", "title": "A", "set_details": "[]"},
        {"date": "1/1/2022", "title": "A", "set_details": '[{"load": 100}, {"load": 110}]'},
    ]
    deduped = conv.dedupe_rows(rows)
    assert len(deduped) == 1
    assert "110" in deduped[0]["set_details"]


# --------------------------------------------------------------------------
# is_sugarwod_export
# --------------------------------------------------------------------------


def test_is_sugarwod_export_valid(tmp_path):
    path = tmp_path / "workouts.csv"
    path.write_text(conv.SUGARWOD_HEADER_LINE + "\n", encoding="utf-8")
    assert conv.is_sugarwod_export(path) is True


def test_is_sugarwod_export_invalid_header(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("foo,bar,baz\n", encoding="utf-8")
    assert conv.is_sugarwod_export(path) is False


def test_is_sugarwod_export_missing_file(tmp_path):
    assert conv.is_sugarwod_export(tmp_path / "nope.csv") is False


# --------------------------------------------------------------------------
# convert_file end-to-end: bad rows are skipped, not fatal
# --------------------------------------------------------------------------


def test_convert_file_skips_bad_rows(tmp_path):
    src = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    fieldnames = [
        "date", "title", "description", "best_result_raw", "best_result_display",
        "score_type", "barbell_lift", "set_details", "notes", "rx_or_scaled", "pr",
    ]
    with src.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerow({**{k: "" for k in fieldnames}, "date": "not-a-date", "title": "Bad"})
        w.writerow({
            **{k: "" for k in fieldnames},
            "date": "12/14/2021", "title": "Back Squat", "score_type": "Load",
            "barbell_lift": "Back Squat", "set_details": '[{"load": 225}]',
            "description": "#1: 5 reps",
        })

    input_count, unique_count, output_count, skipped = conv.convert_file(src, out)
    assert input_count == 2
    assert skipped == 1
    assert output_count == 1  # only the good row produced output
    assert out.exists()
