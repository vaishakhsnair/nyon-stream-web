import requests
import json
import os
import py7zr
import re

subs_path = "subtitles"
temp = "temp_zips"
torrent_info_base = f"https://feed.animetosho.org/json?show=torrent&nyaa_id="
torrent_info_base_2 = f"https://feed.animetosho.org/json?only_tor=1&q="
basedir = "subtitles"
default_lang = "eng"

try:
    os.mkdir(temp)
    os.mkdir(subs_path)
except:
    pass

def subsdl(nyaa_id):
    req = requests.get(torrent_info_base+str(nyaa_id))
    req_json = json.loads(req.content)
    print(req_json)
    if "error" not in req_json.keys():
        title = req_json["title"]
        torrent_name = req_json["torrent_name"]
        primary_file_id = req_json["primary_file_id"]

        if primary_file_id is None:
            req_link = (torrent_info_base_2 + title)
            print(req_link.replace('"',''))
            req = requests.get(req_link.replace('"',''))
            req_second_json = json.loads(req.content)

            print(len(req_second_json))
            for i in req_second_json:
                temp_title = i["title"]
                if temp_title==title:
                    if i["status"] == "skipped":
                        return -1

                    tosho_main_id = i["id"]
                    break
            try :
                
                attachment_link = f"https://animetosho.org/storage/torattachpk/{tosho_main_id}/{title.rstrip('.mkv')}_attachments.7z"
            except ReferenceError:
                return -1
        else:
            attachment_link = f"https://animetosho.org/storage/attachpk/{primary_file_id}/{title.rstrip('.mkv')}_attachments.7z"
            
        return download(attachment_link,nyaa_id)
    else:
        return -1

def download(attachment_link,nyaa_id):
    req_dl = requests.get(attachment_link,stream=True)
    dl_path = os.path.join(temp,f"{nyaa_id}_attachments.7z")
    with open(dl_path,"wb") as file:
        for chunk in req_dl.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)

        return dl_path



def unzip(src,nyaa_id,dest=subs_path):
    print(src,nyaa_id)
    if src == -1:
        return -1
    if os.path.isdir(f"{dest}/{nyaa_id}") and os.path.isfile(f"{dest}/{nyaa_id}/filemap.json"):
        print(f"filemap for the id {nyaa_id} already exists,using it..")
        with open(f"{dest}/{nyaa_id}/filemap.json") as jsonfile:
            filemap = json.load(jsonfile)
        return (f"{dest}/{nyaa_id}",filemap)


    with py7zr.SevenZipFile(src) as f:
        a = [i for i in f.getnames() if "track" and default_lang in i]
        h = {}
        for i in a:
            n = i.split("/")
            if len(n) > 1:
                if n[0] not in h.keys():
                    h[n[0]] = {}
                if len(n) == 3:
                    if n[1] not in h[n[0]].keys():
                        h[n[0]][n[1]] = n[2]
                else:
                    h[n[0]] = n[1]
            else:
                h[str(nyaa_id)] = i   
    
        f.extractall(f"{dest}/{nyaa_id}") 

    with open(f"{dest}/{nyaa_id}/filemap.json","a+") as jsonfile:
        print(f"Creating filemap for the id {nyaa_id}")
        json.dump(h,jsonfile)

          
    return (f"{dest}/{nyaa_id}",h)

def get_subs(nyaa_id):
    return unzip(subsdl(nyaa_id),nyaa_id)