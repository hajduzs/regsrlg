

from re import I


def convert_srlgs_from_lgf(file):

    edges = {}
    slrgs = []

    
    with open(file, 'r') as f:
        lines = f.readlines()


    switch = False
    readedges = False
    readsrlgs = False
    for i in range(len(lines)):

        if lines[i] == '@edges\n':
            switch = True
            continue
            
        if switch:
            switch = False
            readedges = True
            continue

        if lines[i] == '@srlgs\n':
            readedges = False
            readsrlgs = True
            continue

        if readedges:
            u, v, l, _ = lines[i].split('\t')
            edges[l] = [int(u), int(v)]

        if readsrlgs:
            slrgs.append([edges[l] for l in lines[i].split(' ')[:-1]])         

    if slrgs[-1] == []:
        del slrgs[-1]

    return slrgs
