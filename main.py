# CoolSearch
# Ultimate Media's CoolStuff
# 
# Copyright (c) Ultimate Media
# Released under the MIT License
# https://ultimatemedia.js.org/legal/mit-license

from flask import Flask, render_template, request, redirect
from pysondb import db
import config, time
app = Flask('app')

data = db.getDb(config.DATA_FILE)

def find(query):
    q = query.lower()
    results = []

    for site in data.getAll():
        if site["error"] == None:
            if q in site["title"].lower():
                results.append(site)
            elif q in site["url"].lower():
                results.append(site)
    
    return results

@app.route('/')
def home():
    return render_template("home.html")

@app.route("/cool")
def search():
    timetook = time.time()
    query = request.args.get("search", None)
    results = find(query)
    if query == None:
        return redirect("/")
    timetook = round(time.time() - timetook, 6)
    return render_template("search.html", query=query, results=results, timetook=timetook)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.run(host='0.0.0.0', port=8080)
