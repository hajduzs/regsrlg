from src.SrlgDisjointSolver import SrlgDisjointSolver
from copy import deepcopy


def solve_and_get_result(GDIR, possibleuvs, SDIR, jsg, jss):
    num_runs = 0
    num_succ_runs = 0
    
    results = []

    for u, v in possibleuvs:
        
        if num_succ_runs == 30 or num_runs > 150:
            break       # we are done when we hade 30 good random runs or 150 runs altogether
                        # (or when the list is exhausted)
        num_runs += 1
        try:
            print(f'-- Running: {GDIR} for {SDIR}. S-T: {u}-{v} ({len(possibleuvs)} / {num_runs} [{num_succ_runs}])')
            solver = SrlgDisjointSolver(jsg, deepcopy(jss), u, v)
            solver.solve()
            results.append(solver.get_run_metrics())
            num_succ_runs += 1
            
        except Exception as e:
            pass # do nothing silently
            #print(e)

    return (GDIR, SDIR, results)
