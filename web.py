
import datetime
import json
import random
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

#Background service modules
import services

print("Nyon Stream Web Server")


# Our WebSocket Server protocol
class socks(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connect",request.peer)

    def onMessage(self, payload, isBinary):
        self.sendMessage(payload, isBinary)
        payload = json.loads(payload.decode("utf-8"))        
        #print(payload)

        if payload["message"] == "started":
            services.player(uid=payload["uid"],magnet = payload["magnet"],configs=configs,webplayer_args=webplayer_args)
        
        if payload["message"] == "keepalive":
            print(services.active[payload["uid"]].keys(),[i.name for i in threading.enumerate()],f'scrape-{payload["uid"]}',sep="\n")

            if  services.active[payload["uid"]]["scraped"] == "Not Started":
                print("Not scraped or scraping not completed")
                threading.Thread(name=f'scrape-{payload["uid"]}', target=services.scrape,args=(payload,)).start()
                self.sendMessage(json.dumps({"message":"Not Ready","uid":payload["uid"]}).encode(),isBinary)

                if "nyaaid" in payload.keys():
                    threading.Thread(name=f'subs-{payload["uid"]}',target=services.ready_subs,args=(payload,)).start()
                    services.active[payload["uid"]]["subtitles"] = "running"

                services.active[payload["uid"]]["scraped"] = "running"

            elif services.active[payload["uid"]]["scraped"] == "running" or services.active[payload["uid"]]["subtitles"] == "running":
                print("scraping/Subs not completed")

            else:
                print("Scrape completed")    
                message = ["ready",services.active[payload["uid"]]["addr"],services.active[payload["uid"]]["port"],services.active[payload["uid"]]["subtitles"]]    
                print(message)    
                self.sendMessage(json.dumps({"message":message[0],"uid":payload["uid"],
                                "addr":message[1],"port":message[2],"subtitles":message[3]}).encode(),isBinary)
                print("Changing Keepalive")
                services.keepalivehistory[payload["uid"]] = datetime.datetime.now()

    def onClose(self, wasClean, code, reason):
        print(code,reason)
        if "kill" not in [i.name for i in threading.enumerate()]:
            threading.Thread(name="kill",target=services.keepalivecheck).start()


class statsocks(WebSocketServerProtocol):
    def onConnect(self, request):
        print("Client connect",request.peer)
    
    
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
        torrents = services.nyaa.getTorrents(request_query.replace(" ","+"))
        if len(torrents)>0:
            return jsonify({"message":"success","magnets":torrents})
        return jsonify({"message":"error","magnets":"No Results"})

@app.route("/player")
def player_page():
    uid = uuid.uuid4()
    resp = make_response(render_template("player.html"))
    resp.set_cookie("uid",str(uid))
    services.active[str(uid)] = None
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
    print(uid)
    if uid in services.active.keys():
        a = services.active[uid]
        return json.dumps({"port":a["port"],"magnet":a["magnet"],"scraped":a["scraped"],"subtitles":a["subtitles"]})

    else:
        return json.dumps({"Message":"Not Found"})

if __name__ == "__main__":

    with open("config.json","r") as configfile:
        configs = json.load(configfile)

    webplayer_args = configs['webtorrent-arguments']

    if os.name == "posix":
        configs = configs["linux"]
    else:
        configs = configs["windows"]
    
    print("Current Config :",configs)

    

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
