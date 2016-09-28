from random import randint
import threading
import numpy as np
import time
from Tkinter import *

HOME_POS = [2, 2]
FOOD_POS = [10, 10]
NUMBER_OF_ANTS = 3
FORAGING_SQUARE_AREA = 15
FOOD_FOUND_FLAG = False
FOOD_CONTENT = 10
FOOD_EXHAUSTED_FLAG = False
masterFoodTrail = 0
TIME_DELAY = 0.09
SCALING_FACTOR = 30
RANGING_RADIUS = 2

# WorldMap [number of ant visits] for the given coordinate
worldMap = np.zeros(shape=(FORAGING_SQUARE_AREA, FORAGING_SQUARE_AREA), dtype=int)

#pheromoneMap = [[[100, 100, 100, 100, 100, 100, 100, 100]] * FORAGING_SQUARE_AREA for i in range(FORAGING_SQUARE_AREA)]
pheromoneMap = np.zeros(shape=(FORAGING_SQUARE_AREA, FORAGING_SQUARE_AREA, 8), dtype=int)
pheromoneMap.fill(100)
foodomoneMap = np.zeros(shape=(FORAGING_SQUARE_AREA, FORAGING_SQUARE_AREA), dtype=int)
foodomoneMap.fill(100)

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
        global worldMap

        self.currentDirection = randint(1, 8)
        newPos = self.determineNextPos(self.currentDirection)

        if (newPos[0] > 0 and newPos[0] < FORAGING_SQUARE_AREA and newPos[1] > 0 and newPos[1] < FORAGING_SQUARE_AREA):
            print "Ant" + str(self.antNumber) + "\'s new position is: " + str(newPos)
            self.currentPos = newPos
            self.travelList.append(newPos)

            # Update worldMap and drop pheromone
            worldMap[newPos[0]][newPos[1]] += 1

            # Add to distance from home. This will be the pheromone seed
            if(self.foodFoundByMe == False):
                self.distanceFromHome += 1
                self.dropToHomePheromone(newPos)
                pheromoneMap[HOME_POS[0]][HOME_POS[1]] = 0

        else:
            # print "Ant has reached boundaries. Ignoring this movement and restarting foraging"
            self.forage()

    def dropToHomePheromone(self, pos):
        global worldMap
        pheromoneValue = self.distanceFromHome
        if(pheromoneMap[pos[0]][pos[1]][self.currentDirection - 1] > pheromoneValue):
            pheromoneMap[pos[0]][pos[1]][self.currentDirection - 1] = pheromoneValue

    def dropToFoodPheromone(self, pos):
        global worldMap
        foodomoneValue = self.distanceFromFood
        if (foodomoneMap[pos[0]][pos[1]] > foodomoneValue):
            foodomoneMap[pos[0]][pos[1]] = foodomoneValue

    def startPheromoneTrailing(self):
        global heroAnt
        global FOOD_CONTENT
        global FOOD_POS
        global FOOD_EXHAUSTED_FLAG
        global HOME_POS

        masterFoodTrail = heroAnt.travelList

        print "Starting pheromone trailing for ant " + str(self.antNumber) + "Current pos " + str(self.currentPos)

        while (FOOD_EXHAUSTED_FLAG != True):
            time.sleep(TIME_DELAY)
            LATEST_POSITIONS[self.antNumber - 1] = self.currentPos
            #print "Current pos for ant " + str(self.antNumber) + " is " + str(self.currentPos)
            if(self.foodFoundByMe == True):
                #print "inside the food found loop for ant " + str(self.antNumber)
                if(self.currentPos == FOOD_POS):
                    self.distanceFromFood = 0
                    j = 3
                    k = 2
                    if(FOOD_CONTENT>0):
                        FOOD_CONTENT = FOOD_CONTENT - 1
                        self.carryingFood = True
                        print "Food picked up by ant " + str(self.antNumber)
                        self.currentPos, distanceTravelled = self.getBestRoute(pheromoneMap)
                        self.distanceFromFood += distanceTravelled
                        self.dropToFoodPheromone(self.currentPos)

                    else:
                        FOOD_EXHAUSTED_FLAG = True
                        return
                elif (self.currentPos == HOME_POS):
                    if(self.carryingFood == True):
                        print "Food brought home by ant " + str(self.antNumber)

                    self.carryingFood = False  # Take away the food
                    self.currentPos = self.getBestRoute(foodomoneMap)

                else:
                    if (self.carryingFood == False):
                        self.currentPos = self.getBestRoute(foodomoneMap)
                    else:
                        self.currentPos, distanceTravelled = self.getBestRoute(pheromoneMap)
                        self.distanceFromFood += distanceTravelled
                        self.dropToFoodPheromone(self.currentPos)
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
                        self.forage()

    def getBestRoute(self, Map):
        global RANGING_RADIUS
        checkList = []

        k1 = Map[self.currentPos[0] + 1][self.currentPos[1] + 1]  # North-East
        k2 = Map[self.currentPos[0] + 1][self.currentPos[1] + 0]  # East
        k3 = Map[self.currentPos[0] + 1][self.currentPos[1] - 1]  # South-East
        k4 = Map[self.currentPos[0] + 0][self.currentPos[1] - 1]  # South
        k5 = Map[self.currentPos[0] - 1][self.currentPos[1] - 1]  # South-West
        k6 = Map[self.currentPos[0] - 1][self.currentPos[1] + 0]  # West
        k7 = Map[self.currentPos[0] - 1][self.currentPos[1] + 1]  # North-West
        k8 = Map[self.currentPos[0] + 0][self.currentPos[1] + 1]  # North
        j1 = Map[self.currentPos[0] + 2][self.currentPos[1] + 1]  # East Side
        j2 = Map[self.currentPos[0] + 2][self.currentPos[1] + 2]  # East Side
        j3 = Map[self.currentPos[0] + 2][self.currentPos[1] - 1]  # East Side
        j4 = Map[self.currentPos[0] + 1][self.currentPos[1] - 2]  # South Side
        j5 = Map[self.currentPos[0] + 0][self.currentPos[1] - 2]  # South Side
        j6 = Map[self.currentPos[0] - 1][self.currentPos[1] - 2]  # South Side
        j7 = Map[self.currentPos[0] - 2][self.currentPos[1] - 1]  # West Side
        j8 = Map[self.currentPos[0] - 2][self.currentPos[1] + 0]  # West Side
        j9 = Map[self.currentPos[0] - 2][self.currentPos[1] + 1]  # West Side
        j10 = Map[self.currentPos[0] - 1][self.currentPos[1] + 2]  # North Side
        j11 = Map[self.currentPos[0] + 0][self.currentPos[1] + 2]  # North Side
        j12 = Map[self.currentPos[0] + 1][self.currentPos[1] + 2]  # North Side

        checkList.extend([min(k1), min(k2), min(k3), min(k4), min(k5), min(k6), min(k7), min(k8), min(j1),
                          min(j2), min(j3), min(j4), min(j5), min(j6), min(j7), min(j8), min(j9), min(j10),
                          min(j11), min(j12)])

        print ("Checklist : " + str(checkList))
        newPosIndex = checkList.index(min(checkList))

        if(newPosIndex > 7):
            distanceTravelled = 2
        else:
            distanceTravelled = 1

        newPos = self.switchToBestPheromone(newPosIndex)
        return newPos, distanceTravelled

    def switchToBestPheromone(self, max):
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
            20: [self.currentPos[0] + 1, self.currentPos[1] + 2]  # North Side
        }.get(max + 1)


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
        # deltax = randint(0, 5)
        # deltay = randint(0, 5)
        # self.canvas.move(self.ball, deltax, deltay)


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
    print str(len(ants)) + " ants are running"

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