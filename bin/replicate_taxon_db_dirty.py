from __future__ import print_function
import requests
import argparse
import pycouch.wrapper as couchDB
import json
import asyncio
import sys

SESSION = requests.session()
SESSION.trust_env = False

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def args_gestion():
    parser = argparse.ArgumentParser(description="Replicate database dirty way. Download all docs and reinject in new database")
    parser.add_argument("--source", help="source database", required = True)
    parser.add_argument("--target", help="target database", required = True)
    args = parser.parse_args()
    return args

def get_doc_ids(database):
    r = SESSION.get(database + "/_all_docs")
    doc = json.loads(r.text)
    if "error" in doc:
        raise Exception(database, doc)

    ids = [row["id"] for row in doc["rows"]]
    return ids

def write_doc(target, doc):
    r = json.loads(SESSION.post(target, json = doc).text)
    if "error" in r:
        raise Exception(r)

async def copy_docs(source, target, doc_id):
    try:
        # Get documents
        r = SESSION.get(source + "/" + doc_id)
        doc = json.loads(r.text)
        if "error" in doc:
            eprint(doc_id, doc)
            return doc_id, "get_error"
        doc = {k: v for k,v in doc.items() if k != "_rev"}
    except Exception as e:
        eprint(doc_id, ": error in get doc from source :", e)
        return doc_id, "get_error"

    try:
        write_doc(target, doc)  
    except Exception as e:
        eprint(doc_id, ": error in write doc to target :", e)
        return doc_id, "write_error"

    return doc_id, "done"    

async def main_get_docs(source, target, ids):
    status = await asyncio.gather(*[ copy_docs(source, target, i) for i in ids ])
    print("== Final states")
    for stat in status: 
        print(stat[0], stat[1])

def check_database(database):
    r = json.loads(SESSION.get(database).text)
    if "error" in r:
        raise Exception(database, r)

def create_database(database):
    r = json.loads(SESSION.put(database).text)
    if "error" in r:
        raise Exception("Create error " + database, r)

def check_target(target):
    r = json.loads(SESSION.get(target).text)
    if "error" in r :
        if r["error"] == "not_found":
            print(target, "doesn't exist.")
            print("Create", target)
            create_database(target)
        else:
            raise Exception(database, r)    
                    

if __name__ == "__main__":
    
    ARGS = args_gestion()

    print("COMMAND :", " ".join(sys.argv))

    print("CHECK DATABASES")
    check_database(ARGS.source)
    check_target(ARGS.target)
    
    print("SEARCH AND CREATE")
    source_ids = get_doc_ids(ARGS.source)
    asyncio.run(main_get_docs(ARGS.source, ARGS.target, source_ids))




