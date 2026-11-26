import pandas as pd
from collections import defaultdict
from pybaseball import playerid_reverse_lookup

# =============================
# Basic settings
# =============================
REACH_EVENTS = ['single', 'double', 'triple', 'hr', 'walk', 'hbp', 'sf', 'sh']

def init_counter():
    return {e: 0 for e in REACH_EVENTS}

# SB / CS containers
sb2 = defaultdict(init_counter)
sb3 = defaultdict(init_counter)
sbh = defaultdict(init_counter)

cs2 = defaultdict(init_counter)
cs3 = defaultdict(init_counter)
csh = defaultdict(init_counter)  # not used for the wOBA deduction

# =============================
# Trace back the event that put the runner on base
# =============================
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

# =============================
# Load Retrosheet play-by-play data
# =============================
df_rs = pd.read_csv('2025plays.csv')

for idx, row in df_rs.iterrows():

    # ----- SB -----
    if row.get('sb2', 0) == 1:
        ev = find_reach_event(df_rs, idx, row.get('br1_pre'))
        if ev:
            sb2[row['br1_pre']][ev] += 1

    if row.get('sb3', 0) == 1:
        ev = find_reach_event(df_rs, idx, row.get('br2_pre'))
        if ev and ev not in ['single', 'walk', 'hbp']:
            sb3[row['br2_pre']][ev] += 1

    if row.get('sbh', 0) == 1:
        ev = find_reach_event(df_rs, idx, row.get('br3_pre'))
        if ev:
            sbh[row['br3_pre']][ev] += 1

    # ----- CS -----
    if row.get('cs2', 0) == 1:
        ev = find_reach_event(df_rs, idx, row.get('br1_pre'))
        if ev:
            cs2[row['br1_pre']][ev] += 1

    if row.get('cs3', 0) == 1:
        ev = find_reach_event(df_rs, idx, row.get('br2_pre'))
        if ev and ev not in ['single', 'walk', 'hbp']:
            cs3[row['br2_pre']][ev] += 1

    if row.get('csh', 0) == 1:
        ev = find_reach_event(df_rs, idx, row.get('br3_pre'))
        if ev:
            csh[row['br3_pre']][ev] += 1

# =============================
# Build df2
# =============================
def to_df(d, label):
    out = pd.DataFrame.from_dict(d, orient='index').fillna(0)
    out.index.name = 'retro_id'
    out = out.reset_index()
    out['type'] = label
    return out

df2 = pd.concat([
    to_df(sb2, 'SB_2B'),
    to_df(sb3, 'SB_3B'),
    to_df(sbh, 'SB_H'),
    to_df(cs2, 'CS_2B'),
    to_df(cs3, 'CS_3B'),
    to_df(csh, 'CS_H')
], ignore_index=True)

# =============================
# Map Retrosheet IDs -> MLBAM IDs
# =============================
retro_ids = df2['retro_id'].dropna().unique().tolist()

id_map = playerid_reverse_lookup(retro_ids, key_type='retro')
id_map = id_map[['key_retro', 'key_mlbam']]

df2 = df2.merge(
    id_map,
    left_on='retro_id',
    right_on='key_retro',
    how='left'
)

df2 = df2.dropna(subset=['key_mlbam'])
df2['player_id'] = df2['key_mlbam'].astype(int)
df2 = df2.drop(columns=['retro_id', 'key_retro', 'key_mlbam'])

# =============================
# Aggregate SB upgrades
# =============================
sb2_df = df2[df2['type'] == 'SB_2B']
sb3_df = df2[df2['type'] == 'SB_3B']
sbh_df = df2[df2['type'] == 'SB_H']

upgrade_2b = (
    sb2_df.groupby('player_id')[['single', 'walk', 'hbp']]
    .sum()
    .rename(columns={
        'single': 'single_to_2b',
        'walk': 'walk_to_2b',
        'hbp': 'hbp_to_2b'
    })
)

upgrade_3b = (
    sb3_df.groupby('player_id')[['double']]
    .sum()
    .rename(columns={'double': 'double_to_3b'})
)

