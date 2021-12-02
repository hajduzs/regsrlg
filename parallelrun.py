import argparse, os


import json
from copy import deepcopy
import random
import networkx as nx
from itertools import combinations

from src.SrlgDisjointSolver import SrlgDisjointSolver
from src.util.JsonGraphGenerator import JsonGraphGenerator

from src.generation.parsefromlgf import convert_srlgs_from_lgf

splen = 0
from paralleldefs import solve_and_get_result
import sys
sys.setrecursionlimit(2000)

from multiprocessing import Pool 

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

parser = argparse.ArgumentParser()
parser.add_argument('--path', type=dir_path)
args = parser.parse_args()

def get_all_u_v_from_jsg(jsg):

    g = nx.Graph()
    for n in jsg['nodes']:  # Get every point of the graph with coordinates
        g.add_node(n['id'])

    for e in jsg['edges']:  # Get every edge of the graph with lengths caluclated from the coordinates
        g.add_edge(e['from'], e['to'])

    # now we filter out nodes that are virtually impossible to find >2 paths for 

    nodes_with_degree_1 = [0]

    while nodes_with_degree_1:
        nodes_with_degree_1 = [n for n, d in g.degree() if d == 1]
        g.remove_nodes_from(nodes_with_degree_1)

    pnodes = [n for n in g.nodes()]    

    ret = [(x,y) for x,y in combinations(pnodes,2)]
    random.shuffle(ret)
    return ret #(e for e in ret)



AGGREGATED = []
AGG = {}
ROOTDIR = args.path


STARTPARAMS = []

root, subdirs, files = next(os.walk(ROOTDIR))
# walk every subdir (must be containing graphs)
for GDIR in subdirs:
    
    G_root, G_subdirs, G_files = next(os.walk(f'{ROOTDIR}/{GDIR}'))
    # get graph file
    gfile = [f for f in G_files if f.split('.')[0] == GDIR][0]
    
    jsg = JsonGraphGenerator(f'{ROOTDIR}/{GDIR}/{gfile}').gen_json(auto_convert=False)

    allpossibeluv = get_all_u_v_from_jsg(jsg)

    grap_metric_got = False
    
    for SDIR in G_subdirs:
        S_root, S_subdirs, S_files = next(os.walk(f'{ROOTDIR}/{GDIR}/{SDIR}'))
        s_method = SDIR.split('_')[1]
        sfiles = [f for f in S_files if f.split('.')[-1] == 'srlg' or f.split('.')[-1] == 'slrg']
        lgffiles = [f for f in S_files if f.split('.')[-1] == 'lgf']
        if len(sfiles) != 0:
            sfile = sfiles[0]
            with open(f'{ROOTDIR}/{GDIR}/{SDIR}/{sfile}') as fff:
                jss = json.load(fff)
                if len(jss) == 1:
                    jss = jss[0]
        elif len(lgffiles) != 0:
            sfile = lgffiles[0]
            fff = f'{ROOTDIR}/{GDIR}/{SDIR}/{sfile}'
            jss = convert_srlgs_from_lgf(fff)

        print(f'{ROOTDIR}/{GDIR}/{SDIR}/{sfile}')

        try:

            s = SrlgDisjointSolver(jsg, deepcopy(jss), 0, 1)

            if not grap_metric_got:
                # GRAPH METRIC SAVE
                AGG[GDIR] = s.get_graph_metrics()
                AGG[GDIR]['fromfile'] = gfile
                AGG[GDIR]['srlgs'] = {}
                grap_metric_got = True

            AGG[GDIR]['srlgs'][SDIR] = s.get_srlg_metrics()
            AGG[GDIR]['srlgs'][SDIR]['fromfile'] = sfile
            AGG[GDIR]['srlgs'][SDIR]['gen'] = s_method

            STARTPARAMS.append( (GDIR, deepcopy(allpossibeluv), SDIR, deepcopy(jsg), deepcopy(jss)))
        except Exception as e:
            print(f'something went wrong: {e}')

def collect_result(result):
    global AGG
    GDIR, SDIR, res = result
    AGG[GDIR]['srlgs'][SDIR]['runs'] = res

splen = len(STARTPARAMS)

pool = Pool()
for SP in STARTPARAMS:
    pool.apply_async(solve_and_get_result, args=SP, callback=collect_result)

pool.close()
pool.join()

AGGREGATED = []
for k, v in AGG.items():
    slrgs = []
    for sk, sv, in AGG[k]['srlgs'].items():
        slrgs.append(sv)
    v['srlgs'] = slrgs
    AGGREGATED.append(v)


# really U G L Y aggregated XML generation 
with open(f'{ROOTDIR}/aggregated.xml', 'w') as f:
    f.write('<?xml version="1.0" ?>')
    f.write('<graphs>')
    for GM in AGGREGATED:
        f.write('<graph>')
        for k, v in GM.items():
            if k == 'srlgs':
                f.write('<srlgs>')
                for SM in GM[k]:
                    f.write('<srlg>')
                    for sk, sv in SM.items():
                        if sk == 'runs':
                            f.write('<runs>')
                            for RM in SM[sk]:
                                f.write('<run>')
                                for rk, rv in RM.items():
                                    if isinstance( rv, list):
                                        f.write(f'<{rk}>')
                                        for item in RM[rk]:
                                            f.write(f'<{rk}_item>{item}</{rk}_item>')
                                        f.write(f'</{rk}>')
                                    else:
                                        f.write(f'<{rk}>{rv}</{rk}>')
                                f.write('</run>')
                            f.write('</runs>')
                        elif isinstance( sv, list):
                            f.write(f'<{sk}>')
                            for item in SM[sk]:
                                f.write(f'<{sk}_item>{item}</{sk}_item>')
                            f.write(f'</{sk}>')
                        else:
                            f.write(f'<{sk}>{sv}</{sk}>')    
                    f.write('</srlg>')
                f.write('</srlgs>')
            else:
                f.write(f'<{k}>{v}</{k}>')
        f.write('</graph>')
    f.write('</graphs>')
