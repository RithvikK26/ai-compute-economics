"""Diagnostic-only instrumentation; does not change model files or fixtures."""
import argparse,csv,json,platform,sys,io,contextlib,math
from pathlib import Path
import numpy as np
import pandas as pd
import duckdb
from compute_economics import economics as e, workload as w, scenarios as s, reporting as r, catalog as c

ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--reference');a.add_argument('--primitives-only',action='store_true');args=a.parse_args()
out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
original_discount=e.discount_factors;original_demand=w.build_demand
trace={'discount':{},'demand':{}};reference=json.loads(Path(args.reference).read_text()) if args.reference else None
mode='native'
def discount(rate,periods):
 key=f'{rate!r}/{periods}'
 native=original_discount(rate,periods)
 trace['discount'][key]={'rate':rate,'periods':periods,'base':1+rate,'exponents':(-np.arange(periods+1)/12).tolist(),'values':native.tolist(),'scalar_pow':[float(1+rate)**float(x) for x in -np.arange(periods+1)/12], 'numpy_scalar_pow':[float(np.power(np.float64(1+rate),np.float64(x))) for x in -np.arange(periods+1)/12]}
 if mode in ('discount','both'):return np.array(reference['discount'][key]['values'])
 return native

def demand(run):
 native=original_demand(run)
 key=r.digest(run.model_dump(mode='json'))
 pre=3600*run.demand_scale_tokens_s*np.tile(run.demand_base_nodes,run.horizon_months)*native.hours
 growth=(1+run.demand_growth_fraction)**(native.period-1)
 trace['demand'][key]={'name':run.scenario_name if hasattr(run,'scenario_name') else '', 'base':1+run.demand_growth_fraction,'exponents':(native.period-1).tolist(),'hours':native.hours.tolist(),'pre_growth':pre.tolist(),'growth':growth.tolist(),'tokens':native.tokens.tolist(),'scalar_pow':[float(1+run.demand_growth_fraction)**int(x) for x in native.period-1]}
 if mode in ('demand','both'):return w.DemandTable(native.period,native.block,native.hours,np.array(reference['demand'][key]['tokens']),native.month_hours,native.month_labels)
 return native

e.discount_factors=discount
w.build_demand=s.build_demand=r.build_demand=demand
meta={'platform':platform.platform(),'machine':platform.machine(),'python':sys.version,'numpy':np.__version__,'duckdb':duckdb.__version__}
f=io.StringIO()
with contextlib.redirect_stdout(f): np.show_runtime();np.show_config()
meta['numpy_runtime']=f.getvalue();(out/'environment.json').write_text(json.dumps(meta,indent=2))
if args.primitives_only:
 for preset in ('stable_demand','demand_disappointment','delayed_capacity'):
  run,_=r.load_run(ROOT/'scenarios'/f'{preset}.json',ROOT/'data');demand(run)
  for rate in (0.05,0.10,0.15):discount(rate,run.horizon_months)
 (out/'trace.json').write_text(json.dumps(trace,indent=2));raise SystemExit(0)
for mode in (('native','discount','demand','both') if reference else ('native',)):
 for preset in ('stable_demand','demand_disappointment','delayed_capacity'):
  run,_=r.load_run(ROOT/'scenarios'/f'{preset}.json',ROOT/'data')
  r.export_run(run,out/mode/preset)
  print(mode,preset,flush=True)
(out/'trace.json').write_text(json.dumps(trace,indent=2))
# Identical fixture inputs on both platforms: no regenerating/reordering the upstream ledger.
rows=list(csv.DictReader((ROOT/'examples/cost_ledger.csv').open()))
for row in rows:
 row['period']=int(row['period'])
 for k in ('cash_usd','pv_usd'):row[k]=float(row[k])
frame=pd.DataFrame(rows);query=(c.SQL/'annual_costs.sql').read_text()
for threads in (1,4):
 for iteration in range(5):
  with duckdb.connect(config={'threads':threads}) as con:
   con.register('ledger',frame);cur=con.execute(query);annual=[dict(zip([x[0] for x in cur.description],v)) for v in cur.fetchall()]
  r.write_csv(out/f'fixed-input-annual-t{threads}-{iteration}.csv',annual)
print('DONE',flush=True)
