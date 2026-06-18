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
  version: "1.1.0"
allowed-tools: Read Write Edit Shell Glob Grep
---

# SugarWOD to Hevy migration

Walk the user through converting a SugarWOD `workouts.csv` export into Strong CSV format for Hevy's **Import Strong CSV** flow. Run the guided orchestrator (`run.py`) — do not re-implement locate/verify/convert/validate by hand.

**Reference docs (read as needed, do not duplicate in chat):**

- [README.md](README.md) — overview and pick-your-path
- [run.py](run.py) — guided orchestrator (locate, verify, convert, validate, next steps)
- [docs/EXPORT_SUGARWOD.md](docs/EXPORT_SUGARWOD.md) — how to export from SugarWOD
- [docs/IMPORT_HEVY.md](docs/IMPORT_HEVY.md) — Hevy import, revert, re-import
- [docs/SUGARWOD_FORMAT.md](docs/SUGARWOD_FORMAT.md) — input CSV schema
- [docs/STRONG_FORMAT.md](docs/STRONG_FORMAT.md) — output CSV schema and validation
- [docs/LEARNINGS.md](docs/LEARNINGS.md) — weight units, Hevy quirks, spot checks

---

## Process

Follow these steps in order. Pause for user confirmation at each gate marked **ASK**.

- [ ] Step 1: Locate export (if needed) **ASK**
- [ ] Step 2: Confirm weight units **ASK**
- [ ] Step 3: Run `run.py`
- [ ] Step 4: Relay output and confirm before import **ASK**
- [ ] Step 5: Import into Hevy
- [ ] Step 6: Revert safety net (if needed)

---

## Step 1: Locate export (if needed)

**ASK:** Where is your SugarWOD `workouts.csv`? Common locations: Downloads, email attachment, or `input/workouts.csv` in this repo.

If the user does not have an export yet, guide them using [docs/EXPORT_SUGARWOD.md](docs/EXPORT_SUGARWOD.md).

**Privacy:** `input/` and `output/` are gitignored. Personal workout data must never be committed. The `.gitignore` also blocks `*.csv` repo-wide as a safety net.

---

## Step 2: Confirm weight units

**ASK before running.** Do not assume units.

### The core gotcha

The Strong CSV has a single `Weight` column with **no unit field**. Hevy's **Import Strong CSV** treats every `Weight` value as **kilograms**, then converts to the user's display preference (e.g. lbs).

SugarWOD barbell loads are typically **pounds** (US CrossFit). If you write raw pound numbers into the CSV, Hevy reads them as kg and weights appear **~2.2× too heavy** (320 lbs in SugarWOD → ~705 lbs in Hevy).

