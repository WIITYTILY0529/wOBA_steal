import pandas as pd

df = pd.read_csv('wOBA_and_steal.csv')
df = df[df['year'] == '2025']

wBB = 0.691
wHBP = 0.722
w1B = 0.882
w2B = 1.252
w3B = 1.584
wHR = 2.037

df['weighted_run'] = w1B * df['single'] + w2B * df['double'] + w3B * df['triple'] + wHR * df['home_run'] + wBB * df['walk'] + wHBP * df['b_hit_by_pitch']
df['den'] = df['ab'] + df['walk'] - df['b_intent_walk'] + df['b_sac_fly'] + df['b_hit_by_pitch']
df['cal_wOBA'] = round(df['weighted_run'] / df['den'], 3)

df['single_to_2B'] = df[['single', 'r_stolen_base_2b']].min(axis=1)
df['double_to_3B'] = df[['double', 'r_stolen_base_3b']].min(axis=1)

df['mod_1B'] = df['single'] - df['single_to_2B']
df['mod_2B'] = df['double'] + df['single_to_2B'] - df['double_to_3B']
df['mod_3B'] = df['triple'] + df['double_to_3B']

df['extra_out'] = df['r_caught_stealing_2b'] + df['r_caught_stealing_3b']

df['wR_mod'] = (
      w1B * df['mod_1B']
    + w2B * df['mod_2B']
    + w3B * df['mod_3B']
    + wHR * df['home_run']
    + wBB * df['walk']
    + wHBP * df['b_hit_by_pitch']
)

df['den_mod'] = (
      df['ab']
    + df['walk'] - df['b_intent_walk']
    + df['b_sac_fly']
    + df['b_hit_by_pitch']
    + df['extra_out']
)

df['wOBA_mod'] = (df['wR_mod'] / df['den_mod']).round(3)
df['diff'] = round(df['wOBA_mod'] - df['cal_wOBA'],3)
df_mod = df[['last_name, first_name', 'cal_wOBA', 'wOBA_mod', 'diff']]

# print(df_mod)