from typing import List
from src.PlanarGraph import PlanarGraph
from src.DualGraph import DualGraph

import random

def generate_srlgs_from_dual(jsg, l:int, n:int = 0) -> List[List[int]]:

    # Construct graph and dual
    PG = PlanarGraph(jsg, [], random.choice(jsg['nodes'])['id'], random.choice(jsg['nodes'])['id'])
    DG = DualGraph(PG)

    if n == 0:
        n = DG.G.number_of_edges() // l

    slrgs = []
    for i in range(n):

        # get random node (region) to start the walk form 

        path_found = False
        while not path_found:
            s = random.choice(list(DG.G.nodes))
            visited = set([s])
            slrg = []

            while len(slrg) != l:
                t = s 
                tries = 0
                while t in visited and tries < 50:
                    neig = list(DG.G.neighbors(s))
                    if neig:
                        t = random.choice(neig)
                    tries += 1
                if tries == 50:
                    break
                
                r = random.randint(0, len(DG.G[s][t]) -1)
                of = DG.G[s][t][r]['of']
                ot = DG.G[s][t][r]['ot']
                slrg.append([of, ot])
                visited.add(t)
                s = t

            if len(slrg) == l:
                slrgs.append(slrg)
                path_found = True
            else: 
                path_found = False

    return slrgs
    