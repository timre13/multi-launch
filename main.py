import subprocess as sp
import os
import bs4
import json
import tkinter as tk
from tkinter import ttk

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

        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.refreshButtonImage = tk.PhotoImage(file="./img/refresh.png").zoom(2, 2)
        self.refreshButton = ttk.Button(self.toolbar, command=self.refreshServerList, image=self.refreshButtonImage)
        self.refreshButton.pack(side=tk.LEFT)
        self.refreshButton.bind("<Enter>", self.onRefreshButtonHovered)
        self.refreshButton.bind("<Leave>", self.onRefreshButtonLeft)

        self.serverListWidgetHeadings = ["Ping", "Game Type", "Map", "Human Players", "All Players", "Player Limit", "Address"]
        self.serverListWidgetKeys = ["ping", "gametype", "map", "rules/g_humanplayers", "numplayers", "maxplayers", "address"]
        self.serverListWidget = ttk.Treeview(self.root, columns=self.serverListWidgetHeadings, height=50)
        self.serverListWidget.heading("#0", text="Name")
        for heading in self.serverListWidgetHeadings:
            self.serverListWidget.heading(heading, text=heading)
        self.serverListWidget.pack(side=tk.TOP, fill=tk.X)

        self.statusBar = ttk.Label(self.root, relief=tk.RIDGE, anchor=tk.W)
        self.statusBar.pack(side=tk.BOTTOM, fill=tk.X)

        self.refreshServerList()

        self.serverListWidget.bind("<Double-Button-1>", self.onServerListItemDoubleclicked)
        self.root.mainloop()

    def refreshServerList(self):
        self.statusBar["text"] = "Querying..."
        self.root.update()
        serverListJson = getServerListJson(GAME, "no")

        self.statusBar["text"] = "Parsing response..."
        parsedJson = json.loads(serverListJson)
        self.root.update()

        masterJson = parsedJson[0]
        serverJson = parsedJson[1:]
        for item in serverJson:
            item["name"] = item["name"].strip()
        serverJson = sorted(serverJson, key=lambda item: getValueByKey(item, "rules/g_humanplayers"), reverse=True)

        self.statusBar["text"] = "Displaying..."
        self.root.update()

        self.serverListWidget.delete(*self.serverListWidget.get_children()) # Clear the widget
        self.serverListWidget.update()
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

        self.statusBar["text"] = "Found " + str(masterJson["servers"]) + " servers, " + str(len(serverJson)) + " responsive."

    def onRefreshButtonHovered(self, _): self.statusBar["text"] = "Refresh server list."
    def onRefreshButtonLeft(self, _): self.statusBar["text"] = ""

    def onServerListItemDoubleclicked(self, event):
        serverIp = self.serverListWidget.item(self.serverListWidget.identify_row(event.y))["values"][self.serverListWidgetKeys.index("address")]
        sp.Popen(["openarena", "+connect", str(serverIp)])

if __name__ == "__main__":
    main = Main()

