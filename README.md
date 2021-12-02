# dijsjoint-py

Python implementation of the algorithms seen in the article titled *"The Regional SRLG-disjoint Flow Problem is in P: Polynomial Algorithm and Max-Min Theorem"*

## Usage

We use `networkx` for graph storage and operations. You can install it by typing `pip install networkx`. Everything else is included with python.

Correct CLI usage: 

`python routesrlg.py <input graph> <input srlg list> <s> <t> [optinal args]`

Arguments are the following: 

`<input graph>` - .lgf, .gml, .graphml or .json of the planar graph

`<input srlg list>` - .json of the SLRGs. Check `/data` for the example format

`<s>` - source node of the graph

`<t>` - target node of the graph

`-v` - (optional) display more output information

`-d` - (optional) display technical, debug information

`-u` - (optional) display a GUI. 

`-h` - (optional) display help

## Code and repository structure

- `/data` - Input files (graph and srlg-list)

- `/out` - Output files (solution, other)

- `/src` - Code 

  - `/geometry`

    - `Vec2.py` - Class designed to handle 2D vectors and operations

    - `Point.py` - Class designed to represent points on the 2D plane.

    - `operations_2d.py` - Functions on 2D vectors like dot product, polar angle computation, etc.

  - `/util`

    - `HelperClasses.py` - `Edge` and `Circulator` classes speeding up the algorithm by a bit 

    - `HelperFunctions.py` - Functions to generate structures and calulate paths for a faster computation

    - `JsonGraphGenerator.py` - Class for converting every graph to json, providing and interface between various input formats and the program itself
  
  - `PlanarGraph.py` - Class representing the graph, handling our custom DFS, as well as some other things.

  - `SlrgDisjointSolver.py` - Class handling the main algorithm.

  - `SolverGUI.py` - A Class based on python's `tkinter` providing a moderately pretty, but handy GUI.

- `routesrlg.py` - Entry script for a single network-srlg-s-t combination run


## Metrics:

Metrics are a bit tricky. The aggregated XML file contains graph, srlg and run metrics in a tree below each other. It looks like this: 

```xml
<graphs>
  <graph>
    (graph metrics)
    <srlgs>
      <srlg>
        (srlg metrics)
        <runs>
          <run>
            (run metrics)
          </run>
          {more runs}
        </runs>
      </srlg>
      {more srlgs}
    </srlgs>
  </graph>
  {more graphs}
</graphs>
```

The following graph metrics are avalible:

| Metric | Description |
|--------|-------------|
| .V | Number of nodes |
| .E | Number of edges |
| .maxiter | Max. Number of iterations where stopping is guaranteed|
| .iternum | Number of iterations needed to exhaust (either maxiter, or  if the heuristic stopped, a smaller number than that) |
| .dg | Longest geometric shortest path from any source to any target (diameter geometric) |
| .dn | Longest shortest path from any source to any target (diameter node) |
| .c | Node connectivity of graph |
| .telen | Sum of geometric edge lengths (total edge length) |

The following SRLG metrics are avalible:

| Metric | Description |
|--------|-------------|
| .gen | Method of generation |
| .ns | Number of SRLGs in used input |
| .sec | (LIST) .sec_item list of edge counts for each srlg (srlg_edge_counts) |
| .sdn | (LIST) .sdn_item list of srlg diameters (in nodes) (srlg_diameters_n) |

The following run metrics are avalible:

| Metric | Description |
|--------|-------------|
| .s | Source node of run |
| .t | Target node of run |
| .stc | Max number of node disjoint paths connecting s to t ( s_t_connectivity) |
| .k | max number of srlg-disjoint paths found |
| .ti_c | Runtime of the core algorithm |
| .ti_hn | Runtime of the node count minimising shortening heuristic algorithm |
| .ti_hd | Runtime of the geometric cost (path length) minimising shortening heuristic algorithm  |
| .pl_bh_avg_node | Avarage node count of paths found before any heuristic optimization |
| .pl_bh_avg_dist | Avarage geometric length of paths found before any heuristic optimization |
| .pl_ahn_avg_n | Avg. path length in nodes after heuristic opt. for node count |
| .pl_ahn_min_n | Min. path length in nodes after heuristic opt. for node count |
| .pl_ahn_max_n | Max. path length in nodes after heuristic opt. for node count |
| .pl_ahn_avg_d | Avg. geometric path length after heuristic opt. for node count |
| .pl_ahn_min_d | Min. geometric path length after heuristic opt. for node count |
| .pl_ahn_max_d | Max. geometric path length after heuristic opt. for node count |
| .pl_ahd_avg_n | Avg. path length in nodes after heuristic opt. for geom. length |
| .pl_ahd_min_n | Min. path length in nodes after heuristic opt. for geom. length |
| .pl_ahd_max_n | Max. path length in nodes after heuristic opt. for geom. length |
| .pl_ahd_avg_d | Avg. geometric path length after heuristic opt. for geom. length |
| .pl_ahd_min_d | Min. geometric path length after heuristic opt. for geom. length |
| .pl_ahd_max_d | Max. geometric path length after heuristic opt. for geom. length |
| .spln | Number of nodes in shortest path  from s to t|
| .spld | Total length of shortest geometric path from s to t|
| .tssn | Sum of node counts in two shortest srlg-disjoint paths (two_shorterst_srlg_node) |
| .tssd | Sum of lengths of the two shortest srlg-disjoint paths (two_shorterst_srlg_dist) |
| .tsfn | Sum of number of nodes in the two shortest node-disjoint paths (optimized for node count) (two_shortest_flow_node) |
| .tsfd | Sum of lengths of the two shortest node-disjoint paths (optimized for length) (two_shortest_flow_dist) |
| .si | (LIST) .si_item list of the number of srlg-s each of the k paths are intersecting. (srlg_intersections) |
