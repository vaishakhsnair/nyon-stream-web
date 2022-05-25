

import json
import subprocess
import datetime
import time
import random
import requests
from bs4 import BeautifulSoup as bs


#External Plugins
import plugins.nyaa.nyaascraper as nyaa
import plugins.animetosho.animetoshoapi as tosho



active = {}             #keeping track of active user's services
keepalivehistory = {}   #keeping track of active online users


def scrape(payload):
    global active,keepalivehistory
    uid = payload["uid"]
    if "addr" not in active[uid].keys():
        try:
            port = active[uid]["port"]
        except KeyError:
            return ["Waiting","Null","Null"]
        time.sleep(3)
        resp = None
        while resp==None:
            try:
                resp = requests.get(f"http://localhost:{port}")
            except:
                pass

            if uid not in active.keys():     
                print("UID Not Found Cancelling scrape")     #avoid zombie mode if the main process is terminated before this thread
                return None

        soup =  bs(resp.text, 'html.parser')
        li = soup.find_all("a",href=True)
        li = [i["href"] for i in li]
        print(li)
        active[uid]["addr"] = li
        active[uid]["scraped"] = True
        return ["ready",li,port]
    else:   
        return ["ready",active[uid]["addr"],active[uid]["port"]]

def ready_subs(payload):
    global active
    extract_path = tosho.get_subs(int(payload["nyaaid"]))
    if extract_path == -1:
        active[payload["uid"]]["subtitles"] = "Not Available"
    else:
        active[payload["uid"]]["subtitles"]=extract_path
    print(active[payload["uid"]]["subtitles"])

def keepalivecheck():
    global keepalivehistory
    time.sleep(15)
    if keepalivehistory:
        print(keepalivehistory)
        torem = []
        for i in keepalivehistory.keys():
            last_ping = keepalivehistory[i]
            if ((datetime.datetime.now() - last_ping).seconds) > 15:
                print(f"UID : {i} is stale , killing process")
                print(active)
                if i in active.keys():
                    active[i]["process"].kill()
                    del(active[i])
                    torem.append(i)
                else:
                    print("UID Not in active sessions")
        if torem:
            for i in torem:
                del(keepalivehistory[i])
                
def getport():
    while True:
        port = random.randint(8081,9999)
        activeports = [i["port"] if i != None else None for i in active.values()]
        print(activeports)
        if port not in activeports:
            return port
    

def player(uid,magnet,configs,webplayer_args):
    global active
    print(active)
    port = getport()
    print("Port :",port)    
    if active[uid] is None:     
        print("Not Running")   
    else:
        active[uid]["process"].kill()

    #print("Command :",f"{configs['node_path']} {configs['webtorrent_path']} \"{magnet}\" {webplayer_args} -p {port}")
    process = subprocess.Popen(f"{configs['node_path']} {configs['webtorrent_path']} \"{magnet}\" {webplayer_args} -p {port}",shell=True
                                ,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=0)

    active[uid] = {"port":port,"magnet":magnet,"process":process,"scraped":"Not Started","subtitles":"Not Started"}
    print(active[uid])

    #stdout=subprocess.PIPE