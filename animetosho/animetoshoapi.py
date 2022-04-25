import requests
import json
import os
import py7zr
import re

subs_path = "subtitles"
temp = "temp"
torrent_info_base = f"https://feed.animetosho.org/json?show=torrent&nyaa_id="
torrent_info_base_2 = f"https://feed.animetosho.org/json?only_tor=1&q="

#https://animetosho.org/storage/attachpk/{primary_file_id}/{title.rstrip(".mkv")}_attachments.7z

if not os.path.isdir(subs_path):
    os.mkdir(temp)
    os.mkdir(subs_path)

def get_subs(nyaa_id):
    req = requests.get(torrent_info_base+str(nyaa_id))
    req_json = json.loads(req.content)
    #print(req_json)
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

def download(attachment_link,nyaa_id):
    req_dl = requests.get(attachment_link,stream=True)
    dl_path = os.path.join(temp,f"{nyaa_id}_attachments.7z")
    with open(dl_path,"wb") as file:
        for chunk in req_dl.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)

        return dl_path


print(get_subs(1419259))

def unzip(src,dest):
    with py7zr.SevenZipFile(src) as zipfile:
        pass