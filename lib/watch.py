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
DIC_URL_POS = {}
DIC_COLOR_STATUS = {}
STDSCR = None

# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console

def init_screen(*urlToWatch):
    global STDSCR
    global DIC_COLOR_STATUS
    global DIC_URL_POS
    STDSCR = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, -1, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1)
    curses.init_pair(4, curses.COLOR_GREEN, -1)
    DIC_COLOR_STATUS["default"] = curses.color_pair(1)
    DIC_COLOR_STATUS["error"] = curses.color_pair(2)
    DIC_COLOR_STATUS["completed"] = curses.color_pair(3)
    DIC_COLOR_STATUS["running"] = curses.color_pair(4)
    DIC_COLOR_STATUS["crashing"] = curses.color_pair(2)
    DIC_COLOR_STATUS["failed"] = curses.color_pair(2)

    i = 0
    for url in urlToWatch:
        DIC_URL_POS[url] = i
        STDSCR.addstr(i, 0, url)
        i += 1

def terminate_screen():
    curses.echo()
    curses.nocbreak()
    curses.endwin()

def updateStatusView(url, status):
    STDSCR.addstr(DIC_URL_POS[url], 0, url + ": " + status, DIC_COLOR_STATUS.get(status, DIC_COLOR_STATUS["default"]))
    STDSCR.clrtoeol()
    STDSCR.refresh()

async def watch(filePath, fStatus, fStop) -> str:
    #print("WATCH")
    #print("Watch", filePath)
    r = SESSION.get(filePath)
    #print(r.text)
    doc = json.loads(r.text)
    
    last_md5 = hashlib.md5(r.text.encode()).hexdigest()
    status = fStatus(doc)
    updateStatusView(filePath, status)
    #print(filePath, status)
    if fStop(status):
        return

    i = 0
    while(True):
        r = SESSION.get(filePath)
        new_md5 = hashlib.md5(r.text.encode()).hexdigest()
        if new_md5 != last_md5:
            #print(r.text)
            status = fStatus(json.loads(r.text))
            #updateStatusView(filePath, status)
            #print(filePath, status)
            if fStop(status):
                return
            last_md5 = new_md5
        await asyncio.sleep(2)  


async def main(fStatus, fStop, *filePath : str) -> None:
    #print("MAIN")
    await asyncio.gather(*[ watch(f, fStatus, fStop) for f in filePath ])

def launch(fStatus, fStop, *urlToWatch):
    init_screen(*urlToWatch)
    try: 
        asyncio.run(main(fStatus, fStop, *urlToWatch))
    finally:
        terminate_screen()

    print("DONE")
#    fileToWatch = sys.argv[1:]
#    asyncio.run(main(*fileToWatch))