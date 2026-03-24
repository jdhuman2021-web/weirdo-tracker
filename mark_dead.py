import json

with open('config/tokens.json', 'r') as f:
    data = json.load(f)

for t in data['tokens']:
    if t['symbol'] in ['Devious', 'Lockdown']:
        t['status'] = 'dead'
        print(f"Marked {t['symbol']} ({t['name']}) as dead")

with open('config/tokens.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Saved!")
