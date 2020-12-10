# Python Version 2.7.3
# File: minesweeper.py

from tkinter import *
from tkinter import messagebox as tkMessageBox
from collections import deque
import random
import platform
import time
from datetime import time, date, datetime

SIZE_X = 10
SIZE_Y = 10

STATE_DEFAULT = 0
STATE_CLICKED = 1
STATE_FLAGGED = 2

# added myself
indexToPop = 0


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
            "coords": Label(self.frame, text="The best coordinates to pick are: ", wraplength=350, justify=LEFT)
        }
        self.labels["time"].grid(
            row=0, column=0, columnspan=SIZE_Y)  # top full width
        self.labels["mines"].grid(
            row=SIZE_X+1, column=0, columnspan=int(SIZE_Y/2))  # bottom left
        self.labels["flags"].grid(
            row=SIZE_X+1, column=int(SIZE_Y/2)-1, columnspan=int(SIZE_Y/2))  # bottom right
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
                    "mines": 0  # calculated after grid is built
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

        # for j in self.tiles.values():
            # print(j)
        # prints out coordinates of the mines
        mineTracker = []
        mineTrackID = []
        noMineCoords = []
        noMineID = []
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                if self.tiles[x][y]["isMine"] == True:
                    mineTracker.append(self.tiles[x][y]["coords"])
                    mineTrackID.append(self.tiles[x][y]["id"])

                if self.tiles[x][y]["isMine"] == False:
                    noMineCoords.append(self.tiles[x][y]["coords"])
                    noMineID.append(self.tiles[x][y]["id"])
        Minecoords = []
        safeCoords = []
        for k in mineTracker:
            Minecoords.append([k['x'], k['y']])
        for j in noMineCoords:
            safeCoords.append([j['x'], j['y']])

        self.clearSurroundingTiles(mineTrackID[0])

        mineReveal = []

        for x in Minecoords:
            print(x)
        print("------Revealed Mines-----------")

        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                # print(self.tiles[x][y])
                if self.tiles[x][y]["state"] == 1 and self.tiles[x][y]["isMine"] == False:
                    print(self.tiles[x][y])

                    mineReveal.append(self.tiles[x][y]["coords"])

        uniqueMines = []
        print("----prints neighbors of the mine-----")

        self.nonClickedCoords = []
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                # make a click button command based on the previous input lists
                # and self.tiles[x][y]["isMine"] == False:
                if self.tiles[x][y]["state"] == 0 and self.tiles[x][y]["isMine"] == False:
                    # self.onClick(self.tiles[x][y])
                    self.nonClickedCoords.append(self.tiles[x][y]["id"])
        print('--output of nonclicked coords--------')
        for y in self.nonClickedCoords:
            print(y)

        """
        for g in self.nonClickedCoords:
            print(g)

        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                if self.tiles[x][y]["id"] == self.nonClickedCoords[0] and self.tiles[x][y]["state"] == 1:
                    self.nonClickedCoords.pop(0)
        """

    def updateTile(self, x, y):
        for n in self.getNeighbors(x, y):
            if n["mines"] <= 0 and n["isMine"] == False:
                n["button"].config(image=self.images["mine"])

    def restart(self):
        self.setup()
        self.refreshLabels()

    def refreshLabels(self):
        self.labels["flags"].config(text="Flags: "+str(self.flagCount))
        self.labels["mines"].config(text="Mines: "+str(self.mines))
        # need to make a refresh label for mines listed, could possibly only show one at a time and in order
        self.labels["coords"].config(
            text="Best Coordinates: "+str(self.nonClickedCoords))

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

    def onClickWrapper(self, x, y):
        return lambda Button: self.onClick(self.tiles[x][y])

    def onRightClickWrapper(self, x, y):
        return lambda Button: self.onRightClick(self.tiles[x][y])

    def onClick(self, tile):
        if self.startTime == None:
            self.startTime = datetime.now()

        if tile["isMine"] == True:
            # end game
            self.gameOver(False)
            return

        # change image        original was:  if tile["mines"] == 0 modified:
        if tile["mines"] == 0:
            tile["button"].config(image=self.images["clicked"])
            # orig
            self.clearSurroundingTiles(tile["id"])
            #self.updateTile(tile["coords"]["x"], tile["coords"]["y"])

        else:
            tile["button"].config(
                image=self.images["numbers"][tile["mines"]-1])
        # if not already set as clicked, change state and count
        if tile["state"] != STATE_CLICKED:
            tile["state"] = STATE_CLICKED
            self.clickedCount += 1

        if self.clickedCount == (SIZE_X * SIZE_Y) - self.mines:
            self.gameOver(True)

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

    def clearTile(self, tile, queue):
        if tile["state"] != STATE_DEFAULT:
            self.nonClickedCoords.remove(tile["id"])
            self.refreshLabels()
            return

        if tile["mines"] == 0:
            tile["button"].config(image=self.images["clicked"])
            queue.append(tile["id"])
            self.nonClickedCoords.remove(tile["id"])
            self.refreshLabels()

        else:
            tile["button"].config(
                image=self.images["numbers"][tile["mines"]-1])

        tile["state"] = STATE_CLICKED

        self.clickedCount += 1

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