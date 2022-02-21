# CoolScraper
# Ultimate Media's CoolStuff
# 
# Copyright (c) Ultimate Media
# Released under the MIT License
# https://ultimatemedia.js.org/legal/mit-license

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from pysondb import db
import requests, time, math, numpy, config

def main():
    print("CoolScraper by CoolSearch\n")
    
    print(" Start Config ".center(40, "="))
    for setting in dir(config):
        if not setting.startswith("__"):
            print(f"{setting}:", getattr(config, setting, None))
    print(" End Config ".center(40, "="))

    time.sleep(2)
    
    print("\nBeginning indexing...")

    # init db
    data = db.getDb(config.DATA_FILE)

    # establish initial url
    initialUrl = config.INITIAL_URL
    urls = numpy.array([initialUrl])

    # concat url pool
    try:
        pool = open(config.POOL_FILE, "rb")
        urls = numpy.concatenate((urls, numpy.load(pool)))
        pool.close()
    except:
        print("[Warn] Couldn't load url pool. Scraper may break if sites have been indexed.")
    
    i = 0
    goupto = config.INDEX_SIZE # this value can increase when pages are skipped
    
    while i < goupto:
        to_visit = urls[i]

        
        print(f"[{str(math.floor((i / goupto) * 100))}%] Visiting URL: {to_visit}.")
        
        v = visit(to_visit)

        if v["data"]["url"] != to_visit:
            print(f"[Info] Redirect {to_visit} -> {v['data']['url']}")

        if len(data.getByQuery({"url": v["data"]["url"]})) > 0:
            i += 1
            goupto += 1
            print(f"[Info] Skipped: {v['data']['url']} (Already visited).")
            continue
            
        if v["data"]["error"] != None:
            i += 1
            goupto += 1
            print(f"[Info] Skipped: {to_visit} ({v['data']['error']}).")
            data.add(v["data"])
            continue
        
        urls = numpy.concatenate((urls, numpy.array(v["urls"])))
        data.add(v["data"])

        i += 1

    # write pool
    pool = open(config.POOL_FILE, "wb")
    numpy.save(pool, numpy.unique(urls))
    pool.close()
    
    print("[100%] Done!")

def visit(url):
    urls = [url]

    try:
        robot = RobotFileParser()
        robot.set_url(urlparse(url)._replace(path="/robots.txt", query="", fragment="").geturl())
        robot.read()
        if not robot.can_fetch(config.USER_AGENT, url):
            return {
                "data": {
                    "url": url,
                    "title": None,
                    "dateRecorded": time.time(),
                    "error": "Disallowed by robots.txt"
                },
                "urls": []
            }
    except:
        print("[Warn] Error parsing robots.txt")
    
    try:
        req = requests.get(
            url,
            headers={
                "user-agent": config.USER_AGENT
            }
        )
    except:
        return {
            "data": {
                "url": url,
                "title": None,
                "dateRecorded": time.time(),
                "error": "Request failed"
            },
            "urls": []
        }

    if req.status_code >= 400:
        return {
            "data": {
                "url": url,
                "title": None,
                "dateRecorded": time.time(),
                "error": str(req.status_code)
            },
            "urls": []
        }

    soup = BeautifulSoup(req.text, "html.parser")
    
    for link in soup.find_all("a"):
        href = link.get("href") or ""
        if href.startswith("https://") or href.startswith("http://"):
            urls.append(href)
        elif href.startswith("//"):
            urls.append(f"http:{href}")
        elif href.startswith("/"):
            path = urlparse(href)
            urls.append(urlparse(url)._replace(path=path.path, query=path.query, fragment=path.fragment).geturl())
            
    return {
        "data": {
            "url": req.url,
            "title": (soup.title.string if soup.title else "No Title") or "No Title",
            "dateRecorded": time.time(),
            "error": None
        },
        "urls": urls
    }

if __name__ == "__main__":
    main()