# wOBA Steal

A research project that folds stolen bases and caught stealing into wOBA.

Standard wOBA credits a batter only for the base reached on the plate appearance itself. This project
credits the extra base a runner gains by stealing, and charges the out a runner gives up when caught
stealing, to the plate appearance that put the runner on base. A stolen-base-adjusted wOBA (`wOBA_mod`)
is then recalculated with the same linear weights and compared with the standard value (`cal_wOBA`).

## Method

For each stolen base or caught stealing, the play-by-play data is traced back to the plate appearance in
which that runner reached base. The reaching event is then reclassified:

| Running event | Reaching event | Adjustment |
| --- | --- | --- |
| Steal of 2nd | single, walk, HBP | counted as a double |
| Steal of 3rd | double | counted as a triple |
| Steal of home | triple | counted as a home run |
| Caught stealing 2nd | single, walk, HBP | removed (counted as an out) |
| Caught stealing 3rd | double | removed (counted as an out) |

Walks and HBP that are converted (to a double or an out) are added to the denominator as at-bat events.
Caught stealing at home is tracked but not used in the adjustment. Both wOBA values use these weights:

| uBB | HBP | 1B | 2B | 3B | HR |
| --- | --- | --- | --- | --- | --- |
| 0.691 | 0.722 | 0.882 | 1.252 | 1.584 | 2.037 |

The full calculation is in [`reference/main.py`](reference/main.py).

## Repository layout

```text
.
├── data/
│   ├── raw/            Source input data
│   └── interim/        Event mappings and intermediate adjusted-wOBA tables
├── scripts/            Script that produces the current final table
├── reference/          Core calculation (reference code)
├── experiments/        Earlier and alternative approaches
├── debug/              Debugging code for Statcast event tracing
├── outputs/tables/     Generated result tables
├── pyproject.toml
├── requirements-windows.txt
└── requirements-windows.lock.txt
```

See [`data/README.md`](data/README.md) and [`outputs/README.md`](outputs/README.md) for a description of
each file.

## Code

| File | Role |
| --- | --- |
| `scripts/wOBA_steal_adj.py` | Final step: merges the adjusted wOBA table with the 2025 season stats |
| `reference/main.py` | Core calculation: aggregates steal events and computes the adjusted wOBA |
| `experiments/wOBA_with_steal.py` | Early, simplified adjustment based on season totals only |
| `experiments/temp.py` | Retrosheet-based event aggregation and Retrosheet-to-MLBAM ID mapping |
| `experiments/temp2.py` | Statcast play-description-based steal tracking |
| `debug/debug.py` | Debugging trace for Statcast-based event tracking |

## Setup

Python 3.10 or newer is required (developed with Python 3.12 on Windows).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-windows.txt
```

`requirements-windows.txt` lists the direct dependencies; `requirements-windows.lock.txt` pins the exact
versions used. On macOS or Linux, activate the environment with `source .venv/bin/activate`.

## Usage

Build the final table from the files included in this repository:

```powershell
python scripts\wOBA_steal_adj.py
```

- Inputs: `data/raw/wOBA_and_steal.csv`, `data/interim/wOBA_steal_adj.csv`
- Output: `outputs/tables/final.csv`

### Reproducing the adjustment from scratch

`reference/main.py` and `experiments/temp.py` need the 2025 Retrosheet play-by-play file
(`2025plays.csv`), which is not included in this repository. Download it from
[Retrosheet](https://www.retrosheet.org/) and save it as `data/raw/2025plays.csv`.

These scripts also look up player IDs online through `pybaseball`, and `reference/main.py`,
`experiments/wOBA_with_steal.py`, and `experiments/temp2.py` read and write CSV files in the current
working directory. They are kept as reference code for the research process, not as one-step
reproducible scripts. `experiments/temp2.py` and `debug/debug.py` download Statcast data through
`pybaseball` and can take a long time.

## Example results

The five largest gains in `outputs/tables/final.csv` (2025 season):

| Player | wOBA | Adjusted wOBA | Difference | SB | CS |
| --- | --- | --- | --- | --- | --- |
| Oneil Cruz | .295 | .318 | +.023 | 38 | 5 |
| Trevor Story | .320 | .339 | +.019 | 31 | 1 |
| CJ Abrams | .324 | .342 | +.018 | 31 | 3 |
| Juan Soto | .390 | .407 | +.017 | 38 | 4 |
| Randy Arozarena | .332 | .348 | +.016 | 31 | 6 |

## Data sources

- Season batting and baserunning totals in the Baseball Savant custom leaderboard format.
- Statcast pitch-level data, accessed through [pybaseball](https://github.com/jldbc/pybaseball).
- Retrosheet play-by-play data.

The information used here was obtained free of charge from and is copyrighted by Retrosheet. Interested
parties may contact Retrosheet at [www.retrosheet.org](https://www.retrosheet.org/).
