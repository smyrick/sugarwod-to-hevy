# Usage

How to run the converter — guided (`run.py`) or direct (`convert_sugarwod_to_hevy.py`).

**Previous:** [EXPORT_SUGARWOD.md](EXPORT_SUGARWOD.md) · **Next:** [IMPORT_HEVY.md](IMPORT_HEVY.md) · **Overview:** [README.md](../README.md)

---

## Guided: `run.py` (recommended)

Auto-locates your export, verifies the header, converts, prints validation summary and Hevy next steps.

```bash
python3 run.py
```

With an explicit path:

```bash
python3 run.py ~/Downloads/workouts.csv
```

Non-interactive (for agents, scripts, CI):

```bash
python3 run.py ~/Downloads/workouts.csv --input-weight-unit lbs --yes
```

### `run.py` arguments

| Argument | Default | Purpose |
|----------|---------|---------|
| `input` | auto-locate | Path to SugarWod export |
| `-o`, `--output` | `output/workouts_hevy.csv` | Strong CSV destination |
| `--input-weight-unit` | `lbs` | Unit of load values in SugarWod |
| `--strong-weight-unit` | `kg` | Unit written to Strong `Weight` column |
| `-y`, `--yes` | off | Non-interactive; never prompt |

**Auto-locate order:** explicit path → `input/workouts.csv` → newest `*workouts*.csv` in `~/Downloads`.

---

## Direct: `convert_sugarwod_to_hevy.py`

Lower-level converter for scripting or debugging. No locate/verify/validation summary.

```bash
python3 convert_sugarwod_to_hevy.py
python3 convert_sugarwod_to_hevy.py ~/Downloads/workouts.csv -o output/workouts_hevy.csv
```

### Converter arguments

| Argument | Default | Purpose |
|----------|---------|---------|
| `input` | `input/workouts.csv` | Path to SugarWod export |
| `-o`, `--output` | `output/workouts_hevy.csv` | Strong CSV destination |
| `--input-weight-unit` | `lbs` | Unit of load values in SugarWod |
| `--strong-weight-unit` | `kg` | Unit written to Strong `Weight` column |

---

## No-clone one-liner

From the README — convert without cloning the repo:

```bash
curl -fsSL https://raw.githubusercontent.com/smyrick/sugarwod-to-hevy/main/convert_sugarwod_to_hevy.py \
  | python3 - ~/Downloads/workouts.csv -o workouts_hevy.csv
```

---

## Weight units

SugarWod stores barbell loads in **pounds**. The Strong CSV has a single `Weight` column with **no unit field**. Hevy's Strong importer treats those values as **kilograms**, then converts to your display unit (e.g. lbs).

By default the converter rounds SugarWod loads to the nearest whole pound and uses adaptive kg precision (2–3 decimals) so Hevy displays clean plate weights — see [LEARNINGS.md](LEARNINGS.md#rounding-whole-pounds--adaptive-kg-precision).

| SugarWod load | CSV `Weight` | Hevy display (lbs) |
|---------------|--------------|---------------------|
| 320 lbs | 145.15 | 320 |
| 190 lbs | 86.183 | 190 |
| 335 lbs | 151.953 | 335 |

Bodyweight and cardio rows keep `Weight` as `0`.

To write raw pound values (legacy — weights will appear ~2.2× too heavy in Hevy):

```bash
python3 convert_sugarwod_to_hevy.py --strong-weight-unit lbs
```

---

## Output format

The script writes a **Strong app CSV** — one row per set, 12 columns:

```text
Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,Notes,Workout Notes,RPE
```

Full schema: [STRONG_FORMAT.md](STRONG_FORMAT.md)

Example row (335 lb squat converted to kg for Hevy):

```csv
2021-12-14 12:00:00,Back Squat 1x1,45m,Squat (Barbell),1,151.953,1,0,0,,RX,
```

---

## Mapping notes

- **Barbell lifts** (`score_type = Load`): sets from `set_details` loads and reps from description. Single logged weight replicated across prescribed sets.
- **CrossFit WODs** (time, reps, rounds+reps): custom exercises named after workout title. Timed WODs use `Seconds`; details in `Notes`.
- **PR / RX / SCALED** preserved in `Workout Notes`.
- **Duration** estimated for lifting (`~4 min per set`); timed WODs use actual time (e.g. Murph → `46m`).
- Exercise names mapped to Hevy/Strong canonical names where possible (e.g. `Back Squat` → `Squat (Barbell)`). Unmapped names become custom exercises — see [LEARNINGS.md](LEARNINGS.md#unmapped-exercise-names-become-custom-exercises-in-hevy).

---

## Validation checklist

After conversion, spot-check `output/workouts_hevy.csv`:

| Check | What to verify |
|-------|----------------|
| Header | 12 columns matching Strong schema |
| Delimiter | Comma (not semicolon) |
| Dates | `YYYY-MM-DD HH:MM:SS` |
| Set order | Contiguous `1..N` per exercise within a workout |
| Zero-weight rows | WODs/cardio: `Weight=0`, `Reps=0`; timed WODs use `Seconds` |
| Load weights | Whole-lb SugarWod loads → kg in CSV; Hevy shows original lb value |

Example spot checks:

- **Murph:** `Seconds` populated (e.g. `2762`), `Duration` like `46m`, `Weight=0`, `Reps=0`
- **Back Squat:** exercise `Squat (Barbell)`, weight in kg matching SugarWod lbs
- **Cindy:** custom exercise name, result in `Notes`

`run.py` prints a short validation summary automatically. Duplicate SugarWod rows are deduplicated — see [LEARNINGS.md](LEARNINGS.md#sugarwod-export-duplicate-rows).

---

## Extend exercise name mapping

Edit `EXERCISE_NAME_MAP` at the top of `convert_sugarwod_to_hevy.py` to map additional SugarWod lift names and reduce duplicate custom exercises in Hevy.

---

## Running tests

Optional, for contributors. Tests need `pytest`:

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest
```

Tests cover weight round-trip, load/rep pairing, `score_type` routing, dedupe, bad-row skipping, and `is_sugarwod_export()`.
