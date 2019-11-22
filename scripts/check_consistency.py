import argparse
import os
import errno
import glob
import requests
import json
from ete3 import Tree

def args_gestion():
    parser = argparse.ArgumentParser(description = "Check consistency between index, taxon_tree and taxon_db. For now, just compare GCF and/or names and don't check if genomes not in taxon_tree are anterior version of present genomes.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--index", help = "Genome index directory", required = True)
    parser.add_argument("--url", help = "couchDB url", required = True)
    parser.add_argument("--taxon_tree_name", help = "taxon_tree database name", default = "taxon_tree")
    parser.add_argument("--taxon_db_name", help = "taxon_db database name", default = "taxon_db")
    args = parser.parse_args()
    # Check index directory
    if not os.path.isdir(args.index):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), args.index)
    
    return args

def get_index_names_gcf(index_dir):
    dic = {}
    index_files = [f.split("/")[-1] for f in glob.glob(index_dir + "/*.index")]
    index_names = [f.replace(".index", "") for f in index_files]
    for n in index_names :
        species = " ".join(n.split(" ")[:-1])
        gcf = n.split(" ")[-1]
        if species not in dic:
            dic[species] = []
        dic[species].append(gcf)
    return dic 

def get_taxon_tree_names_gcf(database_url):
    def get_leaves(subtree, leaves_list):
        if not subtree.get("children"):
            leaves_list.append(subtree["text"])
        else:
            for child in subtree["children"]:
                get_leaves(child, leaves_list)    
        return leaves_list

    session = requests.Session()
    session.trust_env = False # to avoid proxy error
    taxon_tree = session.get(database_url + "/maxi_tree").json()
    taxon_tree = json.loads(taxon_tree["tree"].replace("'", '"'))
    leaves_list = []
    leaves_list = get_leaves(taxon_tree, leaves_list)
    taxon_tree_names = [l.split(" : ")[0] for l in leaves_list]
    dic = {}
    for n in taxon_tree_names:
        species = " ".join(n.split(" ")[:-1])
        gcf = n.split(" ")[-1]
        if species not in dic:
            dic[species] = []
        dic[species].append(gcf)
    return dic        

def get_taxon_db(database_url):
    taxon_db_gcf = []
    session = requests.Session()
    session.trust_env = False # to avoid proxy error
    taxon_db_keys = [r["id"] for r in session.get(database_url + "/_all_docs").json()["rows"]]
    dic = {}
    for k in taxon_db_keys:
        doc = session.get(database_url + "/" + k).json()
        taxid = doc["_id"]
        gcfs = doc["GCF"]
        dic[taxid] = gcfs
    return dic    
   

def check_redundancy(list_elements):
    if len(list_elements) != len(set(list_elements)):
        for elmt in set(list_elements):
            count = list_elements.count(elmt)
            if count > 1:
                print(elmt, count)
    else:
        print("No redundancy")

def check_anteriority(index_not_tree, tree_dic, index_dic, taxon_db_dic):
    no_correspondance = []
    anteriority = []
    no_anteriority = []
    for gcf in index_not_tree:
        species = [species for species in index_dic if gcf in index_dic[species]]
        if len(species) > 1:
            raise Exception("More than 1 species in check_anteriority(). Handle this.")
        species = species[0]
        try:
            tree_gcf = tree_dic[species]
        except KeyError:
            no_correspondance.append(species + " " + gcf)
            continue
        if len(tree_gcf) > 1:
                raise Exception(species, tree_gcf, "more than 1 gcf. Handle this")
        tree_gcf = tree_gcf[0]
        taxon_db_gcf = [taxon_db_dic[taxid] for taxid in taxon_db_dic if tree_gcf in taxon_db_dic[taxid]]
        if len(taxon_db_gcf) > 1:
            raise Exception(taxon_db_gcf, "More than one entry in taxon_db")
        taxon_db_gcf = taxon_db_gcf[0]
        if gcf in taxon_db_gcf:
            anteriority.append(species + " " + gcf)
        else:
            no_anteriority.append(species + " " + gcf)

    if anteriority:
        print("* Have newer version in tree")   
        for elmt in anteriority:
            print(elmt) 
    if no_anteriority:
        print("* Have species name in tree but it's not an anterior version of it")
        for elmt in no_anteriority:
            print(elmt)
    if no_correspondance:
        print("* Have no correspondance in tree")
        for elmt in no_correspondance:
            print(elmt)