Details: [docs/LEARNINGS.md](docs/LEARNINGS.md#hevy-treats-strong-csv-weights-as-kilograms)

### Questions to ask the user

1. **What unit are your SugarWOD barbell loads in?**
   - Default for US CrossFit: **lbs** → `--input-weight-unit lbs`
   - If already in kg: `--input-weight-unit kg`

2. **What unit does Hevy display weights in?**
   - Most US users: **lbs**
   - This does not change the CSV — Hevy always imports kg internally

### Recommended defaults

| Situation | Flags |
|-----------|-------|
| US CrossFit logs, Hevy display in lbs | `--input-weight-unit lbs` (default; `run.py` writes kg) |
| SugarWOD loads already in kg | `--input-weight-unit kg` |
| Debug only — weights will be ~2.2× too heavy | `--strong-weight-unit lbs` |

Confirm the chosen `--input-weight-unit` with the user before proceeding.

---

## Step 3: Run `run.py`

Requires Python 3 only — no pip install. Run non-interactively so prompts do not block:

```bash
python3 run.py "<export path>" --input-weight-unit <lbs|kg> --yes
```

Omit the path to let `run.py` auto-locate (`input/workouts.csv` or newest `*workouts*.csv` in Downloads):

```bash
python3 run.py --input-weight-unit lbs --yes
```

`run.py` handles:

- Verifying the file is a real SugarWOD export (header check via `is_sugarwod_export()` in [convert_sugarwod_to_hevy.py](convert_sugarwod_to_hevy.py); canonical header: `SUGARWOD_HEADERS`)
- Converting to Strong CSV (default output: `output/workouts_hevy.csv`)
- Printing a validation spot-check summary
- Printing Hevy import next steps

If `run.py` exits non-zero, read stderr and help the user fix the issue (wrong file → [docs/EXPORT_SUGARWOD.md](docs/EXPORT_SUGARWOD.md)).

Expected header (quick reference; canonical source is `SUGARWOD_HEADERS` in the converter):

```text
date,title,description,best_result_raw,best_result_display,score_type,barbell_lift,set_details,notes,rx_or_scaled,pr
```

---

## Step 4: Relay output and confirm before import

Present `run.py`'s printed summary to the user:

- Deduplication count (if any)
- Skipped unparseable rows (with warnings)
- Final count: `N SugarWod workouts → M Strong-format set rows`
- Validation spot-check (load sample, timed WOD sample)
- Output path: `output/workouts_hevy.csv`

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

## Step 5: Import into Hevy

Guide the user using [docs/IMPORT_HEVY.md](docs/IMPORT_HEVY.md):

1. Open Hevy → **Profile** → **Settings** → **Export & Import Data** → **Import Data**
2. Tap **Import Strong CSV** (not a generic file upload)
3. Select `output/workouts_hevy.csv`
4. Wait for "Workout data successfully imported!"

**Constraints:**

- Hevy allows **one** Strong CSV import per account. Revert any previous import first.
- Column headers must be in English exactly as listed in [docs/STRONG_FORMAT.md](docs/STRONG_FORMAT.md).

After import, ask the user to spot-check 1–2 known sessions in Hevy (a recent squat/bench and a timed WOD like Murph).

---

## Step 6: Revert safety net

If weights or exercises look wrong after import, the user can undo **without leaving the Import Data screen**.

![Hevy Import Data screen showing Revert Data Import](docs/images/hevy-import-revert.png)

### The trick

Right after a successful import:

1. **Stay on the Import Data screen** — do not navigate away from Settings entirely
2. You can tap **Home** or **Profile** on the bottom nav and come back
3. The **Revert Data Import** link (red text) remains available
4. Tap it to remove the imported data and try again

### Full re-import loop

If the user needs to fix the CSV and re-import:

1. **Revert Data Import** (while still on the Import Data screen, or via Settings → Export & Import Data)
2. Re-run `python3 run.py "<path>" --input-weight-unit <unit> --yes`
3. Re-validate (Step 4)
4. Import Strong CSV again

See also: [docs/LEARNINGS.md](docs/LEARNINGS.md#hevy-allows-only-one-strong-csv-import)

---

## Quick reference

### `run.py` arguments

| Argument | Default | Purpose |
|----------|---------|---------|
| `input` | auto-locate | Path to SugarWOD export |
| `-o`, `--output` | `output/workouts_hevy.csv` | Strong CSV destination |
| `--input-weight-unit` | `lbs` | Unit of load values in SugarWOD |
| `--strong-weight-unit` | `kg` | Unit written to Strong `Weight` column |
| `-y`, `--yes` | off | Non-interactive; never prompt |

### Common symptoms

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Weights ~2.2× too heavy in Hevy | Raw lbs written to CSV | Re-run with default `--strong-weight-unit kg` |
| Weights off by a fraction (319.89 vs 320) | Insufficient kg precision | Use current script (adaptive precision in `lbs_to_strong_kg`) |
| Duplicate exercises in Hevy | Unmapped SugarWOD lift names | Add to `EXERCISE_NAME_MAP`, revert, re-import |
| Cindy score missing from Reps | `Rounds + Reps` WODs store score in Notes only | Expected behavior — see [docs/LEARNINGS.md](docs/LEARNINGS.md) |

---

## Ground rules

- ALWAYS ask the user to confirm weight units before running `run.py`
- ALWAYS run `run.py` with `--yes` (non-interactive) — do not invoke the converter directly unless debugging
- ALWAYS relay `run.py`'s validation summary and get user confirmation before Hevy import
- ALWAYS warn about the one-import-per-account limit
- ALWAYS tell the user about the Revert Data Import trick after import
- NEVER commit files from `input/`, `output/`, or any `*.csv` containing personal workout data
- NEVER use `--strong-weight-unit lbs` unless the user explicitly wants legacy/debug behavior
- PREFER default flags (`lbs` in, `kg` out) for US CrossFit users
- PREFER linking to `docs/*` over restating full schema details in conversation