upgrade_hr = (
    sbh_df.groupby('player_id')[['triple']]
    .sum()
    .rename(columns={'triple': 'triple_to_hr'})
)

# =============================
# Aggregate CS downgrades (CS_H excluded)
# =============================
cs2_df = df2[df2['type'] == 'CS_2B']
cs3_df = df2[df2['type'] == 'CS_3B']

downgrade_2b = (
    cs2_df.groupby('player_id')[['single', 'walk', 'hbp']]
    .sum()
    .rename(columns={
        'single': 'cs_single',
        'walk': 'cs_walk',
        'hbp': 'cs_hbp'
    })
)

downgrade_3b = (
    cs3_df.groupby('player_id')[['double']]
    .sum()
    .rename(columns={'double': 'cs_double'})
)

# =============================
# Load the original wOBA data
# =============================
df = pd.read_csv('wOBA_and_steal.csv')
df = df[df['year'] == 2025]

# =============================
# Merge
# =============================
for d in [upgrade_2b, upgrade_3b, upgrade_hr, downgrade_2b, downgrade_3b]:
    df = df.merge(d, on='player_id', how='left')

df.fillna(0, inplace=True)

# =============================
# Adjust events
# =============================
df['mod_1B'] = (
    df['single']
    - df['single_to_2b']
    - df['cs_single']
)

df['mod_2B'] = (
    df['double']
    + df['single_to_2b']
    + df['walk_to_2b']
    + df['hbp_to_2b']
    - df['double_to_3b']
    - df['cs_double']
)

df['mod_3B'] = (
    df['triple']
    + df['double_to_3b']
    - df['triple_to_hr']
)

df['mod_HR'] = (
    df['home_run']
    + df['triple_to_hr']
)

df['mod_BB'] = (
    df['walk']
    - df['walk_to_2b']
    - df['cs_walk']
)

df['mod_HBP'] = (
    df['b_hit_by_pitch']
    - df['hbp_to_2b']
    - df['cs_hbp']
)

# =============================
# Recalculate wOBA
# =============================
wBB = 0.691
wHBP = 0.722
w1B = 0.882
w2B = 1.252
w3B = 1.584
wHR = 2.037

df['wR_mod'] = (
    w1B * df['mod_1B']
    + w2B * df['mod_2B']
    + w3B * df['mod_3B']
    + wHR * df['mod_HR']
    + wBB * (df['mod_BB'] - df['b_intent_walk'])
    + wHBP * df['mod_HBP']
)

df['ab_from_non_ab_events'] = (
    df['walk_to_2b']
    + df['cs_walk']
    + df['hbp_to_2b']
    + df['cs_hbp']
)

df['den_mod'] = (
    df['ab']
    + df['ab_from_non_ab_events']
    + df['mod_BB']
    - df['b_intent_walk']
    + df['b_sac_fly']
    + df['mod_HBP']
)

df['wOBA_mod'] = (df['wR_mod'] / df['den_mod'])
df['weighted_run'] = w1B * df['single'] + w2B * df['double'] + w3B * df['triple'] + wHR * df['home_run'] + wBB * (df['walk'] - df['b_intent_walk']) + wHBP * df['b_hit_by_pitch']
df['den'] = df['ab'] + df['walk'] - df['b_intent_walk'] + df['b_sac_fly'] + df['b_hit_by_pitch']
df['cal_wOBA'] = df['weighted_run'] / df['den']

df['diff'] = round(df['wOBA_mod'] - df['cal_wOBA'],3)
df['real_minus_cal'] = round(df['cal_wOBA'] - df['woba'])
df.sort_values('diff', ascending=False, inplace=True)

df['cs'] = df['r_caught_stealing_2b'] + df['r_caught_stealing_3b']
df['sb'] = df['r_stolen_base_2b']+df['r_stolen_base_3b']

cols = ['last_name, first_name', 'player_id', 'year', 'den', 'den_mod', 'woba', 'cal_wOBA', 'wOBA_mod','diff', 'sb', 'cs']
df_adj = df[cols]

df.to_csv('wOBA_steal_adj_all.csv', index=False)
df_adj.to_csv('wOBA_steal_adj.csv', index=False)
# print(df.head())