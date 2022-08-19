from typing import List, Tuple
from src.geometry.operations_2d import theta
from src.geometry.Point import Point

import logging
log = logging.getLogger(__name__)

class Edge:
    """Edge class for hashing and quick access to edges, as well as srlg-s
    """    
    def __init__(self, x, y) -> None:
        self.x = x  # To preserve direction if needed
        self.y = y  # same
        if x < y:
            self.a = x ; self.b = y
        else:
            self.a = y ; self.b = x
        
    def __repr__(self) -> str:
        return f'{self.x}->{self.y}'

    def __hash__(self) -> int:
       return hash(f'{self.a}-{self.b}')         
    
    def __eq__(self, o: object) -> bool:
        return self.a == o.a and self.b == o.b

    def __getitem__(self, i):
        if i == 0:
            return self.x
        if i == 1:
            return self.y
        return Exception('Edges are only indexable by 0 (x) or 1 (y)!')

    def unpack(self)-> Tuple[int, int]:
        """Unpacks edge, returning from-to (x->y) values as a tuple

        Returns:
            Tuple[int, int]: The 2-tuple of x and y
        """        
        return self.x, self.y

class DirectedEdge(Edge):
    """Directed Edge class for hashing, and quick finding of the dual graph
    """
    def __hash__(self) -> int:
       return hash(f'{self.x}-{self.y}')         
    
    def __eq__(self, o: object) -> bool:
        return self.x == o.x and self.y == o.y

    def opposite(self):
        """Get the Directed edge opposite of self (u->v).

        Returns:
            DirectedEdge: Directed edge going from v to u.
        """        
        return DirectedEdge(self.y, self.x)
    
    def to_undirected(self):
        """Get undirected version for hashing when needed
        """
        return Edge(self.x, self.y)


class Circulator:
    """Circualtor class helping with the setting of clockwise precedence during the DFS and other operations.
    """    
    def __init__(self, nc: Point, edgelist:List[Tuple[int, Point]]) -> None:
        """Constructs the circulator and sorts edges to be in cw rotation.

        Args:
            nc (Point): Coordinate of the starter node
            edgelist (List[Tuple[int, Point]]): List containing the neighboring nodes of nc with (id, coordinate) tuples
        """        
        self._edgelist = [ne for ne, _ in sorted(edgelist, key=lambda x: theta(x[1] - nc))]
        #log.debug(f'Edgelist for nc {nc}: {self._edgelist}')

    def __len__(self):
        return len(self._edgelist)

    def __getitem__(self, i):
        return self._edgelist[i]


    def clockwise_iterator(self, id:int) -> List[int]:
        """Returns the nodes from the circulator after a given node. - The First cw node after the given id will be the first.

        Args:
            id (int): The id of the node to "sort after" 

        Returns:
            [List[int]]: A list of nodes coming after the node with 'id'.
        """        
        index = -1
        for i in range(0, len(self)):
            if self[i] == id:
                index = i
        
        #log.debug(f'id {id} found in {self._edgelist} @ index {index}')
        #log.debug(f'CW iterator precedence: {self[index+1:len(self)] + self[0:index+1]}')
        return self[index+1:len(self)] + self[0:index+1]