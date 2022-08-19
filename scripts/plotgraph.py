import sys
sys.path.append("../regsrlg")
from src.util.JsonGraphGenerator import JsonGraphGenerator
from src.DualGraph import DualGraph
from src.PlanarGraph import PlanarGraph
import networkx as nx 
from matplotlib import pyplot as plt

jsg = JsonGraphGenerator(
    f'/home/zsomb/work/regsrlg/archive/v4_2/att-phys_/att-phys_.gml'
).gen_json(auto_convert=False)

print("xd")

G = nx.Graph()

for n in jsg["nodes"]:
    G.add_node(n["id"], pos = n["coords"])

for e in jsg["edges"]: 
    G.add_edge(e["from"], e["to"])
pos=nx.get_node_attributes(G,'pos')

nx.draw(G, with_labels=True, pos=pos)

# now for the dual 

DG = DualGraph(PlanarGraph(jsg, [], 0, 1)).jsdata

D = nx.Graph()

for n in DG["nodes"]:
    D.add_node(n["id"], pos2 = [n["coords"].x, n["coords"].y])

pos2=nx.get_node_attributes(D,'pos2')

nx.draw(D, with_labels=True, pos=pos2, node_color="green")


plt.show()