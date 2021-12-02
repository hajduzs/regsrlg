import argparse
import os

from src.util.JsonGraphGenerator import JsonGraphGenerator
from src.generation.fromdual import generate_srlgs_from_dual
from src.generation.parsefromlgf import convert_srlgs_from_lgf

#
#   Arguments and parsing
#
parser = argparse.ArgumentParser(description='Generate SLRG list with given parameters for a given planar graph')
parser.add_argument('input_graph', metavar='G', nargs=1 ,type=argparse.FileType('r'),
                    help='The input graph file. Supported formats: {.lgf, .gml, .graphml}')

parser.add_argument('--method', required=True,
                    help='The SLRG generation method. Supported: {fromdual, radius, pslrg}')

parser.add_argument('--param1')   # fromdual: l | radius: r | pslrg: p

parser.add_argument('--param2')

_methods = {
    'fromdual': generate_srlgs_from_dual, 
    'fromlgf': convert_srlgs_from_lgf, 
    'psrlg': NotImplemented
}

args = parser.parse_args()

gname = args.input_graph[0].name

json_graph = JsonGraphGenerator(gname).gen_json(auto_convert=False) # TODO this is a lil' bit hacky, fix

m = args.method
if m not in _methods:
    raise Exception('Not supported SRLG generation method!')

if m == 'fromlgf':
    slrgs = _methods[m](gname) 
else:
    slrgs = _methods[m](json_graph, int(args.param1[0]))

print(slrgs)
exit()

dirpath = f'slrg_fromdual_{int(args.param1)}_{int(args.param2)}'

graph_name = gname.split("/")[-1].split(".")[0]
graph_file = gname.split("/")[-1]
os.mkdir(f'tasks2/{graph_name}/{dirpath}')
with open(f'tasks2/{graph_name}/{dirpath}/{graph_file}.slrg', 'w') as f:
    f.write(str([slrgs]))
