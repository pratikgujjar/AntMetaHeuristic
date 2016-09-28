from random import randint
import threading
import numpy as np
import time
from Tkinter import *
import Queue

HOME_POS = [2, 2]
FOOD_POS = [96, 96]
NUMBER_OF_ANTS = 100
FORAGING_SQUARE_AREA = 100
FOOD_FOUND_FLAG = False
FOOD_CONTENT = 1000
FOOD_EXHAUSTED_FLAG = False
masterFoodTrail = 0
TIME_DELAY = 0.05
SCALING_FACTOR = 5
RANGING_RADIUS = 2
SEPARATION = 3
TRAIL_LENGTH = 40


# WorldMap [number of ant visits] for the given coordinate
worldMap = np.zeros(shape=(FORAGING_SQUARE_AREA, FORAGING_SQUARE_AREA), dtype=int)

pheromoneMap = np.zeros(shape=(FORAGING_SQUARE_AREA, FORAGING_SQUARE_AREA), dtype=int)
pheromoneMap.fill(100000)
foodomoneMap = np.zeros(shape=(FORAGING_SQUARE_AREA, FORAGING_SQUARE_AREA), dtype=int)
foodomoneMap.fill(100000)

pheromoneQueue = Queue.Queue()
foodomoneQueue = Queue.Queue()

LATEST_POSITIONS = [[0,0] for i in range(NUMBER_OF_ANTS)]
print "LATEST_POSITIONS: " + str(LATEST_POSITIONS)
heroAnt = None

# Define Ant Behaviour


