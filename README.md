# SugarWod to Hevy

Convert a SugarWod workout export (`workouts.csv`) into the **Strong app CSV format** that Hevy accepts via **Import Strong CSV**.

```mermaid
flowchart LR
  sugarwod["SugarWOD app export"] --> csvIn["input/workouts.csv gitignored"]
  csvIn --> script["convert_sugarwod_to_hevy.py"]
  script --> csvOut["output/workouts_hevy.csv gitignored"]
  csvOut --> hevy["Hevy Import Strong CSV"]
```

## Local data layout

Personal workout data stays out of git. Use two local folders:

```
sugarwod-to-hevy/
  input/workouts.csv      ← SugarWod export (you provide)
  output/workouts_hevy.csv ← generated Strong CSV for Hevy
```

Both `input/` and `output/` are gitignored. You can still pass any path on the command line if you prefer keeping the export elsewhere.

**Contributors:** never commit files from `input/` or `output/` — even on forks. Workout exports contain personal data. The `.gitignore` also blocks `*.csv` anywhere in the repo as a safety net.

## Step 1: Export from SugarWod

1. Open the **SugarWOD** app
2. Go to **More** (or the menu) → **Tools & Resources** → **Export Workouts**
3. Confirm the export — SugarWOD emails a CSV (often named `workouts.csv`)
4. Save it into this repo as `input/workouts.csv` (create the `input/` folder if needed)

Export before your SugarWOD subscription ends if you are leaving the platform.

## Step 2: Run the converter

Requires Python 3 (stdlib only — no pip install).

```bash
python3 convert_sugarwod_to_hevy.py
```

With defaults, reads `input/workouts.csv` and writes `output/workouts_hevy.csv`. The `output/` folder is created automatically.

Or pass an explicit input path:

```bash
python3 convert_sugarwod_to_hevy.py ~/Downloads/workouts.csv
```

### CLI arguments

| Argument | Default | Purpose |
|----------|---------|---------|
| `input` | `input/workouts.csv` | Path to SugarWod export |
| `-o`, `--output` | `output/workouts_hevy.csv` | Strong CSV destination |
| `--input-weight-unit` | `lbs` | Unit of load values in SugarWod |
| `--strong-weight-unit` | `kg` | Unit written to Strong `Weight` column |

### Running the tests

