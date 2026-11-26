import re
import pandas as pd
from pybaseball import statcast

# Load data (statcast returns rows in reverse chronological order)
df = statcast('2025-01-01', '2025-12-31')
df = df[df['game_type'] == 'R']
df = df.reset_index(drop=True)

def parse_running_events(desc):
    """
    Returns: list of ('type', 'base')
    type: 'steal' or 'cs'
    base: '2b' or '3b'
    """
    if pd.isna(desc):
        return []

    events = []

    if re.search(r'steals .* 2nd base', desc):
        events.append(('steal', '2b'))
    if re.search(r'steals .* 3rd base', desc):
        events.append(('steal', '3b'))
    if re.search(r'steals .* home', desc):
        events.append(('steal', 'home'))

    if re.search(r'caught stealing 2nd', desc):
        events.append(('cs', '2b'))
    if re.search(r'caught stealing 3rd', desc):
        events.append(('cs', '3b'))
    if re.search(r'caught stealing home', desc):
        events.append(('cs', 'home'))

    return events

def get_runner_id(row, base):
    if base == '2b':
        return row['on_1b']
    elif base == '3b':
        return row['on_2b']
    elif base == 'home':
        return row['on_3b']
    return None


def find_previous_reach_event(df, start_idx, runner_id):
    """
    Find the closest plate appearance before the steal (start_idx)
    in which runner_id reached base as the batter.
    """
    if pd.isna(runner_id):
        return None, None

    sub = df.loc[start_idx + 1:]

    cond = (sub['batter'] == runner_id) & (sub['events'].notna())
    hit = sub.loc[cond]

    if hit.empty:
        return None, None
    else:
        row = hit.iloc[0]
        return row['events'], row.name

records = []

for idx, row in df.iterrows():
    running_events = parse_running_events(row['des'])
    if not running_events:
        continue

    for ev_type, base in running_events:
        runner_id = get_runner_id(row, base)

        reach_event, reach_idx = find_previous_reach_event(df, idx, runner_id)

        records.append({
            'runner_id': runner_id,
            'game_date' : row['game_date'],
            'event_type': (
                f'steal_{base}' if ev_type == 'steal'
                else f'caught_steal_{base}'
            ),
             'from_base': (
                'on_1b' if base == '2b'
                else 'on_2b' if base == '3b'
                else 'on_3b'
            ),
            'trigger_row': idx,
            'trigger_des': row['des'],  
            'reach_event': reach_event,
            'reach_event_row': reach_idx
        })

result_df = pd.DataFrame(records)
result_df.to_csv('temp2.csv')
# df.to_csv('temp2-1.csv')
print(result_df)