class Ant(threading.Thread):
    def __init__(self, homePos, antNumber, foodPos):
        threading.Thread.__init__(self)
        self.homePos = homePos
        self.currentPos = homePos
        self.travelList = [homePos]
        self.antNumber = antNumber
        self.foodPos = foodPos
        self.foodFoundByMe = False
        self.carryingFood = False
        self.trailEnteredFlag = False
        self.distanceFromHome = 0
        self.distanceFromFood = 0
        self.currentDirection = 0
        self.continueOnPath = 2

    # Thread Start
    def run(self):

        self.startForaging()
        self.startPheromoneTrailing()
        # print "\nFood found by heroAnt = " + str(heroAnt.antNumber) + " as acknowledged by ant " + str(self.antNumber)

    def startForaging(self):
        global LATEST_POSITIONS
        global FOOD_FOUND_FLAG
        global heroAnt

        while (FOOD_FOUND_FLAG!= True):
            time.sleep(TIME_DELAY)
            LATEST_POSITIONS[self.antNumber - 1] = self.currentPos
            if self.currentPos != self.foodPos:
                    self.forage()
            else:
                print "Food found by ant " + str(self.antNumber) + " in " + str(len(self.travelList)) + " passes"
                self.foodFoundByMe = True
                FOOD_FOUND_FLAG = True
                heroAnt = self

    def determineNextPos(self, direction):
        return {
            1: [self.currentPos[0] + 1, self.currentPos[1] + 1],    # North-East
            2: [self.currentPos[0] + 1, self.currentPos[1] + 0],    # East
            3: [self.currentPos[0] + 1, self.currentPos[1] - 1],    # South-East
            4: [self.currentPos[0] + 0, self.currentPos[1] - 1],    # South
            5: [self.currentPos[0] - 1, self.currentPos[1] - 1],    # South-West
            6: [self.currentPos[0] - 1, self.currentPos[1] + 0],    # West
            7: [self.currentPos[0] - 1, self.currentPos[1] + 1],    # North-West
            8: [self.currentPos[0] + 0, self.currentPos[1] + 1],    # North
        }.get(direction)

    def forage(self):
        global FORAGING_SQUARE_AREA

        #print("Continue on path: " + str(self.continueOnPath))

        if(self.continueOnPath == 2):
            self.currentDirection = randint(1, 8)

        if(self.continueOnPath == 0):
            self.continueOnPath = 3

        self.continueOnPath -= 1
        newPos = self.determineNextPos(self.currentDirection)

        if (newPos[0] > 0 and newPos[0] < FORAGING_SQUARE_AREA and newPos[1] > 0 and newPos[1] < FORAGING_SQUARE_AREA):
            #print "Ant" + str(self.antNumber) + "\'s new position is: " + str(newPos)
            self.currentPos = newPos
            self.travelList.append(newPos)

            # Add to distance from home. This will be the pheromone seed
            if(self.foodFoundByMe == False):
                self.distanceFromHome += 1
                self.dropPheromone(newPos)
                pheromoneMap[HOME_POS[0]][HOME_POS[1]] = 0

        else:
            # print "Ant has reached boundaries. Ignoring this movement and restarting foraging"
            self.forage()

    def dropPheromone(self, pos):
        lock = threading.RLock()
        lock.acquire()
        global pheromoneMap
        pheromoneValue = self.distanceFromHome
        if(pheromoneMap[pos[0]][pos[1]] > pheromoneValue):
            pheromoneMap[pos[0]][pos[1]] = pheromoneValue

        lock.release()

    def dropFoodomone(self, pos):
        lock = threading.RLock()
        lock.acquire()
        global worldMap
        global foodomoneMap
        foodomoneValue = self.distanceFromFood
        if (foodomoneMap[pos[0]][pos[1]] > foodomoneValue):
            foodomoneMap[pos[0]][pos[1]] = foodomoneValue

        lock.release()

    def startPheromoneTrailing(self):
        global heroAnt
        global FOOD_CONTENT
        global FOOD_POS
        global FOOD_EXHAUSTED_FLAG
        global HOME_POS
        global pheromoneMap
        global pheromoneQueue
        global foodomoneMap
        global foodomoneQueue
        global SEPARATION

        checkOnce = False

        masterFoodTrail = heroAnt.travelList
        print "Starting pheromone trailing for ant " + str(self.antNumber) + "Current pos " + str(self.currentPos)
        while (FOOD_EXHAUSTED_FLAG != True):

            foodomoneMap[FOOD_POS[0]][FOOD_POS[1]] = 0
            time.sleep(TIME_DELAY)

            # To have a different trails to get to home and food. Avoids collision
            if (self.carryingFood == True):
                if(self.currentPos != HOME_POS):
                    LATEST_POSITIONS[self.antNumber - 1] = [self.currentPos[0] + SEPARATION, self.currentPos[1] + SEPARATION]
                    foodomoneQueue.put(LATEST_POSITIONS[self.antNumber - 1])
                    #print "Actual calculated position : " + str(self.currentPos)
                    #print "Drawn pos: " +  str(LATEST_POSITIONS[self.antNumber - 1])
                else:
                    LATEST_POSITIONS[self.antNumber - 1] = self.currentPos
                    foodomoneQueue.put(LATEST_POSITIONS[self.antNumber - 1])

            else:
                if(self.currentPos != FOOD_POS):
                    LATEST_POSITIONS[self.antNumber - 1] = [self.currentPos[0] - SEPARATION, self.currentPos[1] + SEPARATION]
                    #print "Actual calculated position : " + str(self.currentPos)
                    #print "Drawn pos: " + str(LATEST_POSITIONS[self.antNumber - 1])
                    pheromoneQueue.put(LATEST_POSITIONS[self.antNumber - 1])
                else:
                    LATEST_POSITIONS[self.antNumber - 1] = self.currentPos
                    pheromoneQueue.put(LATEST_POSITIONS[self.antNumber - 1])

            #print "Current pos for ant " + str(self.antNumber) + " is " + str(self.currentPos)
            if(self.foodFoundByMe == True):
                if(self.currentPos == FOOD_POS):
                    self.distanceFromFood = 0
                    if(FOOD_CONTENT>0):
                        FOOD_CONTENT = FOOD_CONTENT - 1
                        self.carryingFood = True
                        print "Food picked up by ant " + str(self.antNumber)
                        self.currentPos, distanceTravelled = self.getBestRoute(pheromoneMap)
                        if(checkOnce == False):
                            self.distanceFromFood += distanceTravelled
                            self.dropFoodomone(self.currentPos)

                    else:
                        FOOD_EXHAUSTED_FLAG = True
                        return

                elif (self.currentPos == HOME_POS):
                    if(self.carryingFood == True):
                        print "Food brought home by ant " + str(self.antNumber)

                    self.carryingFood = False  # Take away the food
                    # print "Foodomone Map: " + str(foodomoneMap)
                    self.currentPos, distance = self.getBestRoute(foodomoneMap)
                    print "New Pos after bringing food home: " + str(self.currentPos)
                    checkOnce = False
                else:
                    if (self.carryingFood == False):
                        self.currentPos, distance = self.getBestRoute(foodomoneMap)
                        #print "New Pos towards food: " + str(self.currentPos)
                    else:
                        self.currentPos, distanceTravelled = self.getBestRoute(pheromoneMap)
                        if(checkOnce == False):
                            self.distanceFromFood += distanceTravelled
                            self.dropFoodomone(self.currentPos)
            else:
                if self.currentPos in masterFoodTrail:
                    if(self.trailEnteredFlag == False):
                        indexCounter = masterFoodTrail.index(self.currentPos) + 1
                        self.trailEnteredFlag = True
                    #print "CurrentPos for ant " + str(self.antNumber) + " is in MasterTrail. Following the MasterTrail"
                    if (self.currentPos != FOOD_POS):
                        self.currentPos = masterFoodTrail[indexCounter]
                        indexCounter = indexCounter + 1
                    else:
                        print "Food found by following MasterTrail"
                        self.foodFoundByMe = True
                else:
                        self.currentPos, distanceTravelled = self.getBestRoute(pheromoneMap)

    def getBestRoute(self, Map):
        lock = threading.RLock()
        lock.acquire()
        global RANGING_RADIUS
        # print("Current position for ant " + str(self.antNumber) + "is " + str(self.currentPos))
        try:
            k1 = Map[self.currentPos[0] + 1][self.currentPos[1] + 1]  # North-East
        except IndexError:
            print IndexError
            k1 = 1000000

        try:
            k2 = Map[self.currentPos[0] + 1][self.currentPos[1] + 0]  # East
        except IndexError:
            print IndexError
            k2 = 1000000

        try:
            k3 = Map[self.currentPos[0] + 1][self.currentPos[1] - 1]  # South-East
        except IndexError:
            print IndexError
            k3 = 1000000

        try:
            k4 = Map[self.currentPos[0] + 0][self.currentPos[1] - 1]  # South
        except IndexError:
            print IndexError
            k4 = 1000000

        try:
            k5 = Map[self.currentPos[0] - 1][self.currentPos[1] - 1]  # South-West
        except IndexError:
            print IndexError
            k5 = 1000000

        try:
            k6 = Map[self.currentPos[0] - 1][self.currentPos[1] + 0]  # West
        except IndexError:
            print IndexError
            k6 = 1000000

        try:
            k7 = Map[self.currentPos[0] - 1][self.currentPos[1] + 1]  # North-West
        except IndexError:
            print IndexError
            k7 = 1000000

        try:
            k8 = Map[self.currentPos[0] + 0][self.currentPos[1] + 1]  # North
        except IndexError:
            print IndexError
            k8 = 1000000

        try:
            j1 = Map[self.currentPos[0] + 2][self.currentPos[1] + 1]  # East Side
        except IndexError:
            print IndexError
            j1 = 1000000

        try:
            j2 = Map[self.currentPos[0] + 2][self.currentPos[1] + 0]  # East Side
        except IndexError:
            print IndexError
            j2 = 1000000

        try:
            j3 = Map[self.currentPos[0] + 2][self.currentPos[1] - 1]  # East Side
        except IndexError:
            print IndexError
            j3 = 1000000

        try:
            j4 = Map[self.currentPos[0] + 1][self.currentPos[1] - 2]  # South Side
        except IndexError:
            print IndexError
            j4 = 1000000

        try:
            j5 = Map[self.currentPos[0] + 0][self.currentPos[1] - 2]  # South Side
        except IndexError:
            print IndexError
            j5 = 1000000

        try:
            j6 = Map[self.currentPos[0] - 1][self.currentPos[1] - 2]  # South Side
        except IndexError:
            print IndexError
            j6 = 1000000

        try:
            j7 = Map[self.currentPos[0] - 2][self.currentPos[1] - 1]  # West Side
        except IndexError:
            print IndexError
            j7 = 1000000

        try:
            j8 = Map[self.currentPos[0] - 2][self.currentPos[1] + 0]  # West Side
        except IndexError:
            print IndexError
            j8 = 1000000

        try:
            j9 = Map[self.currentPos[0] - 2][self.currentPos[1] + 1]  # West Side
        except IndexError:
            print IndexError
            j9 = 1000000

        try:
            j10 = Map[self.currentPos[0] - 1][self.currentPos[1] + 2]  # North Side
        except IndexError:
            print IndexError
            j10 = 1000000

        try:
            j11 = Map[self.currentPos[0] + 0][self.currentPos[1] + 2]  # North Side
        except IndexError:
            print IndexError
            j11 = 1000000

        try:
            j12 = Map[self.currentPos[0] + 1][self.currentPos[1] + 2]  # North Side
        except IndexError:
            print IndexError
            j12 = 1000000

        try:
            j13 = Map[self.currentPos[0] + 2][self.currentPos[1] + 2]  # North-East Side
        except IndexError:
            print IndexError
            j13 = 1000000

        try:
            j14 = Map[self.currentPos[0] + 2][self.currentPos[1] - 2]  # South-East Side
        except IndexError:
            print IndexError
            j14 = 1000000

        try:
            j15 = Map[self.currentPos[0] - 2][self.currentPos[1] - 2]  # South-West Side
        except IndexError:
            print IndexError
            j15 = 100000

        try:
            j16 = Map[self.currentPos[0] - 2][self.currentPos[1] + 2]  # North-West Side
        except IndexError:
            print IndexError
            j16 = 100000

        #checkList.extend([min(k1), min(k2), min(k3), min(k4), min(k5), min(k6), min(k7), min(k8), min(j1),
        #                  min(j2), min(j3), min(j4), min(j5), min(j6), min(j7), min(j8), min(j9), min(j10),
        #                  min(j11), min(j12)])

        lock.release()
        checkList = [(k1), (k2), (k3), (k4), (k5), (k6), (k7), (k8), (j1),
                         (j2), (j3), (j4), (j5), (j6), (j7), (j8), (j9), (j10),
                         (j11), (j12), (j13), (j14), (j15), (j16)]

        if(min(checkList) == 1000000):
            self.currentDirection = randint(1, 8)
            newPos = self.determineNextPos(self.currentDirection)
            return newPos, 1


        # print ("Checklist : " + str(checkList) + "for antNUmber : " + str(self.antNumber))
        # print ("Map being used: " + str(Map))
        newPosIndex = checkList.index(min(checkList))
        # print("min of checklist: " + str(min(checkList)))

        if(newPosIndex > 7):
            distanceTravelled = 2
        else:
            distanceTravelled = 1

        newPos = self.switchToBestPheromone(newPosIndex)

        return newPos, distanceTravelled

    def switchToBestPheromone(self, min):
        return {
            1: [self.currentPos[0] + 1, self.currentPos[1] + 1], # North-East
            2: [self.currentPos[0] + 1, self.currentPos[1] + 0], # East
            3: [self.currentPos[0] + 1, self.currentPos[1] - 1], # South-East
            4: [self.currentPos[0] + 0, self.currentPos[1] - 1], # South
            5: [self.currentPos[0] - 1, self.currentPos[1] - 1], # South-West
            6: [self.currentPos[0] - 1, self.currentPos[1] + 0], # West
            7: [self.currentPos[0] - 1, self.currentPos[1] + 1], # North-West
            8: [self.currentPos[0] + 0, self.currentPos[1] + 1], # North
            9: [self.currentPos[0] + 2, self.currentPos[1] + 1], # East Side
            10: [self.currentPos[0] + 2, self.currentPos[1] + 2], # East Side
            11: [self.currentPos[0] + 2, self.currentPos[1] - 1], # East Side
            12: [self.currentPos[0] + 1, self.currentPos[1] - 2], # South Side
            13: [self.currentPos[0] + 0, self.currentPos[1] - 2], # South Side
            14: [self.currentPos[0] - 1, self.currentPos[1] - 2], # South Side
            15: [self.currentPos[0] - 2, self.currentPos[1] - 1], # West Side
            16: [self.currentPos[0] - 2, self.currentPos[1] + 0], # West Side
            17: [self.currentPos[0] - 2, self.currentPos[1] + 1], # West Side
            18: [self.currentPos[0] - 1, self.currentPos[1] + 2], # North Side
            19: [self.currentPos[0] + 0, self.currentPos[1] + 2], # North Side
            20: [self.currentPos[0] + 1, self.currentPos[1] + 2], # North Side
            21: [self.currentPos[0] + 2, self.currentPos[1] + 2], # North-East Side
            22: [self.currentPos[0] + 2, self.currentPos[1] - 2], # South-East Side
            23: [self.currentPos[0] - 2, self.currentPos[1] - 2], # South-West Side
            24: [self.currentPos[0] - 2, self.currentPos[1] + 2]  # North-West Side

        }.get(min + 1)


