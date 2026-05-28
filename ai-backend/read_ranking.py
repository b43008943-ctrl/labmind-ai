import json
d = json.load(open('ranking_audit_results.json'))
for x in d:
    print('=' * 60)
    print(x['label'], ' sickle=', x['sickle_count'], ' missed=', x['missed_count'])
    print('  Median sickle morph:', x['median_sickle_morph'])
    print('  TOP 3 SICKLE (red boxes):')
    for c in x['top5_sickle'][:3]:
        print(f'    cnn={c["cnn_sick"]:.3f} morph={c["morph_score"]:.3f} comp={c["composite"]:.3f}  l_ar={c["l_ar"]:.2f} l_circ={c["l_circ"]:.2f} l_sol={c["l_sol"]:.2f}  h_ar={c["h_ar"]:.2f} h_circ={c["h_circ"]:.2f} h_sol={c["h_sol"]:.2f}')
    print('  BOTTOM 3 SICKLE (weakest red):')
    for c in x['bottom5_sickle'][-3:]:
        print(f'    cnn={c["cnn_sick"]:.3f} morph={c["morph_score"]:.3f} comp={c["composite"]:.3f}  l_ar={c["l_ar"]:.2f} l_circ={c["l_circ"]:.2f} l_sol={c["l_sol"]:.2f}  h_ar={c["h_ar"]:.2f} h_circ={c["h_circ"]:.2f} h_sol={c["h_sol"]:.2f}')
    print('  TOP 3 MISSED (green but high morph):')
    for c in x['top5_missed'][:3]:
        print(f'    cnn={c["cnn_sick"]:.3f} morph={c["morph_score"]:.3f} comp={c["composite"]:.3f}  l_ar={c["l_ar"]:.2f} l_circ={c["l_circ"]:.2f} l_sol={c["l_sol"]:.2f}  h_ar={c["h_ar"]:.2f} h_circ={c["h_circ"]:.2f} h_sol={c["h_sol"]:.2f}')
