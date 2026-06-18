# Getting started

This guide is for people who found this project on the internet and want to migrate SugarWOD workout history into Hevy without being a developer.

**Overview:** [README.md](../README.md)

---

## What you need

1. **Python 3** — already installed on most Macs. Check:

   ```bash
   python3 --version
   ```

   If that fails, install Python 3 from [python.org](https://www.python.org/downloads/) or your system package manager.

2. **A SugarWOD export** — see [EXPORT_SUGARWOD.md](EXPORT_SUGARWOD.md).

3. **The Hevy app** on your phone (for import).

No `pip install` is required for conversion — the scripts use only Python's built-in libraries.

---

## Get the code

Pick one:

### Option A — Download ZIP (easiest, no git)

1. Open [github.com/smyrick/sugarwod-to-hevy](https://github.com/smyrick/sugarwod-to-hevy)
2. Click **Code** → **Download ZIP**
3. Unzip to a folder (e.g. `~/Downloads/sugarwod-to-hevy`)
4. Open Terminal and `cd` into that folder:

   ```bash
   cd ~/Downloads/sugarwod-to-hevy
   ```

### Option B — Git clone

If you have git installed:

```bash
git clone https://github.com/smyrick/sugarwod-to-hevy.git
cd sugarwod-to-hevy
```

### Option C — No download at all

Use the [one-command no-clone method](../README.md#one-command-no-clone) from the README if you only want to convert a file and don't need the full repo.

---

## File layout

After you have the repo (or downloaded scripts), your personal data goes in two local folders:

```
sugarwod-to-hevy/
  input/workouts.csv       ← put your SugarWOD export here
  output/workouts_hevy.csv ← created by the converter
```

Both folders are gitignored — your workout data never gets committed.

You can also leave `workouts.csv` in **Downloads**; `run.py` will find it automatically.

---

## Run the converter

From the project folder:

```bash
python3 run.py
```

The script will:

1. Find your SugarWOD export
2. Verify it looks correct
3. Ask about weight units (default: pounds)
4. Write `output/workouts_hevy.csv`
5. Print validation checks and Hevy import instructions

---

## Using an AI assistant instead

If you use Cursor, Claude Code, or similar:

1. Open this folder in your editor
2. Ask: *"Migrate my SugarWOD workouts to Hevy"*
3. The agent follows [SKILL.md](../SKILL.md) and runs the scripts for you

You still need Python 3 installed locally.

---

## Next steps

1. [Export from SugarWOD](EXPORT_SUGARWOD.md)
2. [Usage details](USAGE.md) — CLI flags, weight units, troubleshooting
3. [Import into Hevy](IMPORT_HEVY.md)
