"""Constructed DEMO only. Refuses to overwrite first-pass records."""
import csv
from pathlib import Path

root=Path(__file__).resolve().parent
rows=[]
for policy in ['FIXED_THIRD','DELAYED_TENTH','FIXED_TENTH']:
    volumes={'W':180.0,'E':250.0}
    for minute in range(4):
        alpha=1/3 if policy=='FIXED_THIRD' or (policy=='DELAYED_TENTH' and minute==0) else .1
        inflow={'W':20+30*alpha,'E':10+30*(1-alpha)}
        for tank,capacity,load in [('W',200.0,18.0),('E',300.0,24.0)]:
            gain=inflow[tank]-load
            spill=max(0.0,volumes[tank]+gain-capacity)
            end=min(capacity,volumes[tank]+gain)
            rows.append(dict(provenance='CONSTRUCTED_DEMO',policy=policy,interval_start_min=minute,interval_end_min=minute+1,interval_duration_min=1,tank=tank,alpha_to_west=round(alpha,10),start_l=volumes[tank],capacity_l=capacity,inflow_lpm=inflow[tank],load_lpm=load,net_gain_lpm=gain,raw_net_gain_l=gain,spill_l=spill,end_l=end))
            volumes[tank]=end
    subset=[r for r in rows if r['policy']==policy]
    assert abs(430+240-sum(volumes.values())-168-sum(r['spill_l'] for r in subset))<1e-9
with (root/'interval_results.csv').open('x',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
print('CONSTRUCTED_DEMO: 24 complete interval/tank records; conservation PASS')
