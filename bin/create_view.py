import argparse
import json
from itertools import product

def args_gestion():
    parser = argparse.ArgumentParser(description = "Create couchDB views to store sgRNA - specie combination")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-m", "--mapper", metavar = "<json>", help = "Json file with mapping rules")
    group.add_argument("-d", "--depth", metavar = "<int>", help = "Depth for regex construction (1 for one letter, 2 for 2 letters...)", type = int)
    parser.add_argument("-o", "--output", metavar = "<json>", help = "Json output with created design document", required = True)

    return parser.parse_args()

def construct_view(regexp):
    view = {
            "map" : 'function(doc) { var regexp = new RegExp("' + regexp + '"); if (regexp.test(doc["_id"])){ for (var org in doc) { if (org.charAt(0) != "_") { var nb_occurences = 0; for (var seq_ref in doc[org]){ nb_occurences = nb_occurences + doc[org][seq_ref].length } emit(org, nb_occurences)}}}}'
    }
    return view

def create_mapper(depth):
    mapper = {}
    nt = "ACGT"
    nb_view = 0
    prefix = 20 - depth
    for comb in product(nt, repeat = depth):
        nb_view += 1
        regexp = "^[ACGT]{3}" + "".join(comb) + "[ACGT]{" + str(prefix) + "}$"
        mapper[regexp] = f"organisms{nb_view}"
    
    return mapper

if __name__ == "__main__":
    global ARGS
    ARGS = args_gestion()
    all_design = {'views' : {}}
    if ARGS.mapper:
        print("Use given mapper")
        mapper = json.load(open(ARGS.mapper))

    elif ARGS.depth:
        print("Construct mapper from depth")
        mapper = create_mapper(ARGS.depth)
        print(f"{len(mapper)} views will be construct")

    for regexp,view_name in mapper.items():
        all_design["views"][view_name] = construct_view(regexp)

    with open(ARGS.output, "w") as o:
        json.dump(all_design, o) 
   