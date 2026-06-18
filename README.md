# SugarWod to Hevy

Convert a SugarWod workout export (`workouts.csv`) into the **Strong app CSV format** that Hevy accepts via **Import Strong CSV**.

```mermaid
flowchart LR
  sugarwod["SugarWOD app export"] --> csvIn["input/workouts.csv gitignored"]
  csvIn --> runpy["run.py"]
  runpy --> csvOut["output/workouts_hevy.csv gitignored"]
  csvOut --> hevy["Hevy Import Strong CSV"]
```

**Three steps:** export from SugarWOD → convert → import into Hevy.

**Last tested:** June 18, 2026 — SugarWOD **10.1.1** (iOS), Hevy **3.0.15** (iOS). Export and import flows can change in future app updates; if something breaks, [open an issue](https://github.com/smyrick/sugarwod-to-hevy/issues).

---

## Pick your path

| Path | Who it's for | What to run |
|------|--------------|-------------|
| **A — AI agent** | Cursor, Claude Code, or any agent with [Agent Skills](https://agentskills.io/specification) | Open this repo and ask your agent to migrate your data. It follows [SKILL.md](SKILL.md) and runs `run.py` for you. |
| **B — One command, no clone** | Comfortable with a terminal, don't want git | See [no-clone one-liner](#one-command-no-clone) below |
| **C — Guided script** | Downloaded or cloned the repo, want prompts | `python3 run.py` |
| **D — Power user** | Know CLI flags, scripting | `python3 convert_sugarwod_to_hevy.py` — see [docs/USAGE.md](docs/USAGE.md) |

Paths **A** and **C** run the same guided flow (`run.py`); the agent adds judgment at the weight-unit and pre-import confirmation steps.

Requires **Python 3** (stdlib only — no pip install for conversion).

---

## One command, no clone

If you already have `workouts.csv` from SugarWOD (usually in Downloads):

```bash
curl -fsSL https://raw.githubusercontent.com/smyrick/sugarwod-to-hevy/main/convert_sugarwod_to_hevy.py \
  | python3 - ~/Downloads/workouts.csv -o workouts_hevy.csv
```

For the full guided experience (auto-locate export, verify header, validation summary):

```bash
curl -fsSL https://raw.githubusercontent.com/smyrick/sugarwod-to-hevy/main/run.py -o run.py
curl -fsSL https://raw.githubusercontent.com/smyrick/sugarwod-to-hevy/main/convert_sugarwod_to_hevy.py -o convert_sugarwod_to_hevy.py
python3 run.py
```

Then import `workouts_hevy.csv` into Hevy — [docs/IMPORT_HEVY.md](docs/IMPORT_HEVY.md).

---

## Quick start (cloned repo)

```bash
python3 run.py
```

`run.py` will find your export, verify it, convert it, and print what to do next. Put your SugarWOD file at `input/workouts.csv` or leave it in Downloads.

New to git or Python? Start with [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md).

---

## Privacy

Personal workout data stays out of git:

```
sugarwod-to-hevy/
  input/workouts.csv       ← your SugarWod export (you provide)
  output/workouts_hevy.csv ← generated Strong CSV for Hevy
```

Both folders are gitignored. The `.gitignore` also blocks `*.csv` repo-wide. **Never commit workout exports** — even on forks.

---

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) | Install Python, download ZIP vs git clone, file layout |
| [docs/EXPORT_SUGARWOD.md](docs/EXPORT_SUGARWOD.md) | Export workouts from the SugarWOD app |
| [docs/USAGE.md](docs/USAGE.md) | `run.py`, converter CLI, weight units, validation, tests |
| [docs/IMPORT_HEVY.md](docs/IMPORT_HEVY.md) | Import Strong CSV, revert, re-import after fixes |
| [docs/SUGARWOD_FORMAT.md](docs/SUGARWOD_FORMAT.md) | Input CSV schema |
| [docs/STRONG_FORMAT.md](docs/STRONG_FORMAT.md) | Output CSV schema |
| [docs/LEARNINGS.md](docs/LEARNINGS.md) | Weight rounding, Hevy quirks, migration pitfalls |
| [SKILL.md](SKILL.md) | Agent Skill — guided migration for AI assistants |

---

## License

Apache-2.0 — see [LICENSE](LICENSE).
