---
name: sugarwod-to-hevy
description: >
  Guide users through migrating SugarWOD workout history to Hevy via Strong CSV.
  Use this skill when: (1) a user wants to convert a SugarWOD workouts.csv export
  for Hevy import, (2) a user is migrating from SugarWOD to Hevy and needs step-by-step
  help, (3) imported Hevy weights look wrong or ~2.2x too heavy, (4) a user needs
  to revert or re-import a Hevy Strong CSV import, (5) a user asks about weight
  units for the SugarWOD to Hevy conversion.
license: Apache-2.0
compatibility: Python 3 (stdlib only), shell access, file read/write. No pip install required.
metadata:
  author: smyrick
  version: "1.0.0"
allowed-tools: Read Write Edit Shell Glob Grep
---

# SugarWOD to Hevy migration

Walk the user through converting a SugarWOD `workouts.csv` export into Strong CSV format for Hevy's **Import Strong CSV** flow. This repo's converter is stdlib-only Python — no coding experience required.

**Reference docs (read as needed, do not duplicate in chat):**

- [README.md](README.md) — CLI usage and overview
- [docs/SUGARWOD_FORMAT.md](docs/SUGARWOD_FORMAT.md) — input CSV schema
- [docs/STRONG_FORMAT.md](docs/STRONG_FORMAT.md) — output CSV schema and validation
- [docs/LEARNINGS.md](docs/LEARNINGS.md) — weight units, Hevy quirks, spot checks

---

## Process

Follow these steps in order. Pause for user confirmation at each gate marked **ASK**.

- [ ] Step 1: Locate the SugarWOD export
- [ ] Step 2: Verify the file is a real SugarWOD export
- [ ] Step 3: Confirm weight units **ASK**
- [ ] Step 4: Run the converter
- [ ] Step 5: Validate the output **ASK**
- [ ] Step 6: Import into Hevy
- [ ] Step 7: Revert safety net (if needed)

---

## Step 1: Locate the SugarWOD export

**ASK:** Where is your SugarWOD `workouts.csv`? Common locations: Downloads, email attachment, or `input/workouts.csv` in this repo.

If the user does not have an export yet, guide them:

1. Open the **SugarWOD** app
2. Go to **More** → **Tools & Resources** → **Export Workouts**
3. Confirm the export — SugarWOD emails a CSV (usually named `workouts.csv`)
4. Save it locally (e.g. `input/workouts.csv` in this repo)

**Privacy:** `input/` and `output/` are gitignored. Personal workout data must never be committed. The `.gitignore` also blocks `*.csv` repo-wide as a safety net.

---

## Step 2: Verify the SugarWOD export

Read the first line of the user's CSV. It must match this header exactly (11 lowercase columns):

```text
date,title,description,best_result_raw,best_result_display,score_type,barbell_lift,set_details,notes,rx_or_scaled,pr
```

If the header does not match, stop and tell the user this is not a SugarWOD workout export. Point them back to Step 1.

Optionally skim a few data rows to confirm `set_details` contains JSON arrays and dates look like `MM/DD/YYYY`.

Full input schema: [docs/SUGARWOD_FORMAT.md](docs/SUGARWOD_FORMAT.md)

---

## Step 3: Confirm weight units

**ASK before running the converter.** Do not assume units.

### The core gotcha

The Strong CSV has a single `Weight` column with **no unit field**. Hevy's **Import Strong CSV** treats every `Weight` value as **kilograms**, then converts to the user's display preference (e.g. lbs).

SugarWOD barbell loads are typically **pounds** (US CrossFit). If you write raw pound numbers into the CSV, Hevy reads them as kg and weights appear **~2.2× too heavy** (320 lbs in SugarWOD → ~705 lbs in Hevy).

