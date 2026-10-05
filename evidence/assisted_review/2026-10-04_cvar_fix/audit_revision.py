"""Assisted old/new reporting audit; never overwrite the historical snapshots."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from storage_decision import battery,experiment
CASES=(("base.yaml","baseline","experiments/legacy_threshold_tail/baseline"),("cvar_weight_070.yaml","cvar_weight_070","evidence/personal_run/2026-10-02/cvar_weight_070_outputs/tables"),("high_risk_aversion.yaml","cvar_weight_085","experiments/legacy_threshold_tail/cvar_weight_085"))
def legacy_estimator(profits,alpha=0.9):
    losses=-np.asarray(profits,dtype=float)
    return float(losses[losses>=np.quantile(losses,alpha)].mean())
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-root',type=Path,required=True);args=parser.parse_args()
    target=args.output_root.resolve();target.mkdir(parents=True,exist_ok=True)
    solve=battery.optimise_schedule;fixed_estimator=battery.empirical_cvar_loss;reports=[]
    for config,name,historical in CASES:
        stats={'solves_compared':0,'max_schedule_difference':0.,'max_expected_profit_difference':0.,'max_objective_difference':0.}
        def audited(*positional,**keywords):
            fixed=solve(*positional,**keywords)
            battery.empirical_cvar_loss=legacy_estimator
            try:old=solve(*positional,**keywords)
            finally:battery.empirical_cvar_loss=fixed_estimator
            diff=float(np.abs(fixed.schedule.to_numpy()-old.schedule.to_numpy()).max())
            stats['solves_compared']+=1
            stats['max_schedule_difference']=max(stats['max_schedule_difference'],diff)
            stats['max_expected_profit_difference']=max(stats['max_expected_profit_difference'],abs(fixed.expected_profit-old.expected_profit))
            stats['max_objective_difference']=max(stats['max_objective_difference'],abs(fixed.objective_value-old.objective_value))
            assert diff<=1e-10 and abs(fixed.objective_value-old.objective_value)<=1e-10
            return fixed
        experiment.optimise_schedule=audited
        try:result=experiment.run(ROOT/'configs'/config,ROOT,target/name)
        finally:experiment.optimise_schedule=solve
        differences={}
        for table,cvar in [('strategy_metrics.csv','empirical_cvar_loss_eur'),('daily_results.csv','in_sample_cvar_loss_eur'),('risk_frontier.csv','empirical_cvar_loss_eur')]:
            new=pd.read_csv(target/name/'tables'/table);old=pd.read_csv(ROOT/historical/table)
            assert new.shape==old.shape and list(new.columns)==list(old.columns)
            maximum=0.
            for col in new.columns:
                if col==cvar:continue
                if pd.api.types.is_numeric_dtype(new[col]):
                    delta=float(np.abs(new[col].to_numpy()-old[col].to_numpy()).max());maximum=max(maximum,delta);assert delta<=1e-10,(name,table,col,delta)
                else:assert new[col].equals(old[col]),(name,table,col)
            differences[table]=maximum
        reports.append({'configuration':config,'snapshot':name,**stats,'max_non_cvar_difference_from_historical_tables':differences,'adaptive_cvar':result['summary'].set_index('strategy').loc['adaptive_cvar'].to_dict()})
        print(name,json.dumps(stats),flush=True)
        print(result['summary'].to_string(index=False),flush=True)
    (target/'audit_results.json').write_text(json.dumps({'assisted_review':True,'date':'2026-10-04','cvar_estimator':'empirical_fixed_probability_mass_v1','comparisons':reports},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
