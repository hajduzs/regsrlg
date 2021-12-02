from typing import FrozenSet, List, Union
import networkx as nx
from src.geometry.Point import Point
from src.geometry.operations_2d import point_to_point
from src.util.HelperClasses import *
from src.util.HelperFunctions import *


import logging
log = logging.getLogger(__name__)                



class PlanarGraph:


    def __init__(self, jsg, jss, s, t) -> None:

        self.s = s                                 # source node
        self.t = t                                 # end node
        self.G: nx.Graph = self._init_graph(jsg)        # Graph
        self.S = self._init_srlg_list(jsg, jss)         # SRLGs in a dictionary


    def _init_graph(self, jsg):
        """Initialitzes nx.Graph form the data given in the json graph.

        Args:
            jsg (object): The data of  the planar graph given in .json format. 
        """        
        g = nx.Graph()
        for n in jsg['nodes']:  # Get every point of the graph with coordinates
            g.add_node(n['id'], coords = Point(*n['coords']))

        for e in jsg['edges']:  # Get every edge of the graph with lengths caluclated from the coordinates
            g.add_edge(e['from'], e['to'], length = point_to_point(g.nodes[e['from']]['coords'], g.nodes[e['to']]['coords']))
        
        for n in g.nodes():     # Add a circualtor to every node, which will help iterating over its neighbours. 
            g.nodes[n]['circulator'] = Circulator(g.nodes[n]['coords'],[(ne, g.nodes[ne]['coords']) for ne in g.neighbors(n)])

        return g


    def _init_srlg_list(self, jsg, jss):
        """Initializes self.S, which is a dictionary of {Edge:set[Edge]}, where the key is an edge of the graph, 
        and the value is a set of all other edges that share a common SLRG with the key edge. 

        Args:
            jsg (object): The data of  the planar graph given in .json format. 
            jss (object): A list of lists containing srlgs.
        """        
        d = { Edge(e['from'], e['to']) : set() for e in jsg['edges'] }
        d[Edge(self.s, self.s)] = set()     # additional dummy key to help with clean code in the dfs.
        for srlg in jss:
            for e in srlg:
                for f in srlg: 
                    #if e != f:
                    d[Edge(e[0], e[1])].add(Edge(f[0], f[1]))
        return d

    def edges_on_path(self, p: List[int]) -> Set[Tuple[int, int]]:
        """For a given path, return all the edges connected to the inner nodes (excluding s/t) on the path

        Args:
            p (List[int]): Th epath in question

        Returns:
            Set[int, int]: The edges in question. 
        """
        p = p[1:-1] # we dont need s-t (will interfere if we get neighs for these as well)

        edges = set()
        for node in p: 
            n = self.G.neighbors(node)
            edges.update((Edge(node, ne) for ne in n))
        
        return edges


    def cost_of_path(self, p: List[int]) -> int:
        """Returns the cost of a given path in the graph

        Args:
            p (List[int]): The path

        Returns:
            int: The legth of the path
        """        
        return sum([self.G[p[i]][p[i + 1]]['length'] for i in range(len(p) - 1)])


    def point_disjoint(self, p1: List[int], p2: List[int]) -> bool:
        """Checks if two paths in a planar graph are point-disjoint, not counting source and end nodes.

        Args:
            p1 (List[int]): Path 1 
            p2 (List[int]): Path 2

        Returns:
            bool: True if the two paths are point-disjoint
        """    
        return not set(p1[1:-1]).intersection(set(p2[1:-1]))


    def srlg_disjoint(self, p1: List[int], p2: List[int], srlgs_set) -> bool:
        """Checks if two paths in a planar graph with a given SLRG-list are SLRG-disjoint 

        Args:
            p1 (List[int]): Path 1 
            p2 (List[int]): Path 2

        Returns:
            bool: True if the two paths are SLRG-disjoint
        """       
        if (not p1) or (not p2): # if eiter paths are empty, they are of course disjoint.
            return True

        if srlgs_set is not None:
            SS = self.S
        else:
            SS = srlgs_set
        p1_srlg_edges = set().union(*[self.S[edge] for edge in path_to_edgeset(p1)])   # All the edges that are in a common SLRG with at least on edge in p1
        p2_edges = path_to_edgeset(p2)  # Edges on p2 
        return not p2_edges.intersection(p1_srlg_edges) # If there are no edges on p2 which are in the srlg-set of p1, then the two paths are disjoint.

    def _edges_left_of_path(self, p: List[int]) -> Set[Edge]:
        """Calcualtes edges branching on th left side of a directed path.

        Args:
            p (List[int]): The path as a list of nodes

        Returns:
            Set[Edge]: The edges leaving the path on the left side. 
        """        
        edges = set() 
        # f -> u -> t
        for f, u, t in [(p[i], p[i+1], p[i+2]) for i in range(len(p) - 2)]:
            # u -> v 
            for v in self.G.nodes[u]['circulator'].clockwise_iterator(f):
                if v == t:
                    break
                edges.add(Edge(u,v))
            pass
        return edges


    def right_region(self, u: int, v: int, directed=False) -> Union[Set[Edge] , Set[DirectedEdge]]:
        """Return the region on the right of u->v directed edge int the planar graph.

        Args:
            u (int): Edge source node
            v (int): Edge targe node
            directed (bool): Wheter or not the function should return the region just a set of edges, or a set of directed edges.

        Returns:
            Set[Edge]: The region as a set of edges
        """         

        EdgeType = DirectedEdge if directed else Edge

        def backpropagate_region(current:EdgeType, target:EdgeType) -> FrozenSet[EdgeType]:
            """Starting witha directed edge a->b, find the smallest circle going back to the target. 
            target must be on the edge of the region, and if traget == a, the functiom returns the region as a whole.

            Args:
                a (int): Source node of starting edge
                b (int): Target node of starting edge
                target (int): The target to be reached walking on the edges of the region.

            Returns:
                List[int]: The backpropagated path.
            """            
            if current == target:
                return [current]
            else:
                a, b = current.unpack() 
                nextnode = self.G.nodes[b]['circulator'].clockwise_iterator(a)[0]
                return backpropagate_region(EdgeType(b, nextnode), target) + [current]

        firstedge = EdgeType(u, self.G.nodes[u]['circulator'].clockwise_iterator(v)[0])
        r = backpropagate_region(firstedge, EdgeType(v,u))
        log.debug(f'Right region of {u}->{v} directed edge: {r}')

        return frozenset(r)    

    def caluclate_next_cw_path(self, path: List[int], srlgs_set, newk:bool) -> List[int]:
        """Calculates the closest possible path in clockwise-orientation to the given path,
        taking srlg and point disjointness into account.

        Args:
            path (List[int]): The path as a list of nodes.

        Returns:
            List[int]: The closest possible path in clockwise-orientation found to the given path.
        """ 

        if srlgs_set is not None:
            SS = self.S
        else:
            SS = srlgs_set

        # We define a recursive funtion in this scope, because the outer function 
        # just provides a simpler way to call the function from outside the class.
        def dfs(n: int, pn: int, visited: Set[int], pathnodes: Set[int], pathedges: Set[Edge], forbidden_edges: Set[Edge]) -> List[int]:
            """Custom DFS implementation with respect to srlg-disjointness and point-disjoitness to a given path

            Args:
                n (int): Examined node
                pn (int): Previous node
                visited (Set[int]): Nodes already visited by the given DFS run.
                pathnodes (Set[int]): The path as a set of nodes (must NOT contain first node)
                pathedges (Set[Edge]): The path as set of edge
                forbidden_edges (Set[Edge]): The edges on the 'left' side of the path. 

            Returns:
                List[int]: The closest possible path in clockwise-orientation found to the given path.
            """            
            if n in visited:
                return []           # Return and empty list if we have already seen this node

            if n != self.s and n in pathnodes:
                return []           # Return an empty list if the node is not the source and already used by the given path

            if Edge(pn, n) in forbidden_edges:
                return []           # Return an empty list if edge traversed is 'forbidden' - meaning its on the left side of given path 

            if n != self.s and SS[Edge(pn, n)].intersection(pathedges):
                return []           # Return an empty list if the node is not the source and the examined
                                    # edge is in a common SLRG with any of the edges used on the path
 
            if n == self.t:
                return [n]          # Return the node when we arrive at the target node

            visited.add(n)          # Add node to nodes already visited during a DFS run
            
            for ne in self.G.nodes[n]['circulator'].clockwise_iterator(pn):     # Continue on the next cw oriented edge
                subdfs = dfs(ne, n, visited, pathnodes, pathedges, forbidden_edges) 
                if subdfs != []:
                    return [n] + subdfs     # Roll back on the found s->t path 
            return [] # If we run out of neighbours, go back by returning an empty list

        # Calling previously defined function.
        # call with pn = first node of the path, to ensure right cw precedence.
        if newk:
            res = dfs(self.s, path[1], set(), set(path[:-1]), path_to_edgeset(path), {})    
        else:
            res = dfs(self.s, path[1], set(), set(path[:-1]), path_to_edgeset(path), self._edges_left_of_path(path))    
        log.debug(f'Resulting closest path to {path}: {res}')
        return res
