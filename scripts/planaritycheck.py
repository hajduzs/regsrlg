from src.util.JsonGraphGenerator import JsonGraphGenerator
import itertools 
from src.geometry.Point import Point

gfiles = [
    "sim_v2_0723morning/16_optic_pan_eu_scaled/16_optic_pan_eu_scaled.lgf",
    "sim_v2_0723morning/22_optic_eu_scaled/22_optic_eu_scaled.lgf",
    "sim_v2_0723morning/24_us_wide_scaled/24_us_wide_scaled.lgf",
    "sim_v2_0723morning/28_optic_eu_scaled/28_optic_eu_scaled.lgf",
    "sim_v2_0723morning/39_optic_north_american_scaled/39_optic_north_american_scaled.lgf",
    "sim_v2_0723morning/79_optic_nfsnet_scaled/79_optic_nfsnet_scaled.lgf",
    "sim_v2_0723morning/ATT-L1-Modified_/ATT-L1-Modified_.gml",
    "sim_v2_0723morning/att-phys_/att-phys_.gml",
    "sim_v2_0723morning/sprint-phys_/sprint-phys_.gml",
    "sim_v2_0723morning/USFibre_/USFibre_.gml"
]

def ccw(A,B,C):
    return (C.y-A.y) * (B.x-A.x) > (B.y-A.y) * (C.x-A.x)

# Return true if line segments AB and CD intersect
def intersect(A,B,C,D):
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

for gfile in gfiles:
    print(f'checkig {gfile} planarity -----------------------------------------')
    jg = JsonGraphGenerator(gfile).gen_json(auto_convert=False)

    coordict = {node['id']:node['coords'] for node in jg['nodes']}

    intersectfound = False

    for e1, e2 in itertools.combinations(jg['edges'], 2):
        a,b,c,d = [object() for i in range(4)]
        a = Point(*coordict[e1['from']])
        b = Point(*coordict[e1['to']]    )
        c = Point(*coordict[e2['from']])
        d = Point(*coordict[e2['to']])
        if a == c or a == d or b==c or b==d:
            continue
        if intersect(a,b,c,d):
            print(f'!!: {e1} - {e2}')
            intersectfound = True

    if not intersectfound:
        print('OK Given graph seems to be planar')