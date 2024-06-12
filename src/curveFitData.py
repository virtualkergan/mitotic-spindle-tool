import numpy as np

# using thresholded image, return the desired parameters
def curveFitData(imageArr, arr):

    # create identical array for manipulation
    threshArr = np.zeros(shape=arr.shape)
    for i in range(0, len(arr)):
        for j in range(0, len(arr[i])):
            threshArr[i,j] = arr[i,j]
    
    # count the number of points and preallocate vectors
    numPoints = int(np.sum(threshArr))
    c2 = np.zeros(numPoints)
    r2 = np.zeros(numPoints)
    count = 0

    # list of all x's and y's
    for r in range(0, len(threshArr)):
        for c in range(0, len(threshArr[r])):
            if threshArr[r,c] == 1:
                r2[count] = r
                c2[count] = c
                count += 1
    
    # CHECK EACH POINT AND SORT INTO OBJECTS

    # start object list with one object
    tObjects = [thresholdObject(c2[0], r2[0])]

    # go through each image point
    for i in range(0, len(c2)):
        noMatch = True

        # go through each existing object
        o = 0
        while noMatch and o < len(tObjects):

            # check each point in the object until it finds a neighbor
            # or goes through all of them
            j = len(tObjects[o].xCoords)
            while noMatch and j > 0:

                # if it finds a neighbor, add it to the object
                if (abs(tObjects[o].xCoords[j] - c2[i]) <= 2
                        and abs(tObjects[o].yCoords[j] - r2[i]) <= 2):
                    tObjects[o].addPoint(c2[i], r2[i])
                    noMatch = False
                else:
                    # go to next point
                    j -= 1
            
            o += 1
        
        # if it goes through all objects without a match,
        # make a new object
        if noMatch:
            tObjects.append(thresholdObject(c2[i], r2[i]))

    # CONSOLIDATE OBJECTS

    # this needs to compare every point on an object with every other
    # point on other objects (not really EVERY point)

    # sort the objects array from most points to least
    tObjects = np.sort(tObjects[:,:,-1])

    # set startLength != len(tObjects) to enter the loop
    startLength = len(tObjects) + 1

    while startLength != len(tObjects):

        startLength = len(tObjects)

        o1 = 0
        while o1 < len(tObjects): # going through objects
            o2 = o1 + 1
            
            while o2 < len(tObjects): # comparing with other objects
                noMatch = True
                i = len(tObjects[o1].xCoords) # every point in o1

                while noMatch and i >= 0:
                    temp1 = tObjects[o2].xcoords
                    temp2 = tObjects[o2].ycoords
                    coordTrunc = ((abs(temp1-tObjects[o1].xCoords[i]) < 10)
                                * (abs(temp2-tObjects[o1].yCoords[i]) < 10))

                    if sum(coordTrunc) > 0:
                        # if any o1 points are within a radius of 10 of
                        # any o2 points, consolidate objects
                        # remove o2 from tObjects
                        noMatch = False
                        tObjects[o1].addPoints(temp1, temp2)
                        tObjects.pop(o2)
                    
                i -= 1
            o2 += 1
        o1 += 1
    
    # CENTER OF MASS OF EACH OBJECT
    for o in range(0, len(tObjects)):
        mass = 0
        xsum = 0
        ysum = 0
        for i in range(0, tObjects[o].numPoints):
            mass += imageArr(tObjects[o].yCoords[i], tObjects[o].xCoords[i])
            ysum += (imageArr(tObjects[o].yCoords[i], tObjects[o].xCoords[i])
                    * tObjects[o].yCoords[i])
            xsum += (imageArr(tObjects[o].yCoords[i], tObjects[o].xCoords[i])
                    * tObjects[o].xCoords[i])
        tObjects[o].com = [xsum/mass, ysum/mass]
    
    # FIND SPINDLE AUTOMATICALLY
    xcen = len(threshArr[0]) / 2
    ycen = len(threshArr) / 2

    if len(tObjects) > 1:
        avgObjectSize = np.mean([tObjects[:].numPoints])

        minDist = len(threshArr[0])
        for o in range(0, len(tObjects)):
            if np.linalg.norm(np.array([xcen, ycen]) - np.array([tObjects[o].com])) < minDist and tObjects[o].numPoints > avgObjectSize:
                minDist = np.linalg.norm(np.array([xcen, ycen]) - np.array([tObjects[o].com]))
                centerObj = o
        
        spindle = tObjects[centerObj]
    else:
        spindle = tObjects[0]
    
    # create array with only the spindle object
    spindleArr = np.zeros(threshArr.shape)
    for i in range(0, spindle.numPoints):
        spindleArr[spindle.yCoords[i], spindle.xCoords[i]] = 1
    
    # multiply original image by the one we just made
    spindleImg = imageArr * spindleArr

    return spindleImg

# a class to represent threshold objects
class thresholdObject():

    def __init__(self, x0, y0):

        self.xCoords = [x0]
        self.yCoords = [y0]
        self.numPoints = 1
        self.com = []

    def addPoint(self, xCoord, yCoord):
        self.xCoords.append(xCoord)
        self.yCoords.append(yCoord)
        self.numPoints += 1
    
    def addPoints(self, x2s, y2s):
        for x, y in x2s, y2s:
            self.addPoint(x, y)
