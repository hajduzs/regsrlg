import math
from typing import FrozenSet
from networkx.convert import to_dict_of_dicts
from src.DualGraph import DualGraph
from src.PlanarGraph import PlanarGraph
from src.util.HelperClasses import *
from src.util.HelperFunctions import *
from src.util.Metrics import *
import networkx as nx
from copy import deepcopy
import time
import logging

log = logging.getLogger(__name__)                

class SrlgDisjointSolver:

    def __init__(self, graph, list, s, t):

        # Starter data 
        self.jsg = graph                                # original json data of the graph
        self.jss = list                                 # original SLRG data
        self.s = s                                      # source node
        self.t = t                                      # end node

        # INITIALIZATION of SLRG list, and Graphs.
        self.jss = self._remove_cutting_slrgs()         # To get better results, we exclude SRLGs from the input list that would cut all s-t paths.
        self._jss_orig = deepcopy(self.jss)             # Save original SRLG list
        #self._refresh_jss_with_point_failures()         # Add point-failure srlgs to SRLG-list so point disjointness of paths is guaranteed this way
        self.PG = PlanarGraph(graph, self.jss, s, t)    # The planar Graph instance used for finding paths 
        self.DG = DualGraph(self.PG)                    # Dual of the planar graph
        self.max_iter = self._calc_max_iter()           # maximum number of iterations (stopping point 1)

        # Working variables                             - note: path lists contain lists of node ids.
        self.iternum = 0                                # how many times we have tried in the current iteration
        self.finished = False                           # Boolean indicating if we have come to the end (max k) or not.
        self.k = 0                                      # Current Maximum number of srlg-disjoint paths found
        self.pathqueue = []                             # Current queue of paths during an iteration for a specific k.
        self.fallbackqueue = []                         # Fallback queue for heuristically speeding up stop
        self.oldestpath = []                            # Current oldest path   -   pathqueue[0]
        self.newestpath = []                            # Current latest path   -   pathqueue[-1]
        self.novelpath = []                             # Current novel path caluclated by the specialised DFS

        # Results
        self.results = {}                               # Dictionary containing the result paths for all k. - key: k, value: list of paths 
        self.maxpaths_bh = []                           # Paths found for k=max before shortening heuristic
        self.maxpaths_ah_node = []                      # Paths found for k=max after shortening heuristic, minimising number of nodes
        self.maxpaths_ah_dist = []                      # Paths found for k=max after shortening heuristic, minimising geometric distance

        # Metrics from the run 
        self.shortestpath = []                             # Shortest path found for k=1, saved for convinience                                                
        self.time_core = 0                              # Time needed for the core algoritms to run
        self.time_heur_node = 0                         # Time needed for the shortening heuristic (minimising node count) to run.
        self.time_heur_dist = 0                         # Time needed for the shortening heuristic (minimising geom. dist) to run.

        # Variables associated with the GUI 
        self.gui = None

        
    def get_graph_metrics(self) -> dict:
        return get_graph_metrics_of_solver(self)

    def get_srlg_metrics(self) -> dict:
        return get_srlg_metrics_of_solver(self)

    def get_run_metrics(self) -> dict:
        return get_run_metrics_from_solver(self)

    def get_data(self):
        return {
            'shortest_path': self.shortestpath,
            'res': self.results,
            'path_before_heur': self.maxpaths_bh,
            'path_after_heur_node': self.maxpaths_ah_node,
            'path_after_heur_dist': self.maxpaths_ah_dist
        }

    def wait_for_signal(self, iterfinish=False):
        """Updates GUI with latest information on the paths, then waits for a signal from the GUI to continue.

        Args:
            iterfinish (bool, optional): If iteration is finished, passes solution to GUI. Defaults to False.
        # """        
        if self.gui is None:
            return
        if iterfinish: 
            self.gui._solution = self.results[self.k].copy()
        self.gui.update_canvas()
        self.gui.threadblocker.clear()  # Lower flag
        self.gui.threadblocker.wait()   # Wait for flag to be raised
        if iterfinish: 
            self.gui._solution = None
       
    ## Speeding up heuristic
    def add_to_fallback(self, p):
        self.fallbackqueue.append(p)
        if len(self.fallbackqueue) > self.k: 
            del self.fallbackqueue[0]
    
    
    def _remove_cutting_slrgs(self):
        """Removes SLRG-s form the list which result in all s-t paths getting cut.
        """

        tempG = PlanarGraph(self.jsg, self.jss, self.s, self.t)
        jss_new = []

        for srlg in self.jss:
            cg:nx.Graph = tempG.G.copy()                                       
            cg.remove_edges_from(srlg)

            if not nx.has_path(cg, tempG.s, tempG.t):
                pass #logging.info(f' SLRG {srlg} disconnects s from t! removing.')
            else:
                jss_new.append(srlg)
        return jss_new


    def _calc_max_iter(self):
        """A function to calculate the maximum iterations needed when calculating k srlg-disjoint paths.
        It is |E| - |V| + 3 (so the number of faces in the planar graph + 1)

        Returns:
            int: The maximum number of iterations needed to determine the stopping point.
        """        
        return self.PG.G.number_of_edges() - self.PG.G.number_of_nodes() + 3


    def _path_does_not_cut(self, p):
        """Checks is a given path with any given SLRG would disconnect the graph,
        meaning that there are no possible ways for the DFS to find a path. 
        Returns True is the path is OK, False otherwise.

        Args:
            p (List[int]): The path

        Returns:
            [bool]: True if path is OK
        """        
        for srlg in self._jss_orig:
            cg:nx.Graph = self.PG.G.copy()                                        
            cg.remove_edges_from( [(p[i], p[i+1]) for i in range(0, len(p) -1)] ) 
            cg.remove_edges_from(srlg)                       

            if not nx.has_path(cg, self.PG.s, self.PG.t):
                #logging.warning(f' SLRG {srlg} with path {p} disconnects s from t!')
                return False
        return True
                

    def _get_srlgs_containing_edge(self, u: int, v: int, original=False) -> List[Set[Edge]]:
        """Returns all SLRG-s containing the u-v edge.

        Args:
            u (int): node 1 of the edge
            v (int): node 2 of the edge
            original (bool): If set to true, only takes into SLRG-s originally in the list (without point failures). [Defaults to False]

        Returns:
            List[Set[Edge]]: The list of SLRG-s as Edge sets.
        """        
        res = []
        if original:
            srlgl = self._jss_orig
        else: 
            srlgl = self.jss
        for srlg in srlgl:
            for a, b in srlg: 
                if (a == u and b == v) or (a == v and b == u):
                    res.append(srlg) 
        return [frozenset([Edge(u1,v1) for u1, v1 in srlg]) for srlg in res] 


    def _basecase_tuti(self):
        """Proper function for handling the special base case (setting the stage for k=2)
        """
        
        # 1. step: get two node-disjoint paths (Menger), pick the first one to begin the iteration with 

        G = self.PG.G.copy()
        nx.set_edge_attributes(G, 1, "capacity")
        nx.set_node_attributes(G, {self.s:-2, self.t:2}, "demand")
        scale = 10**6
        lengths = [(u, v, G[u][v]['length'] * scale) for u, v in G.edges()]
        for u, v, nw in lengths:
            G[u][v]['length'] = int(nw)
        flow = nx.min_cost_flow(nx.to_directed(G), weight='length')
        # build back paths from flows: 
        flow_based_paths = []
        for n, f_out in flow[self.s].items():
            if f_out == 0:
                continue
            path = [self.s]
            nextnode = n
            while nextnode != self.t:
                path.append(nextnode)
                nextnode = [k for k, v in flow[nextnode].items() if v == 1][0]
            path.append(self.t)

            flow_based_paths.append(path)

        if len(flow_based_paths) < 2: 
            raise Exception("could not find at least 2 V-disjoint paths")

        P = flow_based_paths[0]

        # 2. step: iterating to max diam/2, while multiplying getting 
        d = max(self.get_srlg_metrics()['sdn']) # get max diameter
        i, maxiter = 1, math.ceil(math.log2(d))
        
        good_path_found = False
        newk = True

        self.oldestpath = P                               
        self.newestpath = P                            # Get the newest path from the solution path queue

        while i <= maxiter:

            # Calculate new set of SLRG-s 
            
            i_srlg = [self.DG.get_shrunk_slrgs(srlg, 2**(i-1)) for srlg in self.jss]     
            i_srlg = list(filter(lambda x: x != [], i_srlg))

            # Load new SRLG set into the Algorithm 1 solver
            shrunksrlgs = self.PG._init_srlg_list(self.jsg, i_srlg)

            
            # Try to caluculate new path based on the main algorithm using the new set of srlgs
            path_found = self.main_alg(shrunksrlgs)

            if not path_found:
                self.finished = True                                # We stop
                self.wait_for_signal(iterfinish=True)
                break

            i += 1

        if path_found:
            self.k += 1 
            self.pathqueue.append(self.novelpath)               # Add new path to queue
            self.results[self.k] = deepcopy(self.pathqueue)     # Copy results 
            self.iternum = 0
            self.wait_for_signal(iterfinish=True)
        else:
            self.finished = True                                # We stop
            self.wait_for_signal(iterfinish=True)

           
    def shortening_heurisctic(self, paths=[], geom=True):

        paths_copy= deepcopy(paths)
        
        last_k_imporvement = [0 for i in range(len(paths_copy))]     # start with a dummy improvement list

        iternum = 0

        while sum(last_k_imporvement) != 0 or iternum <= len(paths_copy):

            iternum += 1

            # delete last path 
            origlen = self.PG.cost_of_path(paths_copy[0])
            origpath = deepcopy(paths_copy[0])
            del paths_copy[0]
            
            
            edges_to_remove = set()
            for fixedpath in paths_copy: 
                # get edges that are in common SLRG-s with any other paths.
                edges_to_remove.update( *[self.PG.S[edge] for edge in path_to_edgelist(fixedpath) ] )
                edges_to_remove.update( path_to_edgeset(fixedpath) )
                # get edges that conect to nodes already used by other paths 
                edges_to_remove.update( self.PG.edges_on_path(fixedpath) )

            # Remove edges from the copy of the graph
            G2:nx.Graph = self.PG.G.copy()
            for e in edges_to_remove: 
                a, b = e.unpack()
                G2.remove_edge(a, b)

            if geom:
                shortenedpath = nx.shortest_path(G2, self.PG.s, self.PG.t, weight="length")
            else:
                shortenedpath = nx.shortest_path(G2, self.PG.s, self.PG.t)

            
            newlen = self.PG.cost_of_path(shortenedpath)
            imp = origlen - newlen
            if imp < 0:
                imp = 0
                paths_copy.append(origpath)
            else:
                paths_copy.append(shortenedpath)
                del last_k_imporvement[0]
            last_k_imporvement.append(imp)

            log.debug(f'Shortened path {shortenedpath} imporovement {imp}')
            
        # If we are done, shift pathqueue back to original:
        for i in range(self.k - (iternum % self.k)):
            paths_copy.append(paths_copy[0])
            del paths_copy[0]
        
        return paths_copy

    def solve(self):
        """ The function solving our problem :)
        """        

        starttime = time.time()

        # STEP 0: Find shortest s->t path (heuristics)
        self.shortestpath = nx.shortest_path(self.PG.G, self.PG.s, self.PG.t, weight="length")
        log.info(f'Shortest path found: {self.shortestpath}')


        # SOLUTION K = 1
        self.k += 1 
        self.pathqueue.append(self.shortestpath)
        self.results[self.k] = [self.shortestpath]

        self.wait_for_signal(iterfinish=True)       # IMPORTANT: these calls are for the GUI. If no gui is set, nothing happens. 

        # STEP 1: Assuming there is an s-t path, and assuming there are no cutting SRLG-s
        # try to fid k=2 solution.  
        self._basecase_tuti()

        # STEP 2: Using the already found k (>=2) paths, try calculating k+1 new paths 

        # SOLUTIONS K >= 3
        
        while not self.finished:

            good_path_found = self.main_alg()

            if good_path_found:
                self.k += 1 
                self.pathqueue.append(self.novelpath)               # Add new path to queue
                self.results[self.k] = deepcopy(self.pathqueue)     # Copy results 
                self.iternum = 0
                self.wait_for_signal(iterfinish=True)
            else:
                self.finished = True                                # We stop
                self.wait_for_signal(iterfinish=True)


        self.time_core = time.time() - starttime
        
        self.maxpaths_bh = deepcopy(self.results[self.k])
        
        # Now we can begin with the shortening heuristic for max found k.
        # self.pathqueue = deepcopy(self.results[self.k])
        
        starttime = time.time()
        self.maxpaths_ah_node = self.shortening_heurisctic(paths=self.maxpaths_bh, geom=False)
        self.time_heur_node = time.time() - starttime
        
        starttime = time.time()
        self.maxpaths_ah_geom = self.shortening_heurisctic(paths=self.maxpaths_bh, geom=True)
        self.time_heur_dist = time.time() - starttime

        self.results[self.k] = deepcopy(self.maxpaths_ah_geom) # Copy back results 
        
        self.wait_for_signal(iterfinish=True)
        print('solved')

    def main_alg(self, srlgs_set=None): 
        good_path_found = False
        newk = True
        for i in range(self.max_iter):
            
            self.iternum += 1

                # if the fallbackqueue is the same as the pathqueue it means we have come "full cycle" and no further improvements are possible
            if self.fallbackqueue == self.pathqueue:
                self.finished = True
                log.debug('Stopping because no further imporvements are possible')
                break

            self.oldestpath = self.pathqueue[0]                                 # Get the oldest path from the solution path queue
            self.newestpath = self.pathqueue[-1]                                # Get the newest path from the solution path queue
            self.novelpath = self.PG.caluclate_next_cw_path(self.newestpath, srlgs_set, newk=newk)    # Calculate novel (k+1 th), closest CW path to the newest

            self.wait_for_signal()

            # If new path is srlg- and point-disjoint with the oldest path we are done with the k-th iteration!
            if self.PG.srlg_disjoint(self.oldestpath, self.novelpath, srlgs_set) and self.oldestpath != self.novelpath:
                good_path_found = True
                log.info(f'good path for k = {self.k} found!')
                self.fallbackqueue = []
                break
            # If not, delete oldest path and add novel path to the end of the queue
            else:
                self.add_to_fallback(deepcopy(self.pathqueue[0]))
                del self.pathqueue[0]
                self.pathqueue.append(self.novelpath)
                newk=False
        return good_path_found

            
    def min_cut(self):
        # TODO: calculate MIN-CUT using algorithm
        pass