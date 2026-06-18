# Import into Hevy

How to import your converted Strong CSV into Hevy, revert if needed, and re-import after fixes.

**Previous:** [USAGE.md](USAGE.md) · **Overview:** [README.md](../README.md)

---

## Import steps

1. Open Hevy → **Profile** → **Settings** → **Export & Import Data** → **Import Data**
2. Tap **Import Strong CSV** (not a generic file upload)
3. Select `output/workouts_hevy.csv` (AirDrop, email, cloud drive, or Files app)
4. Wait for "Workout data successfully imported!"

**Important:**

- Hevy only allows **one** Strong CSV import per account. If you already imported a file, revert/remove it before trying again.
- Column headers must be in English exactly as listed in [STRONG_FORMAT.md](STRONG_FORMAT.md).

After import, spot-check 1–2 known sessions (a recent squat/bench and a timed WOD like Murph).

---

## Revert / undo an import

Right after a successful import, you can undo it **without leaving the Import Data screen**:

1. Stay on **Profile** → **Settings** → **Export & Import Data** → **Import Data** (or return via **Home** / **Profile** bottom nav)
2. Tap the red **Revert Data Import** link

![Hevy Import Data screen with Revert Data Import](images/hevy-import-revert.png)

The revert option stays available while you flip between **Home** and **Profile** — use this to spot-check workouts in Hevy before committing. Once you navigate away from the import flow entirely, you may need to revert from Settings instead.

---

## Re-import after a weight fix

If you previously imported with inflated weights (~2.2× too heavy in Hevy):

1. Hevy → Profile → Settings → Export & Import Data → **revert/remove** the old import
2. Regenerate the CSV (default writes kg):

   ```bash
   python3 run.py --yes
   ```

3. Import Strong CSV again
4. Spot-check a known lift (e.g. a 320 lb squat should show ~320 lbs in Hevy, not ~705 lbs)

See [LEARNINGS.md](LEARNINGS.md#hevy-treats-strong-csv-weights-as-kilograms) for why weights can be wrong.

---

## Full re-import loop

1. **Revert Data Import** (on Import Data screen, or Settings → Export & Import Data)
2. Re-run `python3 run.py` with corrected flags
3. Validate output — [USAGE.md](USAGE.md#validation-checklist)
4. Import Strong CSV again

Hevy allows only one Strong CSV import per account: [LEARNINGS.md](LEARNINGS.md#hevy-allows-only-one-strong-csv-import)
