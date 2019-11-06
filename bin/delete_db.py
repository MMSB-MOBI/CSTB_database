import pycouch.wrapper as couchDB
import argparse
import re
import requests

SESSION = requests.session()
SESSION.trust_env = False

def args_gestion():
    parser = argparse.ArgumentParser(description = "Delete couchDB database")
    parser.add_argument("--db", metavar="<str>", help = "Delete database(s) corresponding to this regular expression", required = True)
    parser.add_argument("--url", metavar="<str>", help = "couchDB endpoint", required = True)
    return parser.parse_args()

if __name__ == '__main__':
    ARGS = args_gestion()
    couchDB.setServerUrl(ARGS.url)
    couchDB.couchPing()

    db_names = [db_name for db_name in couchDB.couchGetRequest("_all_dbs") if not db_name.startswith("_")]
    regExp = re.compile("^" + ARGS.db + "$")
    db_names = [db_name for db_name in db_names if regExp.match(db_name)]

    if not db_names:
        print("No database to delete")
        exit()

    print("== Databases to delete:")
    for db_name in db_names:
        print(db_name)

    confirm = input("Do you want to delete this databases ? (y/n) ")
    while (confirm != "y" and confirm != "n"):
        confirm = input("I need y or n answer : ") 

    if confirm == "n":
        exit()   

    for db in db_names: 
        print("Delete " + db + "...")
        res = SESSION.delete(ARGS.url + "/" + db)
        print(res.text)
       