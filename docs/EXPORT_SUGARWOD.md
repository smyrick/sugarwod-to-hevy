# Export from SugarWOD

How to get your `workouts.csv` file from the SugarWOD app.

**Previous:** [GETTING_STARTED.md](GETTING_STARTED.md) · **Next:** [USAGE.md](USAGE.md) · **Overview:** [README.md](../README.md)

---

## Steps

1. Open the **SugarWOD** app on your phone
2. Go to **More** (or the menu) → **Tools & Resources** → **Export Workouts**
3. Confirm the export — SugarWOD emails a CSV (usually named `workouts.csv`)
4. Save the attachment:
   - **Easiest:** leave it in **Downloads** — `run.py` finds it automatically
   - **Or:** copy it to `input/workouts.csv` in this repo (create the `input/` folder if needed)

---

## Before your subscription ends

Export **before** your SugarWOD subscription lapses if you are leaving the platform. You cannot export historical data after access ends.

---

## Verify the file

A real SugarWOD export has this header (first line of the CSV):

```text
date,title,description,best_result_raw,best_result_display,score_type,barbell_lift,set_details,notes,rx_or_scaled,pr
```

`run.py` checks this automatically. If conversion fails with a header error, you may have the wrong file (e.g. a Hevy export or a spreadsheet export).

Full input schema: [SUGARWOD_FORMAT.md](SUGARWOD_FORMAT.md)

---

## Privacy

Workout exports contain personal data. Keep them in `input/` or Downloads — never commit them to git. The repo `.gitignore` blocks `input/`, `output/`, and `*.csv` as a safety net.
