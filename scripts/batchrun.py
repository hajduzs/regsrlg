import os
import json
from copy import deepcopy
import random

from json2xml import json2xml
from json2xml.utils import readfromstring

import xml.etree.ElementTree as ET

from src.SrlgDisjointSolver import SrlgDisjointSolver
from src.util.JsonGraphGenerator import JsonGraphGenerator

from src.generation.parsefromlgf import convert_srlgs_from_lgf


import sys
sys.setrecursionlimit(2000)


def get_all_u_v_from_jsg(jsg):
    ret = []
    for i in range(len(jsg['nodes'])):
        for j in range(i + 1, len(jsg['nodes'])):
            u = jsg['nodes'][i]['id']
            v = jsg['nodes'][j]['id']
            if u != v:
                ret.append((u,v))
    return ret 


AGGREGATED = []

ROOTDIR = './v4_1'

root, subdirs, files = next(os.walk(ROOTDIR))
# walk every subdir (must be containing graphs)
for GDIR in subdirs:
    
    G_root, G_subdirs, G_files = next(os.walk(f'{ROOTDIR}/{GDIR}'))
    # get graph file
    gfile = [f for f in G_files if f.split('.')[0] == GDIR][0]
    
    jsg = JsonGraphGenerator(f'{ROOTDIR}/{GDIR}/{gfile}').gen_json(auto_convert=False)

    GRAPH_METRICS = {}

    allpossibeluv = get_all_u_v_from_jsg(jsg)
    random.shuffle(allpossibeluv)
    
    for SDIR in G_subdirs:
        S_root, S_subdirs, S_files = next(os.walk(f'{ROOTDIR}/{GDIR}/{SDIR}'))

        s_method = SDIR.split('_')[1]

        # IF SRLG file is in .srlg format

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
        else:
            print('I hate life')
        # IF SRLG file is in .lgf format

        SRLG_METRICS = {}

        num_runs = 0
        num_succ_runs = 0
        
        for u, v in allpossibeluv:
            
            if num_succ_runs == 100 or (num_succ_runs == 0 and num_runs > 100):
                break       # we are done when we hade 100 good random runs 
                            # (or when the list is exhausted)
  
            num_runs += 1

            #if True:
            try:
                print(f'Running: {GDIR} for srlg {SDIR}. S-T: {u}-{v} ({len(allpossibeluv)} / {num_runs} [{num_succ_runs}])')
                succ_run = True
                solver = SrlgDisjointSolver(jsg, deepcopy(jss), u, v)
                solver.solve()
                num_succ_runs += 1

            except Exception as e:
                print(e)
                succ_run = False
            
            if succ_run:
                
                if not GRAPH_METRICS:
                    GRAPH_METRICS = solver.get_graph_metrics()
                    GRAPH_METRICS['fromfile'] = gfile
                    GRAPH_METRICS['srlgs'] = []
                    with open(f'{ROOTDIR}/{GDIR}/graph_metrics.xml', 'w') as f:
                        f.write(
                            json2xml.Json2xml(
                                readfromstring(str(json.dumps(GRAPH_METRICS))), 
                                wrapper="all", 
                                pretty=True, 
                                attr_type=False
                            ).to_xml()
                        )

                if not SRLG_METRICS:
                    SRLG_METRICS = solver.get_srlg_metrics()
                    SRLG_METRICS['fromfile'] = sfile
                    SRLG_METRICS['gen'] = s_method
                    SRLG_METRICS['runs'] = []
                    with open(f'{ROOTDIR}/{GDIR}/{SDIR}/srlg_metrics.xml', 'w') as f:
                        f.write(
                            json2xml.Json2xml(
                                readfromstring(str(json.dumps(SRLG_METRICS))), 
                                wrapper="all", 
                                pretty=True, 
                                attr_type=False
                            ).to_xml()
                        )    
                with open(f'{ROOTDIR}/{GDIR}/{SDIR}/{u}_{v}_metrics.xml', 'w') as f:
                    RUN_METRICS = solver.get_run_metrics()
                    f.write(
                        json2xml.Json2xml(
                            readfromstring(str(json.dumps(RUN_METRICS))), 
                            wrapper="all", 
                            pretty=True, 
                            attr_type=False
                        ).to_xml()
                    )
                    SRLG_METRICS['runs'].append(RUN_METRICS)
                with open(f'{ROOTDIR}/{GDIR}/{SDIR}/{u}_{v}_data.json', 'w') as f:
                    f.write(
                        json.dumps(solver.get_data())
                    )   

        if num_succ_runs != 0:    
            GRAPH_METRICS['srlgs'].append(SRLG_METRICS)
        
    AGGREGATED.append(GRAPH_METRICS)        

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
    
    #f.write(
        #json2xml.Json2xml(
        #    readfromstring(str(json.dumps(AGGREGATED))), 
        #    wrapper="all", 
        #    pretty=True, 
        #    attr_type=False
        #).to_xml()
    #)
