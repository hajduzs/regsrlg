from src.util.HelperClasses import Edge
from typing import List, Set
import networkx as nx

def path_to_edgelist(path: List[int]) -> List[Edge]:
    """Return path as a list of Edges. Used mainly for iterations.

    Args:
        path (List[int]): The list of nodes making up the path: [v1, v2, .. vn]

    Returns:
        List[Edge]: The resulting Edge list. [{v1, v2}, {v2, v3}, .. {vn-1, vn}]
    """    
    return [Edge(path[i], path[i+1]) for i in range(len(path) - 1)]

def path_to_edgeset(path: List[int]) ->Set[Edge]:
    """Return path as a set of Edges. Used for quickly checking if path contains given edge.

    Args:
        path (List[int]): The list of nodes making up the path: [v1, v2, .. vn]

    Returns:
        Set[Edge]: The resulting set of {vi, vi+1} edges 
    """    
    return set(path_to_edgelist(path))


def clockwise_dfs(G: nx.Graph, s:int, t:int, path:List[int]) -> List[int]:
    """A common DFS impementation, preferring to check outgoing edges in a clockwise
    orientation from the incoming edge.

    Args:
        G (nx.Graph): The graph to perform the search on
        s (int): Source node
        t (int): End node 
        path (List[int]): Current oldest path

    Returns:
        List[int]: The found path as a list of nodes
    """    

    pn = path[0]
    # We define a recursive funtion in this scope, because the outer function 
    # just provides a simpler way to call the function from outside the class.
    def simple_dfs(G, visited, n, pn, t):
        if n in visited:
            return []           # Return and empty list if we have already seen this node

        if n == t:
            return [n]          # Return the node when we arrive at the target node

        if n != s and n in path:
            return []           # Return an empty list if the node is not the source and already used by the given path

        
        visited.add(n)          # Add node to nodes already visited during a DFS run
        
        for ne in G.nodes[n]['circulator'].clockwise_iterator(pn):     # Continue on the next cw oriented edge
            subdfs = simple_dfs(G, visited, ne, n, t) 
            if subdfs != []:
                return [n] + subdfs     # Roll back on the found s->t path 
        return [] # If we run out of neighbours, go back by returning an empty list
    
    # Calling previously defined function.
    return simple_dfs(G, set(), s, pn,t)