Details: [docs/LEARNINGS.md](docs/LEARNINGS.md#hevy-treats-strong-csv-weights-as-kilograms)

### Questions to ask the user

1. **What unit are your SugarWOD barbell loads in?**
   - Default for US CrossFit: **lbs**
   - Maps to `--input-weight-unit lbs` (default) or `kg`

2. **What unit does Hevy display weights in?**
   - Most US users: **lbs**
   - This does not change the CSV — Hevy always imports kg internally

### Recommended defaults

| Situation | Flags |
|-----------|-------|
| US CrossFit logs, Hevy display in lbs | `--input-weight-unit lbs --strong-weight-unit kg` (script defaults) |
| SugarWOD loads already in kg | `--input-weight-unit kg --strong-weight-unit kg` |
| Debug only — weights will be ~2.2× too heavy | `--strong-weight-unit lbs` |

Confirm the chosen flags with the user before proceeding.

---

## Step 4: Run the converter

Requires Python 3 only — no pip install.

```bash
python3 convert_sugarwod_to_hevy.py <input_path> -o output/workouts_hevy.csv \
  --input-weight-unit <lbs|kg> \
  --strong-weight-unit <kg|lbs>
```

Example with defaults (lbs in, kg out):

```bash
python3 convert_sugarwod_to_hevy.py input/workouts.csv -o output/workouts_hevy.csv
```

Report the script output to the user:

- Deduplication count (if any duplicate `date`+`title` rows were dropped)
- Skipped unparseable rows (with warnings)
- Final count: `N SugarWod workouts → M Strong-format set rows`
- Output path: `output/workouts_hevy.csv`

---

## Step 5: Validate the output

Before the user imports into Hevy, validate `output/workouts_hevy.csv` and present findings.

### Automated checks (agent performs)

| Check | Pass criteria |
|-------|----------------|
| Header | Exactly 12 columns: `Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,Notes,Workout Notes,RPE` |
| Row count | Matches script summary |
| Timed WOD sample | At least one row with `Seconds` > 0, `Weight` = 0, `Reps` = 0 (e.g. Murph) |
| Load sample | At least one barbell row with kg `Weight` and mapped exercise name (e.g. `Squat (Barbell)`) |
| Set order | Contiguous `1..N` per exercise within a workout |

### Spot-check table (present to user)

Pick 1–2 lifts the user likely remembers. Show SugarWOD lbs → CSV kg → expected Hevy display:

| SugarWOD lbs | CSV `Weight` (kg) | Expected Hevy display (lbs) |
|--------------|-------------------|-------------------------------|
| 320 | 145.15 | 320 |
| 190 | 86.183 | 190 |
| 335 | 151.953 | 335 |

If the user names a specific lift/date, grep the output CSV for that session and verify.

Full validation checklist: [docs/STRONG_FORMAT.md](docs/STRONG_FORMAT.md#validation-checklist)

**ASK:** Do these spot checks look right? Do you want to proceed to Hevy import?

Do not tell the user to import until they confirm.

---

## Step 6: Import into Hevy

Guide the user through Hevy import:

1. Open Hevy → **Profile** → **Settings** → **Export & Import Data** → **Import Data**
2. Tap **Import Strong CSV** (not a generic file upload)
3. Select `output/workouts_hevy.csv` (AirDrop, email, cloud drive, or Files app)
4. Wait for "Workout data successfully imported!"

**Constraints:**

- Hevy allows **one** Strong CSV import per account. Revert any previous import first.
- Column headers must be in English exactly as listed in [docs/STRONG_FORMAT.md](docs/STRONG_FORMAT.md).

After import, ask the user to spot-check 1–2 known sessions in Hevy (a recent squat/bench and a timed WOD like Murph).

---

## Step 7: Revert safety net

If weights or exercises look wrong after import, the user can undo **without leaving the Import Data screen**.

![Hevy Import Data screen showing Revert Data Import](docs/images/hevy-import-revert.png)

### The trick

Right after a successful import:

1. **Stay on the Import Data screen** — do not navigate away from Settings entirely
2. You can tap **Home** or **Profile** on the bottom nav and come back
3. The **Revert Data Import** link (red text) remains available
4. Tap it to remove the imported data and try again

This gives the user time to validate workouts in Hevy before committing to the import.

### Full re-import loop

If the user needs to fix the CSV and re-import:

1. **Revert Data Import** (while still on the Import Data screen, or via Settings → Export & Import Data)
2. Regenerate `output/workouts_hevy.csv` with corrected flags
3. Re-validate (Step 5)
4. Import Strong CSV again

See also: [docs/LEARNINGS.md](docs/LEARNINGS.md#hevy-allows-only-one-strong-csv-import)

---

## Quick reference

### CLI arguments

| Argument | Default | Purpose |
|----------|---------|---------|
| `input` | `input/workouts.csv` | Path to SugarWOD export |
| `-o`, `--output` | `output/workouts_hevy.csv` | Strong CSV destination |
| `--input-weight-unit` | `lbs` | Unit of load values in SugarWOD |
| `--strong-weight-unit` | `kg` | Unit written to Strong `Weight` column |

### Common symptoms

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Weights ~2.2× too heavy in Hevy | Raw lbs written to CSV | Regenerate with default `--strong-weight-unit kg` |
| Weights off by a fraction (319.89 vs 320) | Insufficient kg precision | Use current script (adaptive precision in `lbs_to_strong_kg`) |
| Duplicate exercises in Hevy | Unmapped SugarWOD lift names | Add to `EXERCISE_NAME_MAP`, revert, re-import |
| Cindy score missing from Reps | `Rounds + Reps` WODs store score in Notes only | Expected behavior — see [docs/LEARNINGS.md](docs/LEARNINGS.md) |

---

## Ground rules

- ALWAYS ask the user to confirm weight units before running the converter
- ALWAYS validate the output CSV and get user confirmation before Hevy import
- ALWAYS warn about the one-import-per-account limit
- ALWAYS tell the user about the Revert Data Import trick after import
- NEVER commit files from `input/`, `output/`, or any `*.csv` containing personal workout data
- NEVER use `--strong-weight-unit lbs` unless the user explicitly wants legacy/debug behavior
- PREFER default flags (`lbs` in, `kg` out) for US CrossFit users
- PREFER linking to `docs/*` over restating full schema details in conversation
