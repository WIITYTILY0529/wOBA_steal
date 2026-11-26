from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "wOBA_and_steal.csv"
ADJUSTED_PATH = ROOT / "data" / "interim" / "wOBA_steal_adj.csv"
OUTPUT_PATH = ROOT / "outputs" / "tables" / "final.csv"


def main():
    df = pd.read_csv(RAW_PATH)
    df = df[df['year'] == 2025]


    df2 = pd.read_csv(ADJUSTED_PATH)
    df2 = df2.loc[:, ~df2.columns.str.startswith('Unnamed:')]
    df['sb'] = df['r_stolen_base_2b']+df['r_stolen_base_3b']
    df['cs'] = df['r_caught_stealing_2b'] + df['r_caught_stealing_3b']

    df3 = pd.merge(df, df2, on = 'player_id', how = 'outer')
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df3.to_csv(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    main()
