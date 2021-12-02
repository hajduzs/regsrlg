# The main entry point for the script
import json
import logging
import argparse

import sys
sys.setrecursionlimit(2000)

from src.SrlgDisjointSolver import SrlgDisjointSolver
from src.util.JsonGraphGenerator import JsonGraphGenerator

#
#   Arguments and parsing
#
parser = argparse.ArgumentParser(description='Calculate the maximum number of SLRG-disjoint paths for a given planar graph and SLRG-list.')
parser.add_argument('input_graph', metavar='G', nargs=1 ,type=argparse.FileType('r'),
                    help='The input graph file. Supported formats: {.lgf, .gml, .graphml}')
parser.add_argument('input_slrg_list', metavar='S', nargs=1 ,type=argparse.FileType('r'),
                    help='The input slrg list file. Check the repository for the correct format.')

parser.add_argument('source', metavar='s', nargs=1 ,type=str,
                    help='Source node.')
parser.add_argument('target', metavar='t', nargs=1 ,type=str,
                    help='Target node.')

parser.add_argument('-v', '--verbose', help='Show additional output of the algorithm run.', action='store_true')
parser.add_argument('-d', '--debug', help='Show debugging messages on the command line.', action='store_true')
parser.add_argument('-u', '--gui', help='Start the program with a nice GUI to follow the steps easily.', action='store_true')
args = parser.parse_args()

#
#   Logging
#
log = logging.getLogger(__name__)
if args.debug:
    logging.basicConfig(level='DEBUG')
    log.debug('Logging level set to DEBUG')
elif args.verbose:
    logging.basicConfig(level='INFO')
else:
    logging.basicConfig(level='WARNING')

#
#   Start 
#

# Read input files given in args ant convert them to JSON 
json_graph = JsonGraphGenerator(args.input_graph[0].name).gen_json(auto_convert=False) # TODO this is a lil' bit hacky, fix
json_list  = json.load(args.input_slrg_list[0])
if len(json_list) == 1:
    json_list = json_list[0]
s = args.source[0]
t = args.target[0]

solver = SrlgDisjointSolver(json_graph, json_list, int(s), int(t))

if args.gui:
    from src.SolverGUI import SolverGUI     # ugly import in the middle of the file TODO
    gui = SolverGUI(solver)
    gui.mainloop()
else:
    solver.solve() 