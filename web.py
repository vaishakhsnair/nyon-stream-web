
import datetime
import json
import random
import subprocess
import sys
import threading
import time
import uuid
import os

import requests
from autobahn.twisted.resource import WebSocketResource, WSGIRootResource
from autobahn.twisted.websocket import (WebSocketServerFactory,
                                        WebSocketServerProtocol)
from werkzeug.security import safe_join


from bs4 import BeautifulSoup as bs
from flask import Flask, jsonify, make_response, render_template, request ,send_from_directory,send_file
from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource

import nyaa.nyaascraper as nyaa
import animetosho.animetoshoapi as tosho

print("Nyon Stream Web Server")
nyaa.node_path = os.path.join("dependencies","node.exe")
nyaa.webtorrent_path = os.path.join("dependencies","webtorrent-cli","bin","cmd.js")

webplayer_args = "--playlist --keep-seeding -o torrents/"

if os.name=="posix":
    nyaa.node_path = ""
    nyaa.webtorrent_path = r"webtorrent"

active = {}
keepalivehistory = {}
# Our WebSocket Server protocol
class socks(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connect",request.peer)

    def onMessage(self, payload, isBinary):
        self.sendMessage(payload, isBinary)
        payload = json.loads(payload.decode("utf-8"))        
        print(payload)

        if payload["message"] == "started":
            player(uid=payload["uid"],magnet = payload["magnet"])
        
        if payload["message"] == "keepalive":
            print(active[payload["uid"]].keys(),[i.name for i in threading.enumerate()],f'scrape-{payload["uid"]}',sep="\n")

            if  active[payload["uid"]]["scraped"] == "Not Started":
                print("Not scraped or scraping not completed")
                threading.Thread(name=f'scrape-{payload["uid"]}', target=scrape,args=(payload,)).start()
                self.sendMessage(json.dumps({"message":"Not Ready","uid":payload["uid"]}).encode(),isBinary)

                if "nyaaid" in payload.keys():
                    threading.Thread(name=f'subs-{payload["uid"]}',target=ready_subs,args=(payload,)).start()
                    active[payload["uid"]]["subtitles"] = "running"

                active[payload["uid"]]["scraped"] = "running"

            elif active[payload["uid"]]["scraped"] == "running" or active[payload["uid"]]["subtitles"] == "running":
                print("scraping/Subs not completed")

            else:
                print("Scrape completed")    
                message = ["ready",active[payload["uid"]]["addr"],active[payload["uid"]]["port"],active[payload["uid"]]["subtitles"]]    
                print(message)    
                self.sendMessage(json.dumps({"message":message[0],"uid":payload["uid"],
                                "addr":message[1],"port":message[2],"subtitles":message[3]}).encode(),isBinary)
                print("Changing Keepalive")
                keepalivehistory[payload["uid"]] = datetime.datetime.now()

    def onClose(self, wasClean, code, reason):
        print(code,reason)
        if "kill" not in [i.name for i in threading.enumerate()]:
            threading.Thread(name="kill",target=keepalivecheck).start()


class statsocks(WebSocketServerProtocol):
    def onConnect(self, request):
        print("Client connect",request.peer)
    
    



def scrape(payload):
    global active
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

            if uid not in keepalivehistory.keys():          #avoid zombie mode if the main process is terminated before this thread
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
    

def player(uid,magnet):
    global active
    print(active)
    port = getport()
    print("Port :",port)    
    if active[uid] is None:     
        print("Not Running")   
    else:
        active[uid]["process"].kill()

    #print("Command :",f"{nyaa.node_path} {nyaa.webtorrent_path} \"{magnet}\" {webplayer_args} -p {port}")
    process = subprocess.Popen(f"{nyaa.node_path} {nyaa.webtorrent_path} \"{magnet}\" {webplayer_args} -p {port}",shell=True, stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0)
    active[uid] = {"port":port,"magnet":magnet,"process":process,"scraped":"Not Started","subtitles":"Not Started"}
    print(active[uid])
        

# Our WSGI application .. in this case Flask based
app = Flask(__name__)
app.secret_key = str(uuid.uuid4())

#app.config['UPLOAD_FOLDER'] = tosho.subs_folder


@app.route('/',methods=["GET","POST"])
def page_home():

    if request.method == "GET":
        return render_template('search.html')

    if request.method == "POST":

        request_query = request.form["query"]
        torrents = nyaa.getTorrents(request_query.replace(" ","+"))
        if len(torrents)>0:
            return jsonify({"message":"success","magnets":torrents})
        return jsonify({"message":"error","magnets":"No Results"})

@app.route("/player")
def player_page():
    global active
    uid = uuid.uuid4()
    resp = make_response(render_template("player.html"))
    resp.set_cookie("uid",str(uid))
    active[str(uid)] = None
    return resp

@app.route("/sus")
def testsubs():
    return render_template("subpars.html")

@app.route(f"/subs/<path:flpath>")
def returnsubs(flpath):
    safe_path = safe_join("subtitles",flpath)
    if safe_path == "NotFound":
        return "The requested file is not found"
    return send_file(safe_path,as_attachment=True)

@app.route(f"/stats")
def webtorrstats():
    uid = request.cookies.get("uid")
    
if __name__ == "__main__":

    log.startLogging(sys.stdout)

    # create a Twisted Web resource for our WebSocket server
    wsFactory = WebSocketServerFactory("ws://0.0.0.0:8080")
    wsFactory.protocol = socks
    wsResource = WebSocketResource(wsFactory)

    wsFactoryStats = WebSocketServerFactory("ws://0.0.0.0:8070")
    wsFactoryStats.protocol = statsocks
    wsResourceStats = WebSocketResource(wsFactoryStats)

    # create a Twisted Web WSGI resource for our Flask server
    wsgiResource = WSGIResource(reactor, reactor.getThreadPool(), app)

    # create a root resource serving everything via WSGI/Flask, but
    # the path "/ws" served by our WebSocket stuff
    rootResource = WSGIRootResource(wsgiResource, {b'ws': wsResource,b'wstat': wsResourceStats})

    # create a Twisted Web Site and run everything
    site = Site(rootResource)

    reactor.listenTCP(8080, site)
    reactor.run()
