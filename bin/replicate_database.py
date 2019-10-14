import pycouch.wrapper as couchDB
import argparse
import re
import sys
import time
import copy
import sys 
sys.path.append("/Users/chilpert/Dev/CSTB_database/lib")
import watch as watch

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def args_gestion():
    parser = argparse.ArgumentParser(description = "Replicate couchDB database")
    parser.add_argument("--db", metavar="<str>", help = "Replicate database(s) corresponding to this regular expression")
    parser.add_argument("--all", help = "Replicate all databases in couchDB", action="store_true")
    parser.add_argument("--url", metavar="<str>", help = "couchDB endpoint", required = True)

    args = parser.parse_args()
    if args.db and args.all:
        print("You have to choose between --db or --all")
        exit()
    if not args.db and not args.all:
        print("You have to give --all or --db argument")
        exit()
    args.url = args.url.rstrip("/")
    return args    

def get_database_names():
    db_names = [db_name for db_name in couchDB.couchGetRequest("_all_dbs") if not db_name.startswith("_")]
    return db_names

def get_replicate_doc(db_names, url):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    docs = {}
    for name in db_names:
        target = name + "-bak" + timestamp
        rep_id = "rep_" + target
        docs[rep_id] = {"source": url + "/" + name, "target" : url + "/" + target, "create_target": True, "continuous": False}
    return docs

def get_regexp(input_str):
    regexp = "^" + input_str.replace("*", ".*") + "$"
    return re.compile(regexp)

def monitor_replication(insert_ids, sleep_time = 5):
    completed_ids = set()
    running_ids = copy.deepcopy(insert_ids)
    while set(insert_ids) != completed_ids:
        print("Check status...")
        get_results = couchDB.bulkRequestByKey(running_ids, "_replicator")["results"]
        for rows in get_results:
            doc = rows["docs"][0]["ok"]
            if doc.get("_replication_state") == "completed":
                completed_ids.add(doc["_id"])
                running_ids.remove(doc["_id"])
                print(doc["_id"], "replication job is complete.")
        time.sleep(2)    

if __name__ == '__main__':
    ARGS = args_gestion()
    couchDB.setServerUrl(ARGS.url)
    couchDB.couchPing()
    db_names = get_database_names()
    if ARGS.db:
        regExp = get_regexp(ARGS.db)
        db_names = [db_name for db_name in db_names if regExp.match(db_name)]

    if not db_names:
        print("No database to replicate")
        exit()
    
    print("== Databases to replicate:")
    for db_name in db_names:
        print(db_name)

    confirm = input("Do you want to replicate this databases ? (y/n) ")
    while (confirm != "y" and confirm != "n"):
        confirm = input("I need y or n answer : ") 

    if confirm == "n":
        exit()    
    
    print("== Launch replication")
    to_insert = get_replicate_doc(db_names, ARGS.url)
    couchDB.bulkDocAdd(iterable = to_insert, target = "_replicator")

    print("== Monitor replication")
    repIDs = [rep_name for rep_name in to_insert]
    watch.setServerURL(ARGS.url)
    if (ARGS.db):
        watch.setLogStatus(ARGS.db + "_status.log")
        watch.setLogRunning(ARGS.db + "_running.log")
    watch.launch(*repIDs)

    
        
        