#######################################################################

class AntOvals():
    def __init__(self, canvas, x1, y1, x2, y2, antNumber):
        self.antNumber = antNumber
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.canvas = canvas
        self.ball = canvas.create_oval(self.x1, self.y1, self.x2, self.y2, fill="blue", outline="blue")


    def move_ball(self):

        self.canvas.coords(self.ball, SCALING_FACTOR * LATEST_POSITIONS[self.antNumber - 1][0],
                           SCALING_FACTOR * LATEST_POSITIONS[self.antNumber - 1][1],
                           SCALING_FACTOR * LATEST_POSITIONS[self.antNumber - 1][0] + 5,
                           SCALING_FACTOR * LATEST_POSITIONS[self.antNumber - 1][1] + 5)

        if(self.canvas.coords(self.ball) == [SCALING_FACTOR * FOOD_POS[0],
                                             SCALING_FACTOR * FOOD_POS[1],
                                             SCALING_FACTOR * FOOD_POS[0] + 5,
                                             SCALING_FACTOR * FOOD_POS[0] + 5]):
            self.canvas.itemconfig(self.ball, fill="red", outline="red")

        if(self.canvas.coords(self.ball) == [SCALING_FACTOR * HOME_POS[0],
                                             SCALING_FACTOR * HOME_POS[1],
                                             SCALING_FACTOR * HOME_POS[0] + 5,
                                             SCALING_FACTOR * HOME_POS[0] + 5]):
            self.canvas.itemconfig(self.ball, fill="blue", outline="blue")

        pheromoneList = list(pheromoneQueue.queue)
        #print "PheromoneList: " + str(pheromoneList)
        foodomoneList = list(foodomoneQueue.queue)
        #print "FoodomoneList: " + str(foodomoneList)

        # while(len(pheromoneList) > 18):
        #     pheromoneQueue.get()
        #     pheromoneList = list(pheromoneQueue.queue)
        #
        # while(len(foodomoneList) > 18):
        #     foodomoneQueue.get()
        #     foodomoneList = list(foodomoneQueue.queue)
        #
        # for i in range(len(pheromoneList)):
        #     self.canvas.coords(markers[i],SCALING_FACTOR * pheromoneList[i][0],
        #                    SCALING_FACTOR * pheromoneList[i][1],
        #                    SCALING_FACTOR * pheromoneList[i][0] + 2,
        #                    SCALING_FACTOR * pheromoneList[i][1] + 2)
        #
        # for i in range(len(foodomoneList)):
        #     self.canvas.coords(markers[i + 39],SCALING_FACTOR * foodomoneList[i][0],
        #                    SCALING_FACTOR * foodomoneList[i][1],
        #                    SCALING_FACTOR * foodomoneList[i][0] + 2,
        #                    SCALING_FACTOR * foodomoneList[i][1] + 2)

        self.canvas.after(50, self.move_ball)


