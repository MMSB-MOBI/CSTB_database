import requests
import json

SESSION = requests.session()
SESSION.trust_env = False

DB = "http://chilpert:Z74G6YtrGd@localhost:1234/taxon_db"
GCF_NAME = "/home/chilpert/Dev/CSTB_database/work/gcf_name.txt"

def get_gcf_name():
    dic = {}
    with open(GCF_NAME) as f:
        for l in f:
            l = l.rstrip().split("\t")
            dic[l[0]] = l[1]

    return dic        

if __name__ == "__main__":
    all_doc = json.loads(SESSION.get(DB + "/_all_docs").text)
    dic_gcf_name = get_gcf_name()
    for r in all_doc["rows"]:
        taxon_doc = json.loads(SESSION.get(DB + "/" + r["id"]).text)
        gcf_list = taxon_doc["GCF"]
        current_gcf = taxon_doc["current"]
        if current_gcf != "None":
            current_name = dic_gcf_name[current_gcf]
        names = [dic_gcf_name[gcf] for gcf in gcf_list if gcf != "None"]
        if names and current_name:
            taxon_doc["names"] = names
            taxon_doc["current_name"] = current_name
            r_post = SESSION.post(DB, json = taxon_doc)
        print(r_post.text)