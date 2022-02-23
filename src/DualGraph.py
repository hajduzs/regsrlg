
import networkx as nx
from networkx.classes.function import subgraph
from src.geometry.Point import Point
from src.geometry.operations_2d import point_to_point
from src.util.HelperClasses import DirectedEdge, Edge


class DualGraph():

    def __init__(self, pg):
        self.PG = pg
        self.G = self._init_dual()

    def _init_dual(self):
        
        def find_dual():
            processed = set()
            regions = set()

            def check_edge(f: DirectedEdge):
                if f in processed:
                    return
                processed.add(f)
                
                f1, f2 = f.unpack()
                right_region = self.PG.right_region(f1, f2, directed = True)
                regions.add(right_region)

                for e in right_region:
                    check_edge(e)

            # Start from the first outgoing edge from the source 
            # (Out of convinince, it really  should not matter) 
            u = self.PG.s
            v = list(self.PG.G.neighbors(u))[0]
            
            check_edge(DirectedEdge(u,v))

            return regions

        regions = find_dual()

        def middle_point(face):
            p = Point(0,0)
            for e in face:
                p += self.PG.G.nodes[e[0]]['coords']
            return p / len(face)

        dualnodes = {f:(i, middle_point(f)) for i, f in enumerate(regions)}

        edge_regions = dict()
        for region in regions:
            for de in region:
                e = Edge(*de.unpack())
                if e in edge_regions:
                    edge_regions[e].append(region)
                else:
                    edge_regions[e] = [region]


        # Build the dual graph from face data
        DG = {
            "name": "dual",
            "nodes": [],
            "edges": []
        }

        for id, coords in dualnodes.values():
            DG['nodes'].append({
                'id': id,
                'coords': coords
            })

        for edge, regions in edge_regions.items():
            DG['edges'].append({
                'of': edge[0],
                'ot': edge[1],
                'from': dualnodes[regions[0]][0],
                'to': dualnodes[regions[1]][0],
            })

        g = nx.MultiGraph()
        for n in DG['nodes']:  # Get every point of the graph with coordinates
            g.add_node(n['id'], coords = Point(n['coords'][0], n['coords'][1]))

        for e in DG['edges']:  # Get every edge of the graph with lengths caluclated from the coordinates
            g.add_edge(
                e['from'],
                e['to'],
                of = e['of'],
                ot = e['ot'], 
            )
        
        return g

    def get_shrunk_slrgs(self, srlg, di):

        # get the subgraph composited of the SRLG
        DSLRG = nx.Graph()
        dualedges = []
        for e, f in srlg:
            for u, v, d in self.G.edges(data=True):
                if (e == d['ot'] and f == d['of']) or (e == d['of'] and f == d['ot']):
                    dualedges.append([u, v])
        DSLRG.add_edges_from(dualedges)

        # "Blow up" the subgraph according to the rule 
        subgraphs = []
        paths = dict(nx.all_pairs_shortest_path(DSLRG))
        
        for dn in DSLRG.nodes:
            reachable_dual_nodes = []
            for k, v in paths[dn].items(): 
                if len(v) <= di: 
                    reachable_dual_nodes.append(k)
            H = DSLRG.subgraph(reachable_dual_nodes)
            subgraphs.append(H)

        # Convert the remaining subgraphs back to primal edge sets 
        # And throw out |S| = 1 sets 
        newsets = []
        for SG in subgraphs:
            if len(SG.edges()) == 1:
                continue
            s_set = []
            for u, v in SG.edges():
                s_set.append((
                    self.G[u][v][0]['ot'], 
                    self.G[u][v][0]['of']
                ))
            newsets += s_set

        return newsets
