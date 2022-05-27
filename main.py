import typing
import subprocess as sp
from urllib.request import urlopen, Request
import sys
import json
import time
import tkinter as tk
from tkinter import ttk
from tkinter import font
from PIL import ImageTk, Image
import io

GAME = "openarena"
GAME_EXE_PATH = "openarena"
MASTER_SERVER_REQUEST_TIMEOUT_S = 20
SERVER_REQ_TIMEOUT_S = 20
MAP_IMG_SIZE = 128

"""
    Query the master server to get server list.
    Only provides basic info for each server.
"""
def getServerListJson(game: str) -> str:
    request = Request("https://dpmaster.deathmask.net/?game={}&json=1&nocolors=1&showping=1".format(game))
    try:
        return urlopen(request, timeout=MASTER_SERVER_REQUEST_TIMEOUT_S).read().decode("utf-8")
    except:
        return "ERROR: " + str(sys.exc_info()[1])

"""
    Query a specific server.
    Provides all the possible info of the server.
"""
def getServerInfoJson(game: str, server: str) -> str:
    request = Request("https://dpmaster.deathmask.net/?game={}&json=1&nocolors=1&server={}".format(game, server))
    try:
        return urlopen(request, timeout=SERVER_REQ_TIMEOUT_S).read().decode("utf-8")
    except:
        return "ERROR: " + str(sys.exc_info()[1])

def getMapImg(mapName: str) -> typing.Union[ImageTk.PhotoImage, None]:
    print("Getting:", "http://www.dpmaster.deathmask.net/mapthumbs/{}/{}.jpg".format(GAME, mapName))
    request = Request("http://www.dpmaster.deathmask.net/mapthumbs/{}/{}.jpg".format(GAME, mapName))
    try:
        data = urlopen(request, timeout=MASTER_SERVER_REQUEST_TIMEOUT_S).read()
        img = Image.open(io.BytesIO(data)).resize((MAP_IMG_SIZE, MAP_IMG_SIZE))
        return ImageTk.PhotoImage(image=img)
    except Exception:
        return None

def getPlaceholderMapImg() -> typing.Union[ImageTk.PhotoImage, None]:
    request = Request("https://dpmaster.deathmask.net/game/{}.gif".format(GAME))
    try:
        data = urlopen(request, timeout=MASTER_SERVER_REQUEST_TIMEOUT_S).read()
        img_ = Image.open(io.BytesIO(data))
        img = Image.new(mode=img_.mode, size=(img_.width, img_.width))
        img.paste(img_, box=(0, int(img.height/2-img_.height/2)))
        return ImageTk.PhotoImage(image=img.resize((MAP_IMG_SIZE, MAP_IMG_SIZE)))
    except Exception:
        return None


def getValueByKey(dictionary: dict, key: str):
    result = dictionary
    try:
        for segment in key.split("/"):
            result = result[segment]
    except:
        result = "0"
    return result

