import re
import pandas as pd
from pybaseball import statcast

# 1. Load data (statcast returns newest -> oldest)
df = statcast('2025-04-01', '2025-04-02')

print('Original df shape:', df.shape)
print('Original top des (newest):')
print(df.loc[0, 'des'])
print('=' * 80)

# 2. Reverse chronological order (oldest -> newest)
df = df.iloc[::-1].reset_index(drop=True)

print('Top des after reversing (oldest):')
print(df.loc[0, 'des'])
print('=' * 80)

# 3. Check that the required columns exist
required_cols = ['des', 'batter', 'events', 'on_1b', 'on_2b']
print('Column check')
for c in required_cols:
    print(f'{c}:', 'OK' if c in df.columns else 'MISSING')
print('=' * 80)

# -----------------------------
# Function definitions (original structure kept)
# -----------------------------

def parse_running_events(desc):
    if pd.isna(desc):
        return []

    events = []

    if re.search(r'steals .* 2nd base', desc):
        events.append(('steal', '2b'))
    if re.search(r'steals .* 3rd base', desc):
        events.append(('steal', '3b'))
    if re.search(r'caught stealing 2nd', desc):
        events.append(('cs', '2b'))
    if re.search(r'caught stealing 3rd', desc):
        events.append(('cs', '3b'))

    return events

def get_runner_id(row, base):
    if base == '2b':
        return row['on_1b']
    elif base == '3b':
        return row['on_2b']
    return None

def find_next_batter_event(df, start_idx, runner_id, lookahead=50):
    if pd.isna(runner_id):
        return None, None

    sub = df.loc[start_idx + 1 : start_idx + 1 + lookahead]

    cond = (sub['batter'] == runner_id) & (sub['events'].notna())
    hit = sub.loc[cond]

    if hit.empty:
        return None, None
    else:
        row = hit.iloc[0]
        return row['events'], row.name

# -----------------------------
# 4. Debugging loop
# -----------------------------

records = []

print('STEAL / CS DEBUG TRACE')
print('=' * 80)

for idx, row in df.iterrows():
    desc = row['des']
    running_events = parse_running_events(desc)

    if not running_events:
        continue

    print('STEAL ROW FOUND')
    print('index:', idx)
    print('des:', desc)
    print('on_1b:', row['on_1b'], 'on_2b:', row['on_2b'])
    print('parsed events:', running_events)

    for ev_type, base in running_events:
        runner_id = get_runner_id(row, base)

        print(f'  EVENT: {ev_type} {base}')
        print('  runner_id:', runner_id)

        next_event, next_idx = find_next_batter_event(df, idx, runner_id)

        if next_event is None:
            print('  -> NEXT EVENT NOT FOUND')
        else:
            print('  -> NEXT EVENT FOUND')
            print('     next_index:', next_idx)
            print('     next_event:', next_event)

        records.append({
            'runner_id': runner_id,
            'event_type': (
                f'steal_{base}' if ev_type == 'steal'
                else f'caught_steal_{base}'
            ),
            'from_base': 'on_1b' if base == '2b' else 'on_2b',
            'trigger_row': idx,
            'next_event': next_event,
            'next_event_row': next_idx
        })

    print('-' * 80)

print('DEBUG LOOP END')
print('=' * 80)

# 5. Result DataFrame
result_df = pd.DataFrame(records)

print('RESULT DF PREVIEW')
print(result_df.head(20))
print('Total matches:', len(result_df))