Optional, for contributors. The converter is stdlib-only; tests need `pytest`:

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest
```

Tests cover the weight round-trip, load/rep pairing, `score_type` routing, dedupe, and bad-row skipping.

## Step 3: Import into Hevy

1. Open Hevy → **Profile** → **Settings** → **Export & Import Data** → **Import Data**
2. Tap **Import Strong CSV** (not a generic upload)
3. Select `output/workouts_hevy.csv`
4. Wait for the import to finish

**Important:**

- Hevy only allows **one** Strong CSV import per account. If you already imported a file, revert/remove it in Settings before trying again.
- Headers must be in English exactly as shown below.

### Re-import after a weight fix

If you previously imported with inflated weights (~2.2× too heavy in Hevy):

1. Hevy → Profile → Settings → Export & Import Data → **revert/remove** the old import
2. Regenerate `output/workouts_hevy.csv` with this script (default writes kg)
3. Import Strong CSV again
4. Spot-check a known lift (e.g. a 320 lb squat should show ~320 lbs in Hevy, not ~705 lbs)

## Weight units

SugarWod stores barbell loads in **pounds**. The Strong CSV schema has a single `Weight` column with **no unit field**. Hevy's Strong importer treats those values as **kilograms**, then converts to your display unit (e.g. lbs).

By default this script rounds SugarWod loads to the nearest whole pound and uses adaptive kg precision (2–3 decimals) so Hevy displays clean plate weights — see [docs/LEARNINGS.md](docs/LEARNINGS.md#rounding-whole-pounds--adaptive-kg-precision) for how `lbs_to_strong_kg()` works and which loads were verified.

| SugarWod load | CSV `Weight` | Hevy display (lbs) |
|---------------|--------------|---------------------|
| 320 lbs | 145.15 | 320 |
| 190 lbs | 86.183 | 190 |
| 335 lbs | 151.953 | 335 |

Bodyweight and cardio rows keep `Weight` as `0`.

To write raw pound values (legacy behavior — weights will appear ~2.2× too heavy in Hevy):

```bash
python3 convert_sugarwod_to_hevy.py --strong-weight-unit lbs
```

## Output format (Strong app schema)

The script writes a **Strong app CSV** — one row per set, 12 comma-separated columns — matching what Hevy expects for **Import Strong CSV**.

```text
Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,Notes,Workout Notes,RPE
```

**Full schema reference:** [docs/STRONG_FORMAT.md](docs/STRONG_FORMAT.md) — column semantics, formatting rules, row patterns (strength / timed WOD / reps), weight-unit behavior, and validation checklist. Intended for humans and for other tools or AI agents working with this format.

Example row (335 lb squat converted to kg for Hevy):

```csv
2021-12-14 12:00:00,Back Squat 1x1,45m,Squat (Barbell),1,151.953,1,0,0,,RX,
```

## Mapping notes

- **Barbell lifts** (`score_type = Load`): sets built from `set_details` loads and reps parsed from the description. When only the top working weight was logged, the weight is replicated across all prescribed sets.
- **CrossFit WODs** (time, reps, rounds+reps): imported as custom exercises named after the workout title. Timed WODs use the `Seconds` column; details go in `Notes`.
- **PR / RX / SCALED** flags are preserved in `Workout Notes`.
- **Duration** is estimated for lifting sessions (`~4 min per set`); timed WODs use their actual time (e.g. Murph → `46m`).
- **Distance** and **Seconds** default to `0` when not applicable (matching Strong exports).
- Exercise names are mapped to Hevy/Strong canonical names where possible (e.g. `Back Squat` → `Squat (Barbell)`). Unmapped names become custom exercises in Hevy — see [docs/LEARNINGS.md](docs/LEARNINGS.md#unmapped-exercise-names-become-custom-exercises-in-hevy).

## Validation checklist

After conversion, spot-check your `output/workouts_hevy.csv`:

| Check | What to verify |
|-------|----------------|
| Header | 12 columns: `Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,Notes,Workout Notes,RPE` |
| Delimiter | Comma (not semicolon) |
| Dates | `YYYY-MM-DD HH:MM:SS` |
| Set order | Contiguous `1..N` per exercise within a workout |
| Zero-weight rows | WODs/cardio: `Weight=0`, `Reps=0`; timed WODs use `Seconds` |
| Load weights | Whole-lb SugarWod loads → kg in CSV; Hevy should show the original lb value (typically 2–3 kg decimals) |

Example spot checks:

- **Murph:** `Seconds` populated (e.g. `2762`), `Duration` like `46m`, `Weight=0`, `Reps=0`
- **Back Squat:** exercise name `Squat (Barbell)`, weight in kg matching your SugarWod lbs
- **Cindy:** custom exercise name, result in `Notes`

The script prints how many workouts and set rows were written. Duplicate SugarWod rows are deduplicated automatically — see [docs/LEARNINGS.md](docs/LEARNINGS.md#sugarwod-export-duplicate-rows).

## Extend exercise name mapping

Edit `EXERCISE_NAME_MAP` at the top of `convert_sugarwod_to_hevy.py` to map additional SugarWod lift names and reduce duplicate custom exercises in Hevy.

## Further reading

| Doc | Contents |
|-----|----------|
| [docs/SUGARWOD_FORMAT.md](docs/SUGARWOD_FORMAT.md) | SugarWod input CSV — columns, `set_details` JSON, `score_type` routing |
| [docs/STRONG_FORMAT.md](docs/STRONG_FORMAT.md) | Strong output CSV — columns, row model, Hevy import requirements |
| [docs/LEARNINGS.md](docs/LEARNINGS.md) | Weight rounding, Hevy quirks, converter behavior, validation spot checks |
