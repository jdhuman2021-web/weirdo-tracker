import json
from pathlib import Path

config_file = Path('config/tokens.json')
with open(config_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Add BONER as dead
boner = {
    'symbol': 'BONER',
    'name': 'The Hardest Dog',
    'address': 'FYmauk5k5hst1TDiNKRQFJmNyLUsS3qYTdifYmKkpump',
    'chain': 'SOL',
    'added_date': '2026-03-20',
    'source': 'user_added',
    'status': 'dead',
    'notes': 'Marked as dead - user request'
}

data['tokens'].append(boner)
data['last_updated'] = '2026-03-20T22:50:00'

with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Added BONER with status: dead')
print('Total tokens:', len(data['tokens']))