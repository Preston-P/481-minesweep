from tkinter import *
# from tkinter import WORD
from tkinter import messagebox as tkMessageBox
from collections import deque
import random
import platform
import time
import math
from datetime import time, date, datetime

SIZE_X = 10
SIZE_Y = 10

STATE_DEFAULT = 0
STATE_CLICKED = 1
STATE_FLAGGED = 2

BTN_CLICK = "<Button-1>"
BTN_FLAG = "<Button-2>" if platform.system() == 'Darwin' else "<Button-3>"

window = None


class Minesweeper:

    def __init__(self, tk):

        # import images
        self.images = {
            "plain": PhotoImage(file="images/tile_plain.gif"),
            "clicked": PhotoImage(file="images/tile_clicked.gif"),
            "mine": PhotoImage(file="images/tile_mine.gif"),
            "flag": PhotoImage(file="images/tile_flag.gif"),
            "wrong": PhotoImage(file="images/tile_wrong.gif"),
            "best": PhotoImage(file="images/best_tile.gif"),
            "worst": PhotoImage(file="images/worst_tile.gif"),
            "unknown": PhotoImage(file="images/okay_tile.gif"),
            "numbers": []
        }
        for i in range(1, 9):
            self.images["numbers"].append(
                PhotoImage(file="images/tile_"+str(i)+".gif"))

        # set up frame
        self.tk = tk
        self.frame = Frame(self.tk)
        self.frame.pack()

        # set up labels/UI
        self.labels = {
            "time": Label(self.frame, text="00:00:00"),
            "mines": Label(self.frame, text="Mines: 0"),
            "flags": Label(self.frame, text="Flags: 0"),
            "inst": Label(self.frame, text="Click a square to begin Autonomous Player!"),
            "coords": Label(self.frame, text="The best coordinates to pick are: ", wraplength=350, justify=LEFT)
        }
        self.labels["time"].grid(
            row=0, column=0, columnspan=SIZE_Y)  # top full width
        self.labels["mines"].grid(
            row=SIZE_X+1, column=0, columnspan=int(SIZE_Y/2))  # bottom left
        self.labels["flags"].grid(
            row=SIZE_X+1, column=int(SIZE_Y/2)-1, columnspan=int(SIZE_Y/2))  # bottom right
        self.labels["inst"].grid(
            row=SIZE_X+2, column=0, columnspan=SIZE_Y)  # bottom bottom
        self.labels["coords"].grid(row=SIZE_X+3, column=0, columnspan=SIZE_Y)
        self.restart()  # start game
        self.updateTimer()  # init timer

    def setup(self):
        # create flag and clicked tile variables
        self.flagCount = 0
        self.correctFlagCount = 0
        self.clickedCount = 0
        self.startTime = None

        # create buttons
        self.tiles = dict({})
        self.mines = 0
        self.unclicked = []
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                if y == 0:
                    self.tiles[x] = {}

                id = str(x) + "_" + str(y)
                isMine = False

                # tile image changeable for debug reasons:
                gfx = self.images["plain"]

                # currently random amount of mines
                if random.uniform(0.0, 1.0) < 0.1:
                    isMine = True
                    self.mines += 1

                tile = {
                    "id": id,
                    "isMine": isMine,
                    "state": STATE_DEFAULT,
                    "coords": {
                        "x": x,
                        "y": y
                    },
                    "button": Button(self.frame, image=gfx),
                    "mines": 0,  # calculated after grid is built
                    "heuristic": 0  # heuristic calculated after
                }

                tile["button"].bind(BTN_CLICK, self.onClickWrapper(x, y))
                tile["button"].bind(BTN_FLAG, self.onRightClickWrapper(x, y))
                # offset by 1 row for timer
                tile["button"].grid(row=x+1, column=y)

                self.tiles[x][y] = tile

        # loop again to find nearby mines and display number on tile
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                mc = 0
                for n in self.getNeighbors(x, y):
                    mc += 1 if n["isMine"] else 0
                self.tiles[x][y]["mines"] = mc

        self.bestCoords = []

        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                for n in self.getNeighbors(x, y):
                    if n["heuristic"] <= 0.00:
                        if n["id"] not in self.bestCoords:
                            self.bestCoords.append(self.tiles[x][y]["id"])
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                self.unclicked.append(self.tiles[x][y]["id"])

        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                self.tiles[x][y]["heuristic"] = ((math.comb(self.mines, self.tiles[x][y]["mines"]))/(
                    math.comb((len(self.bestCoords)+self.mines), (self.mines-self.flagCount))))
                # self.tiles[x][y]["heuristic"] = (math.comb((len(self.bestCoords)+self.mines),(self.mines-self.flagCount)))
                print(self.tiles[x][y]["id"], ":", self.tiles[x][y]["mines"], ",", self.tiles[x]
                      [y]["heuristic"], ",", self.mines, ", ", self.tiles[x][y]["isMine"])
                # print(self.tiles[x][y]["heuristic"])
        # print(self.bestCoords)

    def heuristic(self, tile):
        numrevealed = 0
        unclicked = 0
        totalmines = tile["mines"]
        # for x in range(0, SIZE_X):
        # for y in range(0, SIZE_Y):
        for k in self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"]):
            if k["state"] == 0 and k["isMine"] == False:
                numrevealed += 1
                if k["state"] == STATE_FLAGGED:
                    numrevealed -= 1
            if k["state"] == 0:
                unclicked += 1
            if k["state"] == 1:
                totalmines += k["mines"]
                # print(numrevealed)
                # tile["heuristic"] = numrevealed + unclicked
        tile["heuristic"] = math.comb(unclicked, numrevealed)

        # print(tile["heuristic"])
        possible = tile["heuristic"]
        print('this is total mines', totalmines)
        print('this is possible', possible)
        if possible == 1:
            for k in self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"]):
                if k["state"] == 0:
                    k["button"].config(image=self.images["flag"])

    def updateTiles(self):
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                for n in self.getNeighbors(x, y):
                    if n["isMine"] == False and n["state"] == STATE_DEFAULT:
                        n["button"].config(image=self.images["best"])
                    if n["isMine"] == True and n["state"] == STATE_DEFAULT:
                        n["button"].config(image=self.images["worst"])
                # if self.tiles[x][y]

    def updateTile(self, x, y):
        for n in self.getNeighbors(x, y):
            if n["mines"] <= 0 and n["isMine"] == False and n["state"] == 0:
                n["button"].config(image=self.images["best"])

    def updateUnclicked(self):
        b = []
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                if self.tiles[x][y]["state"] == STATE_DEFAULT and self.tiles[x][y]["isMine"] == False:
                    b.append(self.tiles[x][y]["id"])
                    self.unclicked = b
                    for n in self.getNeighbors(x, y):
                        if n["mines"] <= 0 and n["isMine"] == False and n["state"] == 0:
                            n["button"].config(image=self.images["best"])
                # self.updateHeuristic(x, y)

        # self.updateHeuristic()
        # self.unclicked = b
        self.refreshLabels()

    def restart(self):
        self.setup()
        self.refreshLabels()

    def refreshLabels(self):
        self.labels["flags"].config(text="Flags: "+str(self.flagCount))
        self.labels["mines"].config(text="Mines: "+str(self.mines))
        self.labels["coords"].config(
            text="Best Coordinates: "+str(self.unclicked))
        # self.updateTiles()

    def gameOver(self, won):
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                if self.tiles[x][y]["isMine"] == False and self.tiles[x][y]["state"] == STATE_FLAGGED:
                    self.tiles[x][y]["button"].config(
                        image=self.images["wrong"])
                if self.tiles[x][y]["isMine"] == True and self.tiles[x][y]["state"] != STATE_FLAGGED:
                    self.tiles[x][y]["button"].config(
                        image=self.images["mine"])

        self.tk.update()

        msg = "You Win! Play again?" if won else "You Lose! Play again?"
        res = tkMessageBox.askyesno("Game Over", msg)
        if res:
            self.restart()
        else:
            self.tk.quit()

    def updateTimer(self):
        ts = "00:00:00"
        if self.startTime != None:
            delta = datetime.now() - self.startTime
            ts = str(delta).split('.')[0]  # drop ms
            if delta.total_seconds() < 36000:
                ts = "0" + ts  # zero-pad
        self.labels["time"].config(text=ts)
        self.frame.after(100, self.updateTimer)

    def getNeighbors(self, x, y):
        neighbors = []
        coords = [
            {"x": x-1,  "y": y-1},  # top right
            {"x": x-1,  "y": y},  # top middle
            {"x": x-1,  "y": y+1},  # top left
            {"x": x,    "y": y-1},  # left
            {"x": x,    "y": y+1},  # right
            {"x": x+1,  "y": y-1},  # bottom right
            {"x": x+1,  "y": y},  # bottom middle
            {"x": x+1,  "y": y+1},  # bottom left
        ]
        for n in coords:
            try:
                neighbors.append(self.tiles[n["x"]][n["y"]])
            except KeyError:
                pass
        return neighbors

    def getUnclicked(self):
        coords = []
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                if self.tiles[x][y]["state"] == STATE_DEFAULT:
                    coords.append(self.tiles[x][y].id)
        # return coords
        self.unclicked = coords

    def onClickWrapper(self, x, y):
        return lambda Button: self.onClick(self.tiles[x][y])

    def onRightClickWrapper(self, x, y):
        return lambda Button: self.onRightClick(self.tiles[x][y])

    def makeGreen(self, x, y):
        notrevealed = 0
        for k in self.getNeighbors(x, y):
            if k["isMine"] == False and k["state"] == 0:
                k["button"].config(image=self.images["best"])
            """ if k["mines"] > 0 and (k["mines"] == (k["state"] == 0)):
                notrevealed = k["mines"]
                print(notrevealed)
                self.tiles[x][y]["heuristic"] == notrevealed """

    def updateHeuristic(self, x, y):
        # for x in range(0, SIZE_X):
        #     for y in range(0, SIZE_Y):
        self.tiles[x][y]["heuristic"] = ((math.comb(self.mines, self.tiles[x][y]["mines"]))/(
            math.comb((len(self.bestCoords)+self.mines), (self.mines-self.flagCount))))
        print(self.tiles[x][y]["id"], ":", self.tiles[x][y]["mines"], ",", self.tiles[x]
              [y]["heuristic"], ",", self.mines, ", ", self.tiles[x][y]["isMine"])

    def onClick(self, tile):
        totaltiles = len(self.getNeighbors(
            tile["coords"]["x"], tile["coords"]["y"]))
        possible = 0
        totalmines = tile["mines"]
        if self.startTime == None:
            self.startTime = datetime.now()

        if tile["isMine"] == True:
            # end game
            self.gameOver(False)
            return

        self.makeGreen(tile["coords"]["x"], tile["coords"]["y"])
        if tile["mines"] > 0:
            self.heuristic(tile)
        """ numrevealed = 0
        unclicked = 0
        if tile["mines"] > 0:
            for k in self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"]):
                if k["state"] == 0 and k["isMine"] == False:
                    numrevealed += 1
                    if k["state"] == STATE_FLAGGED:
                        numrevealed -= 1
                if k["state"] == 0:
                    unclicked += 1
                if k["state"] == 1:
                    totalmines += k["mines"]
            # print(numrevealed)
            # tile["heuristic"] = numrevealed + unclicked
            tile["heuristic"] = math.comb(unclicked, numrevealed)

        # print(tile["heuristic"])
        possible = tile["heuristic"]
        print('this is total mines', totalmines)
        print('this is possible', possible)
        if possible == 1:
            for k in self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"]):
                if k["state"] == 0:
                    k["button"].config(image=self.images["flag"]) """

        # print(possible)

        if tile["mines"] == 0:
            tile["button"].config(image=self.images["clicked"])
            self.updateTile(tile["coords"]["x"], tile["coords"]["y"])
            self.clearSurroundingTiles(tile["id"])
            # self.updateUnclicked()
            # self.updateTile(tile["coords"]["x"],tile["coords"]["y"])
            # self.updateTiles()  # uncomment to turn tiles diff colors
            # getUnclicked()
        else:
            tile["button"].config(
                image=self.images["numbers"][tile["mines"]-1])
            self.updateTile(tile["coords"]["x"], tile["coords"]["y"])
        # if not already set as clicked, change state and count
        if tile["state"] != STATE_CLICKED:
            self.updateTile(tile["coords"]["x"], tile["coords"]["y"])
            tile["state"] = STATE_CLICKED
            self.clickedCount += 1
        if self.clickedCount == (SIZE_X * SIZE_Y) - self.mines:
            self.gameOver(True)

        # self.unclicked.remove(tile["id"])
        # self.refreshLabels()

        self.updateUnclicked()
        # self.updateTile(tile["coords"]["x"], tile["coords"]["y"])

    def onRightClick(self, tile):
        if self.startTime == None:
            self.startTime = datetime.now()

        # if not clicked
        if tile["state"] == STATE_DEFAULT:
            tile["button"].config(image=self.images["flag"])
            tile["state"] = STATE_FLAGGED
            tile["button"].unbind(BTN_CLICK)
            # if a mine
            if tile["isMine"] == True:
                self.correctFlagCount += 1

            self.flagCount += 1

            self.refreshLabels()
        # if flagged, unflag
        elif tile["state"] == 2:
            tile["button"].config(image=self.images["plain"])
            tile["state"] = 0
            tile["button"].bind(BTN_CLICK, self.onClickWrapper(
                tile["coords"]["x"], tile["coords"]["y"]))
            # if a mine
            if tile["isMine"] == True:
                self.correctFlagCount -= 1
            self.flagCount -= 1
            self.refreshLabels()

    def clearSurroundingTiles(self, id):
        queue = deque([id])

        while len(queue) != 0:
            key = queue.popleft()
            parts = key.split("_")
            x = int(parts[0])
            y = int(parts[1])

            for tile in self.getNeighbors(x, y):
                self.clearTile(tile, queue)
                # self.unclicked.remove(tile["id"])
                # self.refreshLabels()
                # self.tiles[x][y]["button"].config(image = self.images["unknown"])
                # self.unclicked.remove(self.tiles[x][y])

    def clearTile(self, tile, queue):
        if tile["state"] != STATE_DEFAULT:
            return
        if tile["mines"] == 0:
            tile["button"].config(image=self.images["clicked"])
            queue.append(tile["id"])
        else:
            tile["button"].config(
                image=self.images["numbers"][tile["mines"]-1])

        tile["state"] = STATE_CLICKED
        self.clickedCount += 1
        # for x in self.getNeighbors(tile["coords"]["x"],tile["coords"]["y"]):
        # if x["state"] == STATE_DEFAULT and x["isMine"] == False:
        # x["button"].config(image = self.images["best"])


### END OF CLASSES ###

def main():
    # create Tk instance
    window = Tk()
    # set program title
    window.title("Minesweeper")
    # create game instance
    minesweeper = Minesweeper(window)
    # run event loop
    window.mainloop()


if __name__ == "__main__":
    main()
