import networkx as nx
import itertools

from src.util.HelperClasses import Edge

def get_graph_metrics_of_solver(solver):
    m = {}

    m['V'] = solver.PG.G.number_of_nodes()
    m['E'] = solver.PG.G.number_of_edges()
    m['maxiter'] = solver.max_iter
    m['iternum'] = solver.iternum
    
    diam = 0
    sp = nx.shortest_path_length(solver.PG.G, weight='length')
    sp = [i for i in sp]
    for _, paths in sp:
        for _, sv in paths.items():
            if sv > diam:
                diam = sv
    m['dg'] = diam

    diam = 0
    sp = nx.shortest_path_length(solver.PG.G)
    sp = [i for i in sp]
    for _, paths in sp:
        for _, sv in paths.items():
            if sv > diam:
                diam = sv
    m['d'] = diam

    m['c'] = nx.node_connectivity(solver.PG.G)
    m['telen'] = sum([d['length'] for _, _, d in solver.PG.G.edges(data=True)])

    return m

def get_srlg_metrics_of_solver(solver):
    m = {}
        
    m['gen'] = 'unknown'
    m['ns'] = len(solver._jss_orig)
    m['sec'] = [len(srlg) for srlg in solver._jss_orig]

    diameters = []
    for srlg in solver._jss_orig:
        points = set()

        for x, y in srlg: 
            for u, v, d in solver.DG.G.edges(data=True):
                ou = d['of']
                ov = d['ot']
                if Edge(x,y) == Edge(ou, ov):
                    points.update({u, v})

        diam = 0
        
        for x,y in itertools.combinations(points, 2):
            l = len(nx.shortest_path(solver.DG.G, x, y))
            if l > diam:
                diam = l

        diameters.append(diam)
    m['sdn'] = diameters

    return m 

def get_run_metrics_from_solver(solver):
    m = {}

    m['s'] = solver.s
    m['t'] = solver.t 

    m['stc'] = nx.node_connectivity(solver.PG.G, s=solver.s, t=solver.t)
    m['k'] = solver.k

    m['ti_c'] = solver.time_core
    m['ti_hn'] = solver.time_heur_node
    m['ti_hd'] = solver.time_heur_dist

    m['iternum'] = solver.iternum

    bhpathl_node = [len(p) for p in solver.maxpaths_bh]
    bhpathl_dist = [solver.PG.cost_of_path(p) for p in solver.maxpaths_bh]

    ah_node_pathl_node = [len(p) for p in solver.maxpaths_ah_node]
    ah_node_pathl_dist = [solver.PG.cost_of_path(p) for p in solver.maxpaths_ah_node]
    ah_geom_pathl_node = [len(p) for p in solver.maxpaths_ah_geom]
    ah_geom_pathl_dist = [solver.PG.cost_of_path(p) for p in solver.maxpaths_ah_geom]

    m['pl_bh_avg_no'] = sum(bhpathl_node) / len(bhpathl_node)
    m['pl_bh_avg_di'] = sum(bhpathl_dist) / len(bhpathl_dist)

    m['pl_ahn_avg_n'] = sum(ah_node_pathl_node) / len(ah_node_pathl_node)
    m['pl_ahn_min_n'] = min(ah_node_pathl_node)
    m['pl_ahn_max_n'] = max(ah_node_pathl_node)

    m['pl_ahn_avg_d'] = sum(ah_node_pathl_dist) / len(ah_node_pathl_dist)
    m['pl_ahn_min_d'] = min(ah_node_pathl_dist)
    m['pl_ahn_max_d'] = max(ah_node_pathl_dist)

    m['pl_ahd_avg_n'] = sum(ah_geom_pathl_node) / len(ah_geom_pathl_node)
    m['pl_ahd_min_n'] = min(ah_geom_pathl_node)
    m['pl_ahd_max_n'] = max(ah_geom_pathl_node)

    m['pl_ahd_avg_d'] = sum(ah_geom_pathl_dist) / len(ah_geom_pathl_dist)
    m['pl_ahd_min_d'] = min(ah_geom_pathl_dist)
    m['pl_ahd_max_d'] = max(ah_geom_pathl_dist)


    
    #m['shortest_path'] = solver.firstpath
    fp_node = nx.shortest_path(solver.PG.G, solver.PG.s, solver.PG.t)
    m['spln'] = len(fp_node)
    m['spld'] = solver.PG.cost_of_path(solver.firstpath)
    

    # How many srlg-s found paths intersect:
    srlg_int_lens = []
    for p in solver.pathqueue:
        path_srlgs = set()
        for i in range(len(p) - 1):
            u = p[i]
            v = p[i+1]
            edge_srlgs = frozenset(solver._get_srlgs_containing_edge(u,v,True))
            path_srlgs.update(edge_srlgs)
        srlg_int_lens.append(len(path_srlgs))
    m['si'] = srlg_int_lens

    # Cost of two cheapest SLRG-disjoint paths:

    if solver.k < 2:
        m['tssd'] = -1   # results for k=2 do not exist, so we just write -1 instead
        m['tssn'] = -1
    else:
        m['tssd'] = sum([solver.PG.cost_of_path(p) for p in solver.shortening_heurisctic(paths=solver.results[2], geom=False)])
        m['tssn'] = sum([len(p) for p in solver.shortening_heurisctic(paths=solver.results[2], geom=False)])
       

    # Cost of two cheapest node-dijsoint paths: (not including SLRG-s, which might worsen this result)
    G = solver.PG.G.copy()
    nx.set_edge_attributes(G, 1, "capacity")
    nx.set_node_attributes(G, {solver.s:-2, solver.t:2}, "demand")

    scale = 10**6
    
    lengths = [(u, v, G[u][v]['length'] * scale) for u, v in G.edges()]

    for u, v, nw in lengths:
        G[u][v]['length'] = int(nw)
    
    flow = nx.min_cost_flow(nx.to_directed(G), weight='length')


    # build back paths from flows: 

    flow_based_paths = []
    for n, f_out in flow[solver.s].items():
        if f_out == 0:
            continue

        path = [solver.s]
        nextnode = n
        while nextnode != solver.t:
            path.append(nextnode)
            nextnode = [k for k, v in flow[nextnode].items() if v == 1][0]
        path.append(solver.t)

        flow_based_paths.append(path)

    m['tsfd'] = sum([solver.PG.cost_of_path(p) for p in flow_based_paths])


    flow = nx.min_cost_flow(nx.to_directed(G))


    # build back paths from flows: 

    flow_based_paths = []
    for n, f_out in flow[solver.s].items():
        if f_out == 0:
            continue

        path = [solver.s]
        nextnode = n
        while nextnode != solver.t:
            path.append(nextnode)
            nextnode = [k for k, v in flow[nextnode].items() if v == 1][0]
        path.append(solver.t)

        flow_based_paths.append(path)

    m['tsfn'] = sum([len(p) for p in flow_based_paths])

    # min cut info 

    m['mincut_diff'] = solver.mincut_diff

    return m