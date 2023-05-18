import json

def load_srlgs_fromfile(filepath):
    if filepath.split(".")[-1] == "json":
        return json.load(filepath)
    
    with open(filepath, "r") as f:
        lines = f.readlines()

        e_ix = lines.index("@edges\n")
        s_ix = lines.index("@srlgs\n")
        
        edges = lines[e_ix+2:s_ix]
        ed = {s.split("\t")[2]:[int(s.split("\t")[0]), int(s.split("\t")[1])] for s in edges}
        ret = []
        for srlg in lines[s_ix+1::]:
            ret.append([ed[x] for x in srlg.split(" ")[:-1]])

        return ret 