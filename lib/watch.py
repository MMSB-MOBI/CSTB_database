import asyncio
import os
import sys
import pycouch.wrapper as couchDB
import requests
import json
import hashlib 
import curses
import time

SESSION = requests.session()
SESSION.trust_env = False

MONITOR = {}
DEFAULT_END_POINT = "http://localhost:5984"
LOG_STATUS = "./monitor_status.log"
LOG_RUNNING = "./monitor_running.log"

# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console

def initialize_log():
    status = open(LOG_STATUS, "w")
    running = open(LOG_RUNNING, "w")
    status.close()
    running.close()

def writeStatus(to_write):
    with open(LOG_STATUS, "a") as o:
        o.write(to_write)

def writeRunning(to_write):
     with open(LOG_RUNNING, "a") as o:
        o.write(to_write)

def setServerURL(url):
    global DEFAULT_END_POINT
    DEFAULT_END_POINT = url

def setLogStatus(path):
    global LOG_STATUS
    LOG_STATUS = path

def setLogRunning(path):
    global LOG_RUNNING
    LOG_RUNNING = path   

def replicationStatus(doc):
    if "error" in doc: 
        return "error"
    return doc.get("state", "unknown")

def monitorStop(status):
    if status in ["error", "crashing", "failed", "completed"]:
        return True
    return False

async def watch_status(filePath) -> str:
    #print("WATCH")
    global DEFAULT_END_POINT
    global HANDLE_STATUS

    urlToWatch = DEFAULT_END_POINT + "/_scheduler/docs/_replicator/" + filePath
    r = SESSION.get(urlToWatch)

    doc = json.loads(r.text)
    status = replicationStatus(doc)

    to_write = "####" + filePath + " " + time.strftime("%d-%m-%Y/%H:%M:%S") + " " + status + "\n"
    to_write += r.text
    writeStatus(to_write)

    last_md5 = hashlib.md5(r.text.encode()).hexdigest()
    
    if monitorStop(status):
        return

    while(True):
        r = SESSION.get(urlToWatch)
        new_md5 = hashlib.md5(r.text.encode()).hexdigest()
        if new_md5 != last_md5:
            status = replicationStatus(json.loads(r.text))
            to_write = "####" + filePath + " CHANGE " + time.strftime("%d-%m-%Y/%H:%M:%S") + " " + status + "\n"
            to_write += r.text
            writeStatus(to_write)
            if monitorStop(status):
                return
            last_md5 = new_md5
        await asyncio.sleep(2)  

async def watch_advancement(repID, all_docs, target):
    global DEFAULT_END_POINT
    global HANDLE_RUNNING
    doc = json.loads(SESSION.get(target).text)
    
    nb_replicate = str(doc.get("doc_count", 0))
    writeRunning(repID + " " + all_docs + " " + nb_replicate + " (Init)\n")
    last_replicate = nb_replicate

    while(True):
        doc = json.loads(SESSION.get(target).text)
        nb_replicate = str(doc.get("doc_count", 0))
        writeRunning(repID + " " + all_docs + " " + nb_replicate + " (" + last_replicate + ")\n")
        if nb_replicate == all_docs:
            return
        last_replicate = nb_replicate
        await asyncio.sleep(5)


async def get_source_and_target(rep_id):
    dic_ret = {rep_id: {}}
    print("OOOOO")
    print(DEFAULT_END_POINT)
    r = SESSION.get(DEFAULT_END_POINT + "/_replicator/" + rep_id)
    doc = json.loads(r.text)
    if "error" in doc:
        raise Exception(rep_id, doc)
    dic_ret[rep_id]["target"] = doc["target"]
    #dic_ret[rep_id]["source"] = doc["source"]
    doc_source = json.loads(SESSION.get(doc["source"]).text)
    if "error" in doc_source:
        raise Exception(doc["source"], doc_source)
    nb_doc = doc_source["doc_count"]
    dic_ret[rep_id]["source"] = str(nb_doc)
    return dic_ret

async def main(*filePath : str) -> None:
    #print("MAIN")
    ret = await asyncio.gather(*[ get_source_and_target(f) for f in filePath ])
    source_target_dic = {k: v for dic in ret for k, v in dic.items()}
    await asyncio.gather(*[ watch_status(f) for f in filePath ], *[ watch_advancement(f, source_target_dic[f]["source"], source_target_dic[f]["target"]) for f in filePath])


def launch(*repIDs):
    #source_target_dic = asyncio.run(run_source_target(*repIDs))
    initialize_log()
    print("Follow replication states in", LOG_STATUS)
    print("Follow replication advancement in", LOG_RUNNING)
    asyncio.run(main(*repIDs))
    print("DONE")
#    fileToWatch = sys.argv[1:]
#    asyncio.run(main(*fileToWatch))