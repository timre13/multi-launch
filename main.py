#!/usr/bin/env python3

import subprocess as sp
import os
import bs4
import json
import tkinter as tk
from tkinter import ttk

"""
    Universal (both Master and Server lookup):

    xml= [1/0] [default: 0] output as QStat's XML instead of pure HTML.  Note: colored names will still be updated
                to HTML codes unless nocolors is defined.  (Note: many variables below do not apply to xml output.)
    xmlcarets= [1/0] [default: 0] output carets instead of converted fonts when using xml=1
    json= [1/0] [default: 0] output as QStat's JSON instead of pure HTML.  Note: colored names will still be updated
                to HTML codes unless nocolors is defined.  (Note: many variables below do not apply to json output.)
    jsoncarets= [1/0] [default: 0] output carets instead of converted fonts when using json=1
    nocolors= [1/0] [default: 0] don't display HTML colors, hide carrets
    hidehtmltags= [1/0] [default: 0] don't display <html>/<head>/<body> tags
    utf8= [1/0] [default: 1] display names with UTF8 instead of ASCII.


    Master Server lookups:

    master= master server address [defaut: dpmaster.deathmask.net]
    game= game to look up (transfusion, xonotic, nexuiz, openarena, warsow, warfork, quake, urbanterror, tremulous, steelstorm, wolfet, q3rally)
    showping= [1/0] [default 0] hidden feature, show pings relative to Atlanta, GA, USA
    sort= [ping,address,players,pass,map,gametype,name,no] [default: players], ping is local to Atlanta, GA, USA,
                no = natural order (oldest first), pass & gametype only if the game supports it.

    showall= show unresponsive servers [1/0] [default: 0]
    hide= [full, empty, both] [default: N/A] hide full or empty servers (both hides full and empty)
    hidegames= [1/0] [default: 0] hide link to gametype lookup (top of screen)
    showonlylist= [1/0] [default: 0] show only the server list
    showplayers= [1/0] [default: 0] show players on listing
    oldprotocol= [#] [default: N/A] use previous protcol version (this is for games with changing protocols and must be
                manually setup on the webserver [leave blank/don't use for current protocol])
    hidepassworded= [1/0] [default: 0] hide servers requiring a password
    hideheader= [1/0] [default: 0] hide the opening section with game logo, master info
    hideinstagib= [1/0] [default: 0] hide instagib servers, only works with select games.


    Single Server lookups:

    game=game to look up (transfusion, xonotic, nexuiz, openarena, warsow, warfork, quake, urbanterror, tremulous, steelstorm, wolfet, q3rally)
    server= query a server rather than a master server [server address in form of ip:port or hostname:port , requires game]
    hidegames= [1/0] [default 0] hide link to gametype lookup
        *players are automatically sorted by frags, I don't feel this should need to be changed, but could be if really needed.
    hideheader= [1/0] [default: 0] - hide the opening section with map picture and general info
    hideplayers= [1/0] [default: 0] - hides players
    hiderules= [1/0] [default: 0] - hides the server rules
    showonlylist= [1/0] [default: 0] show only the server information line

    *showonlylist will be the easiest way to just get a raw listing
"""

GAME = "openarena"
SORT_VALUES = ("no", "ping", "address", "players", "pass", "map", "gametype", "name")

def getServerListJson(game: str, sortBy: str):
    assert(sortBy in SORT_VALUES)
    # Note: Don't use urrlib, it's slow
    return sp.run(
        ["curl", "https://dpmaster.deathmask.net/?game={}&json=1&nocolors=1&showping=1&sort={}".format(game, sortBy), "-s"],
        stdout=sp.PIPE,
        stderr=sp.PIPE).stdout.decode().strip()

def getValueByKey(dictionary: dict, key: str):
    result = dictionary
    for segment in key.split("/"):
        result = result[segment]
    return result

class Main:
    def __init__(self):
        self.root = tk.Tk()

        self.serverListWidgetHeadings = ["Ping", "Game Type", "Map", "Human Players", "All Players", "Player Limit", "Address"]
        self.serverListWidgetKeys = ["ping", "gametype", "map", "rules/g_humanplayers", "numplayers", "maxplayers", "address"]
        self.serverListWidget = ttk.Treeview(self.root, columns=self.serverListWidgetHeadings, height=50)
        self.serverListWidget.heading("#0", text="Name")
        for heading in self.serverListWidgetHeadings:
            self.serverListWidget.heading(heading, text=heading)
        self.serverListWidget.pack(side=tk.TOP, fill=tk.X)

        statusBar = ttk.Label(self.root, relief=tk.RIDGE, anchor=tk.W)
        statusBar.pack(side=tk.BOTTOM, fill=tk.X)

        statusBar["text"] = "Querying..."
        self.root.update()
        serverListJson = getServerListJson(GAME, "no")

        statusBar["text"] = "Parsing response..."
        parsedJson = json.loads(serverListJson)
        self.root.update()

        masterJson = parsedJson[0]
        serverJson = parsedJson[1:]
        for item in serverJson:
            item["name"] = item["name"].strip()
        serverJson = sorted(serverJson, key=lambda item: getValueByKey(item, "rules/g_humanplayers"), reverse=True)

        statusBar["text"] = "Displaying..."
        self.root.update()

        for i, server in enumerate(serverJson):
            self.serverListWidget.insert(
                "",
                i,
                text=server["name"],
                values=[getValueByKey(server, key) for key in self.serverListWidgetKeys],
                tags=[
                    "even" if i % 2 == 0 else "odd",
                    "full" if server["numplayers"] == server["maxplayers"] else "",
                    "empty" if getValueByKey(server, "rules/g_humanplayers") == "0" else "notempty"
                ]
            )
            self.serverListWidget.update()
        self.serverListWidget.tag_configure("even", background="#dddddd")
        self.serverListWidget.tag_configure("odd", background="#eeeeee")
        self.serverListWidget.tag_configure("full", foreground="orange")
        self.serverListWidget.tag_configure("empty", foreground="gray")
        self.serverListWidget.tag_configure("notempty", foreground="blue")

        statusBar["text"] = "Found " + str(masterJson["servers"]) + " servers, " + str(len(serverJson)) + " responsive."

        self.serverListWidget.bind("<Double-Button-1>", self.onServerListItemDoubleclicked)

        self.root.mainloop()

    def onServerListItemDoubleclicked(self, event):
        serverIp = self.serverListWidget.item(self.serverListWidget.identify_row(event.y))["values"][self.serverListWidgetKeys.index("address")]
        sp.Popen(["openarena", "+connect", str(serverIp)])

if __name__ == "__main__":
    main = Main()

