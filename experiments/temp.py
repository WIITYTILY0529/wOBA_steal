from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]

import pandas as pd
from collections import defaultdict

REACH_EVENTS = ['single', 'double', 'triple', 'hr', 'sh', 'sf', 'hbp', 'walk']

def init_counter():
    return {e: 0 for e in REACH_EVENTS}

# runner_id -> event counter
sb2_cnt = defaultdict(init_counter)
sb3_cnt = defaultdict(init_counter)
sbh_cnt = defaultdict(init_counter)

cs2_cnt = defaultdict(init_counter)
cs3_cnt = defaultdict(init_counter)
csh_cnt = defaultdict(init_counter)

def find_reach_event(df, start_idx, runner_id):
    if pd.isna(runner_id):
        return None

    i = start_idx - 1
    while i >= 0:
        row = df.iloc[i]
        if row['batter'] == runner_id:
            for ev in REACH_EVENTS:
                if row.get(ev, 0) == 1:
                    return ev
            return None
        i -= 1

    return None

df = pd.read_csv(str(PROJECT_ROOT / 'data/raw/2025plays.csv'))

for idx, row in df.iterrows():

    # ---------- SB ----------
    if row.get('sb2', 0) == 1:
        runner = row.get('br1_pre')
        ev = find_reach_event(df, idx, runner)
        if ev:
            sb2_cnt[runner][ev] += 1

    if row.get('sb3', 0) == 1:
        runner = row.get('br2_pre')
        ev = find_reach_event(df, idx, runner)
        if ev:
            sb3_cnt[runner][ev] += 1

    if row.get('sbh', 0) == 1:
        runner = row.get('br3_pre')
        ev = find_reach_event(df, idx, runner)
        if ev:
            sbh_cnt[runner][ev] += 1

    # ---------- CS ----------
    if row.get('cs2', 0) == 1:
        runner = row.get('br1_pre')
        ev = find_reach_event(df, idx, runner)
        if ev:
            cs2_cnt[runner][ev] += 1

    if row.get('cs3', 0) == 1:
        runner = row.get('br2_pre')
        ev = find_reach_event(df, idx, runner)
        if ev:
            cs3_cnt[runner][ev] += 1

    if row.get('csh', 0) == 1:
        runner = row.get('br3_pre')
        ev = find_reach_event(df, idx, runner)
        if ev:
            csh_cnt[runner][ev] += 1

# Convert dict -> DataFrame
def to_df(cnt_dict, label):
    df_out = pd.DataFrame.from_dict(cnt_dict, orient='index')
    df_out.index.name = 'runner_id'
    df_out = df_out.reset_index()
    df_out['type'] = label
    return df_out

result_df = pd.concat([
    to_df(sb2_cnt, 'SB_2B'),
    to_df(sb3_cnt, 'SB_3B'),
    to_df(sbh_cnt, 'SB_H'),
    to_df(cs2_cnt, 'CS_2B'),
    to_df(cs3_cnt, 'CS_3B'),
    to_df(csh_cnt, 'CS_H')
], ignore_index=True)

# result_df.to_csv('temp3.csv')

# print(result_df.head())

from pybaseball import playerid_reverse_lookup

unique_retro_ids = result_df['runner_id'].unique().tolist()

print("Loading the ID mapping table...")
id_map_df = playerid_reverse_lookup(unique_retro_ids, key_type='retro')

id_map = id_map_df[['key_retro', 'key_mlbam']]

result_with_mlb = pd.merge(
    result_df, 
    id_map, 
    left_on='runner_id', 
    right_on='key_retro', 
    how='left'
)

result_with_mlb['runner_id'] = result_with_mlb['key_mlbam'].fillna(result_with_mlb['runner_id'])

result_with_mlb = result_with_mlb.drop(columns=['key_retro', 'key_mlbam'])

print(result_with_mlb.head())

result_with_mlb.to_csv('result_with_mlb_id.csv', index=False)