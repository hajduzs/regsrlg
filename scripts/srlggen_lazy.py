import os
import sys 

from src.util.JsonGraphGenerator import JsonGraphGenerator
from src.generation.fromdual import generate_srlgs_from_dual

sys.setrecursionlimit(2000)

def gen(gname, l, n):
    json_graph = JsonGraphGenerator(gname).gen_json(auto_convert=False) # TODO this is a lil' bit hacky, fix

    srlgs = generate_srlgs_from_dual(json_graph, l)

    dirpath = f'srlg_fromdual_{l}_{n}'

    graph_name = gname.split("/")[-1].split(".")[0]
    graph_file = gname.split("/")[-1]
    os.mkdir(f'sv3/{graph_name}/{dirpath}')
    with open(f'sv3/{graph_name}/{dirpath}/{graph_file}.srlg', 'w') as f:
        f.write(str([srlgs]))

graphs = [
    "sv3/16_optic_pan_eu_scaled/16_optic_pan_eu_scaled.lgf",
    "sv3/22_optic_eu_scaled/22_optic_eu_scaled.lgf",
    "sv3/24_us_wide_scaled/24_us_wide_scaled.lgf",
    "sv3/28_optic_eu_scaled/28_optic_eu_scaled.lgf",
    "sv3/39_optic_north_american_scaled/39_optic_north_american_scaled.lgf",
    "sv3/79_optic_nfsnet_scaled/79_optic_nfsnet_scaled.lgf",
    'sv3/USFibre_/USFibre_.gml',
    'sv3/ATT-L1-Modified_/ATT-L1-Modified_.gml',
    'sv3/sprint-phys_/sprint-phys_.gml',
    'sv3/att-phys_/att-phys_.gml'
    ]

for gn in graphs:
    for l in range(2, 5 + 1):
        for n in [1, 2]:
            gen(gn, l, n)