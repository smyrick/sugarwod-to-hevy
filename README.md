# SugarWod to Hevy

Convert a SugarWod workout export (`workouts.csv`) into the **Strong app CSV format** that Hevy accepts via **Import Strong CSV**.

```mermaid
flowchart LR
  sugarwod["SugarWOD app export"] --> csvIn["workouts.csv local"]
  csvIn --> script["convert_sugarwod_to_hevy.py"]
  script --> csvOut["output/workouts_hevy.csv gitignored"]
  csvOut --> hevy["Hevy Import Strong CSV"]
```

## Step 1: Export from SugarWod

1. Open the **SugarWOD** app
2. Go to **More** (or the menu) → **Tools & Resources** → **Export Workouts**
3. Confirm the export — SugarWOD emails a CSV (often named `workouts.csv`)
4. Save the file somewhere on your machine (e.g. `~/Downloads/workouts.csv`)

Export before your SugarWOD subscription ends if you are leaving the platform.

## Step 2: Run the converter

Requires Python 3 (stdlib only — no pip install).

```bash
python3 convert_sugarwod_to_hevy.py ~/Downloads/workouts.csv
```

This writes `output/workouts_hevy.csv` by default. The `output/` folder is created automatically and is gitignored so your workout data stays local.

### CLI arguments

| Argument | Default | Purpose |
|----------|---------|---------|
| `input` | `workouts.csv` | Path to SugarWod export |
| `-o`, `--output` | `output/workouts_hevy.csv` | Strong CSV destination |
| `--input-weight-unit` | `lbs` | Unit of load values in SugarWod |
| `--strong-weight-unit` | `kg` | Unit written to Strong `Weight` column |

Override the output path:

```bash
python3 convert_sugarwod_to_hevy.py ~/Downloads/workouts.csv -o output/workouts_hevy.csv
```

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

By default this script converts lbs → kg when writing load rows so Hevy shows the correct weight:

| SugarWod load | CSV `Weight` | Hevy display (lbs) |
|---------------|--------------|---------------------|
| 320 lbs | 145.1 | ~320 |
| 190 lbs | 86.2 | ~190 |
| 335 lbs | 152.0 | ~335 |

Bodyweight and cardio rows keep `Weight` as `0`.

To write raw pound values (legacy behavior — weights will appear ~2.2× too heavy in Hevy):

```bash
python3 convert_sugarwod_to_hevy.py ~/Downloads/workouts.csv --strong-weight-unit lbs
```

## Output format (Strong app schema)

Comma-delimited CSV with these columns (in order):

```
Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,Notes,Workout Notes,RPE
```

This matches a direct export from the [Strong app](https://help.strongapp.io/article/235-export-workout-data), which is what Hevy's importer expects.

Example row (335 lb squat converted to kg):

```csv
2021-12-14 12:00:00,Back Squat 1x1,45m,Squat (Barbell),1,152.0,1,0,0,,RX,
```

## Mapping notes

- **Barbell lifts** (`score_type = Load`): sets built from `set_details` loads and reps parsed from the description. When only the top working weight was logged, the weight is replicated across all prescribed sets.
- **CrossFit WODs** (time, reps, rounds+reps): imported as custom exercises named after the workout title. Timed WODs use the `Seconds` column; details go in `Notes`.
- **PR / RX / SCALED** flags are preserved in `Workout Notes`.
- **Duration** is estimated for lifting sessions (`~4 min per set`); timed WODs use their actual time (e.g. Murph → `46m`).
- **Distance** and **Seconds** default to `0` when not applicable (matching Strong exports).
- Exercise names are mapped to Hevy/Strong canonical names where possible (e.g. `Back Squat` → `Squat (Barbell)`).

## Validation checklist

After conversion, spot-check your `output/workouts_hevy.csv`:

| Check | What to verify |
|-------|----------------|
| Header | 12 columns: `Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,Notes,Workout Notes,RPE` |
| Delimiter | Comma (not semicolon) |
| Dates | `YYYY-MM-DD HH:MM:SS` |
| Set order | Contiguous `1..N` per exercise within a workout |
| Zero-weight rows | WODs/cardio: `Weight=0`, `Reps=0`; timed WODs use `Seconds` |
| Load weights | Known lbs ÷ 2.205 ≈ CSV kg value (within ~0.1) |

Example spot checks:

- **Murph:** `Seconds` populated (e.g. `2762`), `Duration` like `46m`, `Weight=0`, `Reps=0`
- **Back Squat:** exercise name `Squat (Barbell)`, weight in kg matching your SugarWod lbs
- **Cindy:** custom exercise name, result in `Notes`

The script prints how many workouts and set rows were written. Duplicate SugarWod rows are deduplicated automatically.

## Extend exercise name mapping

Edit `EXERCISE_NAME_MAP` at the top of `convert_sugarwod_to_hevy.py` to map additional SugarWod lift names and reduce duplicate custom exercises in Hevy.
