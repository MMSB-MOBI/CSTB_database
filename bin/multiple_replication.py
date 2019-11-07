import argparse
import pycouch.wrapper as couchDB
import time

def args_gestion():
    parser = argparse.ArgumentParser(description = "Replicate one database multiple times.")
    parser.add_argument("--db", metavar="<str>", help = "Database to replicate", required = True)
    parser.add_argument("--url", metavar="<str>", help = "couchDB endpoint", required = True)
    parser.add_argument("-n", metavar="<int>", help = "Number of replications", default=1)

    args = parser.parse_args()
    args.url = args.url.rstrip("/")
    args.n = int(args.n)
    return args

def get_replicate_doc(db_name, url, nb):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    docs = {}
    target = db_name + "-bak" + timestamp + "-" + str(nb)
    return {"source": url + "/" + db_name, "target" : url + "/" + target, "create_target": True, "continuous": False}

if __name__ == '__main__':
    ARGS = args_gestion()
    couchDB.setServerUrl(ARGS.url)
    couchDB.couchPing()

    print("== Databases to replicate: " + ARGS.db)

    confirm = input("Do you want to replicate this database ? (y/n) ")
    while (confirm != "y" and confirm != "n"):
        confirm = input("I need y or n answer : ") 

    if confirm == "n":
        exit()


    print("== Launch replication")
    for i in range(ARGS.n): 
        to_insert = get_replicate_doc(ARGS.db, ARGS.url, i)
        couchDB.bulkDocAdd(iterable = to_insert, target = "_replicator")