def __main__():
    args = args_gestion()
    index_dic = get_index_names_gcf(args.index)
    index_gcf = [gcf for species in index_dic for gcf in index_dic[species]]
    taxon_tree_dic = get_taxon_tree_names_gcf(args.url + "/" + args.taxon_tree_name)
    taxon_tree_gcf = [gcf for species in taxon_tree_dic for gcf in taxon_tree_dic[species]]
    taxon_db_dic = get_taxon_db(args.url + "/" + args.taxon_db_name)
    taxon_db_gcf = [gcf for taxid in taxon_db_dic for gcf in taxon_db_dic[taxid]]
    #print(index_dic)
    #print(taxon_tree_dic)

    print("* Redundancy taxon_tree")
    check_redundancy(taxon_tree_gcf)
    print("* Redundancy index")
    check_redundancy(index_gcf)
    print("* Redundancy taxon_db")
    check_redundancy(taxon_db_gcf)
    print()
    print("# CONSISTENCY : TAXON_TREE & INDEX")
    index_not_tree = set(index_gcf).difference(set(taxon_tree_gcf))
    tree_not_index = set(taxon_tree_gcf).difference(set(index_gcf))
    if tree_not_index:
        print("##", len(tree_not_index), "genome(s) in taxon_tree and not in index")
        for g in tree_not_index:
            species = [species for species in taxon_tree_dic if g in taxon_tree_dic[species]]
            print(g, species)
    else:
        print("## All genomes in taxon_tree are in index")            

    if index_not_tree:
        print("##", len(index_not_tree), "genome(s) in index and not in taxon_tree")
        check_anteriority(index_not_tree, taxon_tree_dic, index_dic, taxon_db_dic)
    else:
        print("## All genomes in index are in taxon_tree")    
    print()
    print("# CONSISTENCY : TAXON_DB & INDEX")  
    taxondb_not_index = set(taxon_db_gcf).difference(set(index_gcf))
    index_not_taxondb = set(index_gcf).difference(set(taxon_db_gcf))
    if taxondb_not_index:
        print("##", len(taxondb_not_index), "genome(s) in taxon_db and not in index")
        for elmt in taxondb_not_index:
            print(elmt)
    else:
        print("## All genomes in taxon_db are in index")    
    
    if index_not_taxondb:
        print("##", len(index_not_taxondb), "genome(s) in index and not in taxon_db")
        for elmt in index_not_taxondb:
            species = [species for species in index_dic if elmt in index_dic[species]]
            print(elmt, species)
    else:
        print("## All genomes in index are in taxon_db")        

    print()
    print("# CONSISTENCY : TAXON_DB & TAXON_TREE")
    taxon_db_current_gcf = [taxon_db_dic[taxid][0] for taxid in taxon_db_dic]
    taxondb_not_in_tree = set(taxon_db_current_gcf).difference(set(taxon_tree_gcf))
    tree_not_in_taxondb = set(taxon_tree_gcf).difference(set(taxon_db_current_gcf))
    if taxondb_not_in_tree:
        print("##", len(taxondb_not_in_tree), "genome(s) in taxon_db and not in taxon_tree")
        for gcf in taxondb_not_in_tree:
            print(gcf)
    else:
        print("## All genomes in taxon_db are in taxon_tree")
    if (tree_not_in_taxondb):
        print("##", len(tree_not_in_taxondb), "genome(s) in taxon_tree and not in taxon_db")
        for gcf in tree_not_in_taxondb:
            species = [species for species in taxon_tree_dic if gcf in taxon_tree_dic[species]]
            print(gcf, species)
    else:
        print("## All genomes in taxon_tree are in taxon_db")          
    
__main__()    