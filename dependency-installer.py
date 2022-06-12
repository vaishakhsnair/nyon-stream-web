#this script will install all the required dependencies in a folder inside the current active directory (FOR WINDOWS ONLY)
import os
import subprocess
import sys
import shutil

dependecies_folder = "dependencies"

if not os.path.isdir(dependecies_folder):
    os.mkdir(dependecies_folder)
    os.mkdir(os.path.join(dependecies_folder,"npm"))


def pythondependencies():
    dependency_list = ["requests","bs4","uuid","autobahn","werkzeug","flask","twisted","tqdm","py7zr"]
    for i in dependency_list:
        try:
            __import__(i)  #to check if package is installed
            print(i," is already installed")
        except ImportError:
            print("installing :",i)
            reqs = subprocess.check_output([sys.executable, '-m', 'pip', "install",i])  
            print("successfully installed :",i)
            __import__(i)


def node_dependencies(check=True,node_path=None):
    if check:
        if os.name == "nt":
            node_dl_link = "https://nodejs.org/download/release/latest/win-x64/node.exe"
            if "node.exe" not in os.listdir(dependecies_folder):
                downloader(node_dl_link,"node.exe")
            node_path = os.path.join(os.getcwd(),dependecies_folder,"node.exe")

        else:
            print("The Current os is not windows. if you are running linux install node and npm using your package manager and use 'npm i webtorrent-cli -g' to install webtorrent")
            return None
    
    npm_link = "https://nodejs.org/dist/npm/npm-1.4.9.zip"
    downloader(npm_link, "npm.zip")
    extractor(os.path.join(dependecies_folder,"npm.zip"),os.path.join(dependecies_folder,"npm"))
    npm_path = os.path.join(os.getcwd(),dependecies_folder,"npm","node_modules","npm","bin","npm-cli.js") 



    webtorrent_latest_tag_zipball = requests.get("https://api.github.com/repos/webtorrent/webtorrent-cli/releases/latest").json()["zipball_url"]
    print(webtorrent_latest_tag_zipball)

    if "webtorrent-cli" not in os.listdir(dependecies_folder):

        downloader(webtorrent_latest_tag_zipball, "webtorrent-cli.zip",progress=False)
        extractor(os.path.join(dependecies_folder,"webtorrent-cli.zip"), dependecies_folder)

        for i in os.listdir(dependecies_folder):
            if "webtorrent-cli" in i:
                print(i)
                os.rename(os.path.join(dependecies_folder,i),os.path.join(dependecies_folder,"webtorrent-cli")) #renaming for consistency

    webtorrent_path = os.path.join(dependecies_folder,"webtorrent-cli")



    #adding both npm and node to path temporarily and moving to webtorrent-cli folder to install req components
    #print("Command :",f"SET PATH={npm_path}\;%PATH% && SET PATH={node_path}\;%PATH% && cd {webtorrent_path} && npm i --save")
    print("Installing Webtorrent-Cli")
    os.system(f"SET PATH={npm_path}\;%PATH% && SET PATH={node_path}\;%PATH% && cd {webtorrent_path} && npm i --save") 


        
def extractor(src,dest):
    with ZipFile(src,"r") as file:
        file.extractall(dest)
    os.remove(src)

def downloader(link,filename,progress=True):
    if link is not None:
        print("Downloading Object from :",link)
        req_dl = requests.get(link,stream=True)
        if progress:
            total_length = int(req_dl.headers.get("Content-Length"))
            with tqdm.wrapattr(req_dl.raw, "read", total=total_length, desc="") as raw:
                with open(os.path.join(dependecies_folder,filename),"wb") as file:
                    shutil.copyfileobj(raw, file)
        else:
            with open(os.path.join(dependecies_folder,filename),"wb") as file:
                for chunk in req_dl.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
                



if __name__ == "__main__":
    pythondependencies()
    import requests
    from zipfile import ZipFile
    from tqdm.auto import tqdm

    args = sys.argv
    if '--nocheck' and '--node' in args:
        node_dependencies()(check=False,node_path=args[args.index('--node')+1])
    else:
        node_dependencies()