###############################################################################################


# initialize root Window and canvas
root = Tk()
root.title("Ant Meta-Heuristic")
root.resizable(False, False)
canvas = Canvas(root, bg = "white", confine = True,  width= 600, height= 600)
canvas.pack()

# Create n ants
ants = []
antOvals = []
for i in range(1, NUMBER_OF_ANTS + 1, 1):
    ants.append(Ant(HOME_POS, i, FOOD_POS))
    antOvals.append(AntOvals(canvas, HOME_POS[0], HOME_POS[1], HOME_POS[0]+5, HOME_POS[1]+5, i))
    print str(len(ants)) + " ant thread(s) (is) are running"

print "FOOD_CONTENT before foraging: " + str(FOOD_CONTENT)

# create two ball objects and animate them

print "Creating ants"
# Start ant foraging
for ant in ants:
    ant.start()

canvas.create_rectangle((SCALING_FACTOR * HOME_POS[0]) - 10, (SCALING_FACTOR * HOME_POS[1]) - 10,
                        (SCALING_FACTOR * HOME_POS[0]) + 10, (SCALING_FACTOR * HOME_POS[1]) + 10, fill="blue", outline="blue")

canvas.create_rectangle((SCALING_FACTOR * FOOD_POS[0]) - 10, (SCALING_FACTOR * FOOD_POS[1]) - 10,
                        (SCALING_FACTOR * FOOD_POS[0]) + 10, (SCALING_FACTOR * FOOD_POS[1]) + 10, fill="red", outline="red")

markers = []
for i in range(TRAIL_LENGTH):
    markers.append(canvas.create_oval(HOME_POS[0], HOME_POS[1], HOME_POS[0]+2, HOME_POS[1]+2, fill="blue", outline="blue"))

for i in range(TRAIL_LENGTH):
    markers.append(canvas.create_oval(HOME_POS[0], HOME_POS[1], HOME_POS[0]+2, HOME_POS[1]+2, fill="red", outline="red"))

print (str(markers))

for antOval in antOvals:
    antOval.move_ball()

root.mainloop()

# Wait for threads to end
for thread in ants:
    thread.join()

print "FOOD_CONTENT after foraging: " + str(FOOD_CONTENT)
print "worldMap: \n" + str(worldMap)
np.set_printoptions(threshold='nan')

text_file = open("Output.txt", "w")
text_file.write("Foodomone Map is : %s" % str(foodomoneMap))
text_file.close()

print "pheromoneMap: \n" + str(pheromoneMap)
print "FoodomoneMap: \n" + str(foodomoneMap)
print LATEST_POSITIONS
print "Length of latest positions: " + str(len(LATEST_POSITIONS))