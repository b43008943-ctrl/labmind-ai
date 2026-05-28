import json
d = json.load(open('recall_results.json'))
for x in d:
    l = x['label'][:20].ljust(20)
    print(f"{l} fin={x['final']:4d} sick={x['sickle']:3d} rbc={x['rbc']:3d} none={x['classify_none']}")
