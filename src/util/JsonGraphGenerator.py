"""This module contains the JSON graph converter class, which is used
to convert various graph descriptor formats into a unified .json structure, 
as well as code related to JsonGraphGenerator: functions for input handling and graph data operations"""

from math import cos, pi
import networkx as nx
import re
import json

def convert_lat_long_to_x_y(graph: dict, sensitivity: int = 2):
    """Converts coordinates found in the graph dict from lat-long to x-y by projection

    :param graph:  The input graph
    :param sensitivity: How many decimals should stay in the new coordinate values.
    """
    candidate_nodes = [(node["coords"][0], node["coords"][1], node["id"]) for node in graph["nodes"]]

    avg_lon = sum([n[0] for n in candidate_nodes]) / len(candidate_nodes)
    avg_lat = sum([n[1] for n in candidate_nodes]) / len(candidate_nodes)

    new_nodes = []
    for n in candidate_nodes:
        dx = (avg_lon - n[0]) * 40000 * cos((avg_lat + n[1]) + pi / 360) / 360
        dy = (avg_lat - n[1]) * 40000 / 360
        new_nodes.append({
            "id": int(n[2]),
            "coords": [
                round(dx, sensitivity),
                round(dy, sensitivity)
            ]
        })

    graph["nodes"] = new_nodes


def prep_graph_for_json_dump(path: str, nodes: list, edges: list) -> dict:
    """Helper function preparing graphs for json dumping or further use.
    Only used inside the _functions module!

    :param path: The full path of the graph (name is derived from this)
    :param nodes: The nodes of the graph in a list
    :param edges: The edges of the graph in a list
    :return: A complete dictionary of base data needed
    """
    return {
        "name": path.split("/")[-1].split(".")[0],
        "nodes": nodes,
        "edges": edges
    }


'''
    The functions handling different file formats:
'''


def json_dict_from_gml(file: str) -> dict:
    """ Returns the JSON dict from .gml input file.

    :param file: Input filepath
    :return: the JSON dict
    """
    g = nx.read_gml(file, label='id')

    node_data = g.nodes(data=True)
    edge_data = g.edges(data=True)

    nodes, edges, forbidden_nodes = [], [], []

    if u'Longitude' in node_data[1]:
        for node_id, data in node_data:
            if u'Longitude' not in [k for k, v in data.items()]:
                forbidden_nodes.append(node_id)
                continue

            nodes.append({
                "id": int(node_id),
                "coords": [
                    data[u'Longitude'],
                    data[u'Latitude'],
                ]
            })

    elif u'graphics' in node_data[1]:
        for node_id, data in node_data:
            nodes.append({
                "id": int(node_id),
                "coords": [
                    data['graphics']['x'],
                    data['graphics']['y'],
                ]
            })
    elif u'pos' in node_data[1]:
        for node_id, data in node_data:
            nodes.append({
                "id": int(node_id),
                "coords": data['pos']
            })
    else:
        raise Exception("??")   # TODO

    for n1, n2, data in edge_data:
        if n1 in forbidden_nodes or n2 in forbidden_nodes:
            continue
        edges.append({
            "from": int(n1),
            "to": int(n2)
        })

    return prep_graph_for_json_dump(file, nodes, edges)


def json_dict_from_lgf(file: str) -> dict:
    """ Returns the JSON dict from .lgf input file.

    :param file: Input filepath
    :return: the JSON dict
    """
    f = open(file, 'r')
    all_line = f.read().split('\n')
    all_match = [re.findall(r'^(\d+)\t\((.+),(.+)\)|^(\d+)\t(\d+)\t(\d+)', line) for line in all_line]
    all_match = filter(len, all_match)
    nodes = []
    edges = []
    for line in all_match:
        line = line[0]
        if line[3] == '':
            nodes.append({
                "id": int(line[0]),
                "coords": [
                    float(line[1]),
                    float(line[2])
                ]
            })
        else:
            edges.append({
                "from": int(line[3]),
                "to": int(line[4])
            })

    return prep_graph_for_json_dump(file, nodes, edges)


def json_dict_from_graphml(file: str) -> dict:
    """ Returns the JSON dict from .graphml input file.

    :param file: Input filepath
    :return: the JSON dict
    """
    g = nx.read_graphml(file)
    nodes = []
    for n in g.nodes(data=True):
        nodes.append({
            "id": n[0],
            "coords": [
                n[1]['x'],
                n[1]['y']
            ]
        })

    edges = [{"from": e[0], "to": e[1]} for e in g.edges]

    return prep_graph_for_json_dump(file, nodes, edges)


def json_from_json(file: str) -> dict:
    return json.load(open(file,))



""" Supported formats: if a new format is introduced,
append the corresponding function below this block, 
and import it into the dict for easier use. 
"""
_SUPPORTED_FORMATS = {
    "lgf": json_dict_from_lgf,
    "gml": json_dict_from_gml,
    "graphml": json_dict_from_graphml,
    "json": json_from_json
}


class JsonGraphGenerator:
    """Class made for generating usable .json data from various input graph formats."""
    def __init__(self, file):
        """ Initializes raw data from input file."""
        ext = file.split('.')[-1]
        if ext not in _SUPPORTED_FORMATS:
            raise Exception("Not supported file format!")
        self._dump = _SUPPORTED_FORMATS[ext](file)

    def gen_json(self, auto_convert=True):
        """ Returns json compatible data of converted graph.
        :param auto_convert: If true, detects if input is in lat-long format,
        and projects it to a 2D plane
        :return: a JSON object containing graph information
        """
        if not auto_convert:
            return self._dump
        else:
            for n in self._dump['nodes']:
                lon_ovr = n['coords'][0] < -180 or 180 < n['coords'][0]
                lat_ovr = n['coords'][1] < -90 or 90 < n['coords'][1]
                if lon_ovr or lat_ovr:
                    return self._dump
            convert_lat_long_to_x_y(self._dump, sensitivity=4)
            return self._dump
