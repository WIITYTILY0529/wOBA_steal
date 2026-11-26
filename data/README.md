# Data

## Raw

- `raw/wOBA_and_steal.csv`: Season batting and baserunning totals for 2021–2025 (one row per player-season).
  This is the source input; do not modify or overwrite it.
- `raw/2025plays.csv`: 2025 Retrosheet play-by-play data. Not included; see the main
  [README](../README.md#reproducing-the-adjustment-from-scratch).

## Interim

- `interim/result_with_mlb_id.csv`: Reaching-event counts per steal type, with runner IDs mapped to MLBAM IDs
- `interim/temp2.csv`: Steal events traced from Statcast play descriptions
- `interim/temp3.csv`: Reaching-event counts per steal type, keyed by Retrosheet runner ID
- `interim/wOBA_steal_adj.csv`: Adjusted-wOBA table used in the final merge