class Main:
    def __init__(self):
        self.sortBy = "rules/g_humanplayers"
        self.shouldReverseSorting = True

        self.root = tk.Tk()
        self.root.title("Multi-Launch OpenArena Launcher")

        self.monoFont = font.Font(font="TkFixedFont")
        style = ttk.Style()
        style.configure("Treeview", font=self.monoFont)

        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.refreshButtonImage = tk.PhotoImage(file="./img/refresh.png").zoom(2, 2)
        self.refreshButton = ttk.Button(self.toolbar, command=self.refreshServerList, image=self.refreshButtonImage)
        self.refreshButton.pack(side=tk.LEFT)
        self.refreshButton.bind("<Enter>", self.onRefreshButtonHovered)
        self.refreshButton.bind("<Leave>", self.clearStatusBarText)

        self.separator1 = ttk.Separator(self.toolbar, orient=tk.VERTICAL)
        self.separator1.pack(side=tk.LEFT)

        self.playButtonImage = tk.PhotoImage(file="./img/play.png").zoom(2, 2)
        self.playButton = ttk.Button(self.toolbar, command=self.onServerListItemDoubleclicked, image=self.playButtonImage)
        self.playButton.pack(side=tk.LEFT)
        self.playButton.bind("<Enter>", self.onPlayButtonHovered)
        self.playButton.bind("<Leave>", self.clearStatusBarText)

        self.spectateButtonImage = tk.PhotoImage(file="./img/spectate.png").zoom(2, 2)
        self.spectateButton = ttk.Button(self.toolbar, command=self.onSpectateButtonClicked, image=self.spectateButtonImage)
        self.spectateButton.pack(side=tk.LEFT)
        self.spectateButton.bind("<Enter>", self.onSpectateButtonHovered)
        self.spectateButton.bind("<Leave>", self.clearStatusBarText)

        self.separator2 = ttk.Separator(self.toolbar, orient=tk.VERTICAL)
        self.separator2.pack(side=tk.LEFT)

        self.playOfflineButtonImage = tk.PhotoImage(file="./img/play_offline.png").zoom(2, 2)
        self.playOfflineButton = ttk.Button(self.toolbar, command=self.onPlayOfflineButtonClicked, image=self.playOfflineButtonImage)
        self.playOfflineButton.pack(side=tk.LEFT)
        self.playOfflineButton.bind("<Enter>", self.onPlayOfflineButtonHovered)
        self.playOfflineButton.bind("<Leave>", self.clearStatusBarText)

        self.serverListFrame = ttk.Frame(self.root)
        self.serverListFrame.pack(fill=tk.BOTH, side=tk.TOP, expand=True)

        self.serverListWidgetScrollbar = ttk.Scrollbar(self.serverListFrame)
        self.serverListWidgetScrollbar.pack(fill=tk.Y, side=tk.RIGHT)

        self.serverListWidgetHeadings = ["Ping", "Game Type", "Map", "Human Players", "All Players", "Player Limit", "Address"]
        self.serverListWidgetKeys = ["ping", "gametype", "map", "rules/g_humanplayers", "numplayers", "maxplayers", "address"]
        self.serverListWidget = ttk.Treeview(self.serverListFrame, columns=self.serverListWidgetHeadings, height=10,
                                             selectmode=tk.BROWSE, yscrollcommand=self.serverListWidgetScrollbar.set)
        self.serverListWidget.heading("#0", text="Name", command=lambda: self.onListHeadingClicked("name"))
        for heading in self.serverListWidgetHeadings:
            self.serverListWidget.heading(heading, text=heading, command=lambda h=heading: self.onListHeadingClicked(h))
        self.serverListWidget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.serverListWidgetScrollbar.config(command=self.serverListWidget.yview)

        self.serverInfoFrame = ttk.LabelFrame(self.root, text="Server info")
        self.serverInfoFrame.pack(fill=tk.BOTH)

        self.mapImagePlaceholder = getPlaceholderMapImg()

        self.serverInfoMapImg = ttk.Label(self.serverInfoFrame, image=self.mapImagePlaceholder)
        self.serverInfoMapImg.pack(side=tk.LEFT)

        self.serverInfoWidgetScrollbar = ttk.Scrollbar(self.serverInfoFrame)
        self.serverInfoWidgetScrollbar.pack(fill=tk.Y, side=tk.RIGHT)

        self.serverInfoWidget = ttk.Treeview(self.serverInfoFrame, height=10, show="tree", selectmode=tk.BROWSE, columns=("1",), yscrollcommand=self.serverInfoWidgetScrollbar.set)
        self.serverInfoWidget.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.serverInfoWidgetScrollbar.config(command=self.serverInfoWidget.yview)

        self.statusBar = ttk.Label(self.root, relief=tk.RIDGE, anchor=tk.W)
        self.statusBar.pack(side=tk.BOTTOM, fill=tk.X)

        self.refreshServerList()

        self.serverListWidget.bind("<ButtonRelease-1>", self.onServerListItemClicked)
        self.serverListWidget.bind("<Double-Button-1>", self.onServerListItemDoubleclicked)
        self.root.mainloop()

    def updateServerListWidget(self):
        def strToIntOrStr(string: str):
            try:
                output = int(string)
            except:
                output = string
            return output

        self.serverJson = sorted(self.serverJson, key=lambda item: strToIntOrStr(getValueByKey(item, self.sortBy)), reverse=self.shouldReverseSorting)

        self.serverListWidget.delete(*self.serverListWidget.get_children()) # Clear the widget
        self.serverListWidget.update()
        for i, server in enumerate(self.serverJson):
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

    def refreshServerList(self):
        self.statusBar["text"] = "Querying..."
        self.root.update()
        startTime = time.time()
        serverListJson = getServerListJson(GAME)

        if serverListJson.startswith("ERROR: "):
            self.statusBar["text"] = serverListJson
            return

        self.statusBar["text"] = "Parsing response..."
        parsedJson = json.loads(serverListJson)
        self.root.update()

        self.masterJson = parsedJson[0]
        self.serverJson = parsedJson[1:]
        for item in self.serverJson:
            item["name"] = item["name"].strip()

        self.statusBar["text"] = "Displaying..."
        self.root.update()
        self.updateServerListWidget()

        self.statusBar["text"] = "Found {} servers, {} responsive. (took {:.2f}s)".format(self.masterJson["servers"], len(self.serverJson), time.time()-startTime)

    def clearStatusBarText(self, _=None): self.statusBar["text"] = ""
    def onRefreshButtonHovered(self, _): self.statusBar["text"] = "Refresh server list."
    def onPlayButtonHovered(self, _): self.statusBar["text"] = "Play on the selected server."
    def onPlayOfflineButtonHovered(self, _): self.statusBar["text"] = "Start the game without connecting to a server."
    def onSpectateButtonHovered(self, _): self.statusBar["text"] = "Spectate on the selected server. (may fail)"

    def onServerListItemClicked(self, _=None):
        self.serverInfoWidget.delete(*self.serverInfoWidget.get_children()) # Clear the widget
        self.serverInfoMapImg.config(image=self.mapImagePlaceholder) # Clear map image widget
        focusedItem = self.serverListWidget.focus()
        if not focusedItem:
            return
        self.statusBar["text"] = "Getting server info..."
        self.statusBar.update()

        serverAddr = self.serverListWidget.item(focusedItem)["values"][self.serverListWidgetKeys.index("address")]
        serverJson = getServerInfoJson(game=GAME, server=serverAddr)

        if serverJson.startswith("ERROR: "):
            self.statusBar["text"] = serverJson
            return

        parsedJson = json.loads(serverJson)[0]

        def addItem(text: str, parent="", vals=[]) -> str:
            id = self.serverInfoWidget.insert(
                parent,
                index="end",
                text=text.strip(),
                values=[str(x).strip() for x in vals],
                tags=[
                    "even" if addItem.i % 2 == 0 else "odd",
                ],
                open=True
            )
            addItem.i += 1
            self.serverListWidget.update()
            return id
        addItem.i = 0

        for k, v in parsedJson.items():
            if k == "rules":
                id = addItem(text=k)
                for kk, vv in v.items():
                    addItem(parent=id, text=kk, vals=[vv])
            elif k == "players":
                id = addItem(text=k)
                for vv in v:
                    addItem(parent=id, text=vv["name"], vals=["Ping: {} | Score: {}".format(str(vv["ping"]).rjust(3, " "), vv["score"])])
            else:
                addItem(text=k, vals=[v])
        self.serverInfoWidget.tag_configure("even", background="#dddddd")
        self.serverInfoWidget.tag_configure("odd", background="#eeeeee")

        self.statusBar["text"] = "Getting map image..."
        self.statusBar.update()
        self.mapImg = getMapImg(parsedJson["map"])
        if self.mapImg:
            self.serverInfoMapImg.config(image=self.mapImg)
            self.serverInfoMapImg.update()

        self.statusBar["text"] = "Done."

    def onServerListItemDoubleclicked(self, _=None):
        focusedItem = self.serverListWidget.focus()
        if not focusedItem:
            return
        serverIp = self.serverListWidget.item(focusedItem)["values"][self.serverListWidgetKeys.index("address")]
        sp.Popen([GAME_EXE_PATH, "+connect", str(serverIp)])

    def onPlayOfflineButtonClicked(self):
        sp.Popen([GAME_EXE_PATH])

    def onSpectateButtonClicked(self):
        focusedItem = self.serverListWidget.focus()
        if not focusedItem:
            return
        serverIp = self.serverListWidget.item(focusedItem)["values"][self.serverListWidgetKeys.index("address")]
        sp.Popen([GAME_EXE_PATH, "+connect", str(serverIp), "+team", "s"])

    def onListHeadingClicked(self, heading):
        if heading == "name":
            sortBy = "name"
        else:
            sortBy = self.serverListWidgetKeys[self.serverListWidgetHeadings.index(heading)]
        if self.sortBy == sortBy:
            self.shouldReverseSorting = not self.shouldReverseSorting
        self.sortBy = sortBy
        self.updateServerListWidget()

if __name__ == "__main__":
    main = Main()

