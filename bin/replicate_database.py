import pycouch.wrapper as couchDB
import argparse
import re
import sys
import time
import copy
import sys 
import os
import requests
import json
sys.path.append("/home/chilpert/Dev/CSTB_database/lib")
import watch as watch

SESSION = requests.session()
SESSION.trust_env = False
FAILED = []

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def args_gestion():
    parser = argparse.ArgumentParser(description = "Replicate couchDB database")
    parser.add_argument("--db", metavar="<str>", help = "Replicate database(s) corresponding to this regular expression")
    parser.add_argument("--all", help = "Replicate all databases in couchDB", action="store_true")
    parser.add_argument("--url", metavar="<str>", help = "couchDB endpoint", required = True)
    parser.add_argument("--bulk", metavar="<int>", help = "Number of replication to launch simultanously (default: 2)", default=2)

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

def create_bulks(db_names, bulk_size):
    bulks = [db_names[x:x+bulk_size] for x in range(0, len(db_names), bulk_size)]
    return bulks

def delete_replication_doc(*repIDs):
    global ARGS
    for rep in repIDs:
        doc_url = ARGS.url + "/_replicator/" + rep
        rev_id = json.loads(SESSION.get(doc_url).text)["_rev"]
        print("Delete " + rep + " replication document...")
        res = SESSION.delete(doc_url + "?rev=" + rev_id)
        print(res.text)

def delete_databases(repIDs):
    for rep in repIDs:
        target = rep.lstrip("rep_")
        print("Delete failed " + target + "...")
        print(ARGS.url + "/" + target)
        res = SESSION.delete(ARGS.url + "/" + target)
        print(res.text)

def replication(databases):
    global FAILED
    print("I replicate", databases)    
    to_insert = get_replicate_doc(databases, ARGS.url)
    couchDB.bulkDocAdd(iterable = to_insert, target = "_replicator")

    repIDs = [rep_name for rep_name in to_insert]

    print("I start monitor")
    watch_status = watch.launch(*repIDs)

    if watch_status == "Done":
        print("I finish replicate", databases)

    elif watch_status == "Fail":
        print("I fail replicate", databases) 
        delete_replication_doc(*repIDs)  
        FAILED += repIDs

if __name__ == '__main__':
    global ARGS
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

    bulks = create_bulks(db_names, ARGS.bulk)

    watch.setServerURL(ARGS.url)
    
    nb_bulk = 0
    for bulk in bulks:
        nb_bulk += 1
        watch.setLogStatus("replicate_bulk" + str(nb_bulk)+ "_status.log")
        watch.setLogRunning("replicate_bulk" + str(nb_bulk)+ "_running.log")
        replication(bulk)

    if FAILED:
        print("== Failed", FAILED)
        print("Don't forget to delete newly created failed databases")
    else:
        print("== All databases successfully replicated")

    exit()    
    
    print("== Launch replication")
    to_insert = get_replicate_doc(db_names, ARGS.url)
    couchDB.bulkDocAdd(iterable = to_insert, target = "_replicator")

    #print("== Monitor replication")
    #repIDs = [rep_name for rep_name in to_insert]
    #watch.setServerURL(ARGS.url)
    #if (ARGS.db):
    #    watch.setLogStatus(ARGS.db + "_status.log")
    #    watch.setLogRunning(ARGS.db + "_running.log")
    #watch.launch(*repIDs)

    
        
        

