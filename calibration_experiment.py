# -*- coding: utf-8 -*-
"""
Created on Fri Jan 25 13:04:52 2019

@author: User1
"""
import numpy as np
import pandas as pd
import time
import datetime
import cv2
import os
from psychopy import visual, core, event, monitors
import random
from pepper_connector import socket_connection
from multiprocessing import Process, Manager
from threading import Thread


def getMac():
    from uuid import getnode as get_mac
    mac = ':'.join(['{:02x}'.format((get_mac() >> ele) & 0xff) for ele in range(0, 8 * 6, 8)][::-1])
    return mac


def isNumber(s):
    """
    Tests whether an input is a number

    Parameters
    ----------
    s : string or a number
        Any string or number which needs to be type-checked as a number

    Returns
    -------
    isNum : Bool
        Returns True if 's' can be converted to a float
        Returns False if converting 's' results in an error

    Examples
    --------
    >>> isNum = isNumber('5')
    >>> isNum
    True

    >>> isNum = isNumber('s')
    >>> isNum
    False
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


def drawText(win,
             text='No text specified!',
             textKey=['space'],
             wrapWidth=1800,
             textSize=100,
             textColor=[0, 0, 0]):
    """
    Draw a string on a psychopy window and waits for a keypress, always tries
    to draw the text in the center of the screen.

    Parameters
    ----------
    win : psychopy window
        An instance of an active psychopy window on which to draw the text
    text : string
        The text to draw
    textKey : list
        A list of the allowed keys to press to exit the function. The function
        will block code execution until the specified key or escape is pressed
    wrapWidth : int
        The number of characters to display per line. If there are more
        characters on one line than specified in wrapWith the text will
        continue on the next line
    textSize : int
        The height of the text in pixels
    textColor : list of [R,G,B] values
        The color in which to draw the text, [R,G,B]

    Returns
    -------
    key : string
        The key pressed
    rt : float
        The time from text display onset until keypress in seconds

    Examples
    --------
    >>> key, rt = pl.drawText(win, 'Press "Space" to continue!')
    >>> key
    'space'
    >>> rt
    1.2606524216243997
    """

    if np.sum(np.array(textColor) == 0) == 3 and np.sum(win.color < 100) == 3:
        textColor = [255, 255, 255]

    textDisp = visual.TextStim(win, text=text, wrapWidth=wrapWidth,
                               height=textSize, colorSpace='rgb255',
                               color=textColor, pos=(0, 0))
    textDisp.draw()
    time = core.Clock()
    win.flip()
    if isNumber(textKey[0]):
        core.wait(textKey[0])
        key = ['NoKey']
    else:
        key = getKey(textKey)
    rt = time.getTime()
    return key[0], rt


def getKey(allowedKeys=['left', 'right'], waitForKey=True, timeOut=0):
    """
    Gets a keypress by using the event.waitKeys or event.getKeys from
    the psychopy module

    The escape key is always allowed.

    Parameters
    ----------
    allowedKeys : list, list fo strings
        The list should contain all allowed keys
    waitForKey : Bool
        If True, the code waits until one of the keys defined in allowedkeys
        or escape has been pressed
    timeOut : int or float, positive value
        Only has effect if waitForKey == True\n
        If set to 0, the function waits until an allowed key is pressed\n
        If set to any other positive value, breaks after timeOut seconds

    Returns
    -------
    key_pressed : tuple with two items
        The first index returns the Key\n
        The second index returns the timestamp\n
        The timestamp is in seconds after psychopy initialization and does not
        reflect the duration waited for the key press\n
        If timeOut or no key is pressed, returns ['NoKey', 9999]

    Note
    --------
    The function requires an active psychopy window

    Examples
    --------
    >>> key = getKey(allowedKeys = ['left', 'right'], waitForKey = True, timeOut = 0)
    >>> key # the 'left' key is pressed after 156 seconds'
    ('left', 156.5626505338878)
    """
    if waitForKey:
        while True:
            # Get key
            if timeOut > 0:
                key_pressed = event.waitKeys(maxWait=timeOut, timeStamped=True)
                if key_pressed is None:
                    key_pressed = [['NoKey', 9999]]
                    break
            else:
                key_pressed = event.waitKeys(maxWait=float('inf'), timeStamped=True)
            # Check last key
            if key_pressed[-1][0] == 'escape':
                break
            if key_pressed[-1][0] in allowedKeys:
                break

    else:
        # Get key
        key_pressed = event.getKeys(allowedKeys, timeStamped=True)
        if not key_pressed:
            key_pressed = [['NoKey', 9999]]

    return key_pressed[-1]


def makeSquareGrid(x=0, y=0, grid_dimXY=[10, 10], line_lengthXY=[10, 10]):
    """
    Creates the coordinates for a square grid.

    Parameters
    ----------
    x : float or int
        The center x position of the grid
    y : float or int
        The center y position of the grid
    grid_dimXY : list, positive integers
        The size of the grid, e.g. the number of points in each direction
    line_lengthXY : list, positive floats or ints
        The length between each grid intersection, [width, height]

    Returns
    -------
    gridpositions : list of tuples
        Each tuple contains the (x,y) position of one of the grid intersections

    Examples
    --------
    >>> gridpositions = makeSquareGrid(0,0,[4,4],[10,10])
    >>> gridpositions
    [(-15.0, -15.0),
     (-15.0, -5.0),
     (-15.0, 5.0),
     (-15.0, 15.0),
     (-5.0, -15.0),
     (-5.0, -5.0),
     (-5.0, 5.0),
     (-5.0, 15.0),
     (5.0, -15.0),
     (5.0, -5.0),
     (5.0, 5.0),
     (5.0, 15.0),
     (15.0, -15.0),
     (15.0, -5.0),
     (15.0, 5.0),
     (15.0, 15.0)]

    """
    # Left starting position
    start_x = x - 0.5 * grid_dimXY[0] * line_lengthXY[0] + 0.5 * line_lengthXY[0]
    # Top starting position
    start_y = y - 0.5 * grid_dimXY[1] * line_lengthXY[1] + 0.5 * line_lengthXY[1]
    # For loops for making grid
    gridpositions = []
    for x_count in range(0, grid_dimXY[0]):
        current_x = start_x + x_count * line_lengthXY[0]
        for y_count in range(0, grid_dimXY[1]):
            current_y = start_y + y_count * line_lengthXY[1]
            gridpositions.append((current_x, current_y))
    return gridpositions


def drawDots(point, rad, col, OuterDot, InnerDot):
    OuterDot.fillColor = col
    OuterDot.pos = point
    OuterDot.radius = rad
    OuterDot.draw()
    InnerDot.pos = point
    InnerDot.draw()

def drawArrow(point, lr='left', col=[0, 0, 0], arrowLineW = 0, arrowLine = None, arrowHead = None):
    if lr == "left":
        arrowPoint = [point[0] - (arrowLineW / 2), point[1]]
        ori = 270
    elif lr == 'right':
        arrowPoint = [point[0] + (arrowLineW / 2), point[1]]
        ori = 90
    arrowLine.fillColor = col
    arrowLine.pos = point
    arrowLine.draw()
    arrowHead.fillColor = col
    arrowHead.pos = arrowPoint
    arrowHead.ori = ori
    arrowHead.draw()


def calibration(win, fileName, calibration, pc='default', nrPoints=15, dotColor=[255, 255, 255], ip="192.168.0.167", port= 12345, camera = 4):
    """
    Custom calibration using psychoLink. It uses the background
    color which is set in win. Flips the screen empty before returning.

    Parameters
    ----------
    win : psychopy window
        An instance of an active psychopy window on which to draw the text
    nrPoints : int
        The number of calibration points to use, allowed input:\n
        9,13,15 or 25
    dotColor : list, [R,G,B]
        The RGB color of the validation dot

    Returns
    -------
    gridPoints : 2d np.array (col 1 x positions, col2 y positions)


    Examples
    --------

    """
    # Get required information from the supplied window
    xSize, ySize = win.size
    bgColor = list(win.color)
    arrowColor = [255, 255, 255]
    escapeKey = ['None']
    sampDur = 2000
    textColor = [255, 0, 0]
    waitForSacc = 1
    radStep = 0.75
    stepDir = -radStep
    dotRad = xSize / 75
    maxDotRad = xSize / 60
    minDotRad = xSize / 300
    nFramesPerDot = 5
    nRandDots = 60
    arrowLineW = xSize / 60
    leftRight = ['left', 'right']
    totalDots = nrPoints + nRandDots
    nFrames = totalDots * nFramesPerDot
    cols = ['frameNr', 'x', 'y', 'dotNr', 'arrowOri', 'Resp', 'corrResp', 'fName', 'sampTime']  # for pandas dataframe
    headerInfo = pd.DataFrame([], columns=cols)
    headerInfo['pc'] = pc
    headerInfo['resX'] = xSize
    headerInfo['resY'] = ySize
    # calDotNr = np.zeros(nFrames)

    if np.sum(np.array(textColor) == 0) == 3 and np.sum(win.color < 100) == 3:
        textColor = [255, 255, 255]
    if np.sum(np.array(dotColor) == 0) == 3 and np.sum(win.color < 100) == 3:
        dotColor = [255, 255, 255]

    # Initiate Dots (inner and outer dot for better fixation)
    OuterDot = visual.Circle(win,
                             radius=10,
                             lineWidth=1,
                             fillColorSpace='rgb255',
                             lineColorSpace='rgb255',
                             lineColor=bgColor,
                             fillColor=dotColor,
                             edges=40,
                             pos=[0, 0])

    InnerDot = visual.Circle(win,
                             radius=xSize / 500,
                             lineWidth=1,
                             fillColorSpace='rgb255',
                             lineColorSpace='rgb255',
                             lineColor=bgColor,
                             fillColor=bgColor,
                             edges=40,
                             pos=[0, 0])

    arrowLine = visual.Rect(win,
                            width=arrowLineW,
                            height=arrowLineW / 5,
                            fillColorSpace='rgb255',
                            lineColorSpace='rgb255',
                            lineColor=arrowColor,
                            fillColor=arrowColor,
                            lineWidth=0,
                            pos=[0, 0])

    arrowHead = visual.Polygon(win,
                               radius=arrowLineW / 2,
                               fillColorSpace='rgb255',
                               lineColorSpace='rgb255',
                               lineColor=arrowColor,
                               fillColor=arrowColor,
                               lineWidth=0,
                               pos=[0, 0])


    # Make the grid depending on the number of points for calibration
    if nrPoints == 9:
        xlineLength = (xSize - xSize / 13) / 2
        yLineLength = (ySize - ySize / 13) / 2
        gridPoints = makeSquareGrid(0, 0, [3, 3], [xlineLength, yLineLength])

    elif nrPoints == 12:
        xlineLength = (xSize - xSize / 10) / 3
        yLineLength = (ySize - ySize / 10) / 2
        gridPoints = makeSquareGrid(0, 0, [4, 3], [xlineLength, yLineLength])
    elif nrPoints == 15:
        xlineLength = (xSize - xSize / 25) / 4
        yLineLength = (ySize - ySize / 15) / 2
        gridPoints = makeSquareGrid(0, 0, [5, 3], [xlineLength, yLineLength])
    else:
        drawText(win, 'Incorrect number of validation points,\n please try again with a different number', 3)
        win.flip()
        return headerInfo

    # training for 1 position
    gridPoints = [i for i in gridPoints]
    connect = socket_connection(ip=ip, port=port, camera=camera)
    connect.adjust_head(-0.3, 0)
    fCount = 0
    #
    # Draw the first fixation dot and wait for spacepress to start validation
    startKey = \
    drawText(win, textSize=xSize / 40, text='Training! \n 30 dots will appear on the screen,'
                                                'one after the other in random order [space]', textKey=['space', 'escape'])[0]

    drawText(win, textSize=xSize / 40, text=' You must look at them and select the correct arrow direction  [space]',
             textKey=['space', 'escape'])[0]

    drawText(win, textSize=xSize / 30,
             text='Stand at the position #1 and press [space] to start the training ',
             textKey=['space', 'escape'])[0]
    drawDots((0, 0), dotRad, dotColor, OuterDot, InnerDot)
    win.flip()
    time.sleep(sampDur / 1000.)
    if startKey[0] == 'escape':
        escapeKey[0] = 'escape'
        return headerInfo

    # shuffle points
    for el in range(0, nrPoints):
        a = gridPoints[nrPoints * el: nrPoints * el + nrPoints - 1]
        random.shuffle(a)
        gridPoints[nrPoints * el: nrPoints * el + nrPoints - 1] = a

    for i in range(0, len(gridPoints)):
        s = time.time()
        curFCount = 0
        dotRadius = dotRad

        # Draw arrow and wait for responsse
        lr = np.random.choice(2)
        respIdxStart = fCount

        while True:
            if dotRadius > maxDotRad:
                stepDir = -radStep
            elif dotRadius < minDotRad:
                stepDir = radStep
            dotRadius += stepDir
            drawDots(gridPoints[i], dotRadius, dotColor, OuterDot, InnerDot)
            sampTime = win.flip()
            if (time.time() - s) > waitForSacc:
                # Increase frame counters
                img = connect.get_img()
                fCount += 1
                curFCount += 1

            # Go to next dot after nFramesPerDot
            if curFCount >= nFramesPerDot:
                break

        # Check abort
        escapeKey = getKey(['escape'], waitForKey=False)
        if escapeKey[0] == 'escape':
            exit()

        # Draw arrow and get response
        respIdxEnd = fCount - 1
        drawArrow(gridPoints[i], leftRight[lr], arrowLineW = arrowLineW, arrowLine = arrowLine, arrowHead = arrowHead)
        win.flip()
        time.sleep(0.150)
        win.flip()
        resp = getKey(timeOut=1)[0]
        headerInfo.loc[respIdxStart:respIdxEnd, 'Resp'] = resp
        if leftRight[lr] == resp:
            headerInfo.loc[respIdxStart:respIdxEnd, 'corrResp'] = True
            drawArrow(gridPoints[i], leftRight[lr], [0, 255, 0], arrowLineW, arrowLine, arrowHead)
        else:
            headerInfo.loc[respIdxStart:respIdxEnd, 'corrResp'] = False
            drawArrow(gridPoints[i], leftRight[lr], [255, 0, 0], arrowLineW, arrowLine, arrowHead)

        # Draw response
        win.flip()
        time.sleep(0.25)
        win.flip()

        # Break between blocks
        if (i + 1) % (nrPoints * 2) == 0 and i != len(gridPoints):
            pos = int((i + 1) / (nrPoints * 2)) + 1
            text = 'break! Go to position: ', str(pos), ' \n\nPress space to continue'
            drawText(win, textSize=xSize / 30,
                     text='break! Go to position: ' + str(pos) + ' \n\nPress space to continue')
            win.flip()
            time.sleep(0.5)
    drawText(win, textSize=xSize / 30,
             text='Good job :) !!  Your training is finished... \n Now you are ready to start the experiment \n\n Press space to start')
    win.flip()


    # Experiment
    gridPoints = [i for i in gridPoints * 2 * 9]
    # connect = socket_connection(ip=ip, port=port, camera=camera)
    # connect.adjust_head(-0.3, 0)

    # connect.adjust_head(0.2, 0)
    # print("connection established")

    # Draw the first fixation dot and wait for spacepress to start validation
    startKey = \
    drawText(win, textSize=xSize / 30, text='Press space to start calibration!', textKey=['space', 'escape'])[0]
    drawDots((0, 0), dotRad, dotColor, OuterDot, InnerDot)
    win.flip()
    time.sleep(sampDur / 1000.)
    if startKey[0] == 'escape':
        escapeKey[0] = 'escape'
        return headerInfo

    # Draw the Dots dot and wait for 1 second between each dot
    fCount = 0

    # shuffle points
    for el in range(0, nrPoints):
        a = gridPoints[nrPoints * el: nrPoints * el + nrPoints - 1]
        random.shuffle(a)
        gridPoints[nrPoints * el: nrPoints * el + nrPoints - 1] = a

    for i in range(0, len(gridPoints)):
        s = time.time()
        curFCount = 0
        dotRadius = dotRad

        # Draw arrow and wait for responsse
        lr = np.random.choice(2)
        respIdxStart = fCount

        while True:
            if dotRadius > maxDotRad:
                stepDir = -radStep
            elif dotRadius < minDotRad:
                stepDir = radStep
            dotRadius += stepDir
            drawDots(gridPoints[i], dotRadius, dotColor, OuterDot, InnerDot)
            sampTime = win.flip()
            if (time.time() - s) > waitForSacc:
                # Get video image
                fName = fileName + '%05d.jpg' % (fCount + 1)
                # print('store frame')
                # print('fName', fName)
                # print('calibration', calibration)
                img = connect.get_img()
                cv2.imwrite(calibration + '\\' + fName, img)
                # cv2.imwrite(calibration + '\\' + fName, getFrame())
                headerInfo.loc[fCount, 'x'] = gridPoints[i][0]
                headerInfo.loc[fCount, 'y'] = gridPoints[i][1]
                headerInfo.loc[fCount, 'dotNr'] = i
                headerInfo.loc[fCount, 'arrowOri'] = leftRight[lr]
                print(fName)
                headerInfo.loc[fCount, 'fName'] = fName
                headerInfo.loc[fCount, 'sampTime'] = sampTime

                # Increase frame counters
                fCount += 1
                curFCount += 1

            # Go to next dot after nFramesPerDot
            if curFCount >= nFramesPerDot:
                break

        # Check abort
        escapeKey = getKey(['escape'], waitForKey=False)
        if escapeKey[0] == 'escape':
            exit()

        # Draw arrow and get response
        respIdxEnd = fCount - 1
        drawArrow(gridPoints[i], leftRight[lr], arrowLineW=arrowLineW, arrowLine = arrowLine, arrowHead=arrowHead)
        win.flip()
        time.sleep(0.150)
        win.flip()
        resp = getKey(timeOut=1)[0]
        headerInfo.loc[respIdxStart:respIdxEnd, 'Resp'] = resp
        if leftRight[lr] == resp:
            headerInfo.loc[respIdxStart:respIdxEnd, 'corrResp'] = True
            drawArrow(gridPoints[i], leftRight[lr], [0, 255, 0], arrowLineW=arrowLineW, arrowLine = arrowLine, arrowHead=arrowHead)
        else:
            headerInfo.loc[respIdxStart:respIdxEnd, 'corrResp'] = False
            drawArrow(gridPoints[i], leftRight[lr], [255, 0, 0], arrowLineW=arrowLineW, arrowLine = arrowLine, arrowHead=arrowHead)

        # Draw response
        win.flip()
        time.sleep(0.25)
        win.flip()

        # Break between blocks
        if (i + 1) % (nrPoints * 2) == 0 and i - 1 != len(gridPoints):
            pos = int((i + 1) / (nrPoints * 2)) + 1
            text = 'break! Go to position: ', str(pos), ' \n\nPress space to continue'
            if pos!= 10:
                drawText(win, textSize=xSize / 30,
                     text='break! Go to position: ' + str(pos) + ' \n\nPress space to continue')
            if pos==4:
                connect.adjust_head(0.2,0)
            if pos == 7:
                connect.adjust_head(0.1, 0)
            win.flip()
            time.sleep(0.5)
    drawText(win, textSize=xSize / 30,
             text='Thanks for your attention :) !!  The experiment is ended. \n Now you can take a break and ask any question you want')
    win.flip()
    return headerInfo



def getFrame():
    return video_capture.read()[1]


def dispCalVid(loc, f, fps=33):
    data = pd.read_pickle(loc + '\\' + f)
    try:
        for i in range(len(data)):
            frame = cv2.imread(loc + '\\' + data['fName'][i])
            cv2.putText(frame, 'CalDot: ' + str(int(data['dotNr'][i])), (0, 25), 0, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.imshow('Calibration', frame)
            cv2.waitKey(int(1000 / fps))
    except:
        pass


def getFileName(ppNr):
    participant = 'PP%03d' % ppNr
    # Check for existing files
    if not os.path.exists(participant):
        os.mkdir(participant)
    else:
        it = 1
        newDir = participant
        while os.path.exists(newDir):
            newDir = participant + '_%03d' % it
            it += 1
            if it > 100:
                break
        participant = newDir
        os.mkdir(newDir)
    return participant


def getFileName2():
    now = datetime.datetime.now()
    identifier = np.random.randint(0, 99999999)
    participant = '{}_{}_{}_{}_{}_{}_{:08d}'.format(now.year, now.month,
                                                    now.day, now.hour, now.minute, now.second, identifier)
    # Check for existing files
    if not os.path.exists(participant):
        os.mkdir(participant)
    else:
        it = 1
        newDir = participant
        while os.path.exists(newDir):
            identifier = np.random.randint(0, 99999999)
            newDir = '{}_{}_{}_{}_{}_{}_{:08d}'.format(now.year, now.month,
                                                       now.day, now.hour, now.minute, now.second, identifier)
            it += 1
            if it > 100:
                break
        participant = newDir
        os.mkdir(participant)
    return participant




if __name__ == '__main__':

    # ==============================================================================
    # Settings
    # ==============================================================================
    pc = 'Jonathan_Desktop_mac:{}'.format(getMac())
    # screenRes = (1536, 864)
    bgColor = (0, 0, 0)
    screenNr = 0


    fullScreen = True
    # Get correct file names
    participant = getFileName2()
    fileName = '{}_'.format(participant)

    ip = "10.15.3.25"
    port = 12345
    camera = 4  # [ 3: red_id=1, cam_id=0 res=(320,240)  ||  4: red_id=2, cam_id=0 res=(640,480) ]

    # ==============================================================================
    # Initiate webcam
    # ==============================================================================
    faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')
    video_capture = cv2.VideoCapture(0)

    # ==============================================================================
    # Initiate psychopy
    # ==============================================================================
    # mon = monitors.Monitor('testMonitor', width=47,distance=75)
    mon = monitors.getAllMonitors()[0]
    # print('mon', mon)
    # exit()
    # print('size', monitors.Monitor(mon).getSizePix())

    win = visual.Window(pos=(0, 0), units='pix', monitor=mon, size=monitors.Monitor(mon).getSizePix(),
                        colorSpace='rgb255',
                        color=bgColor, screen=screenNr, fullscr=fullScreen,
                        gammaErrorPolicy="ignore")

    # for mon in monitors.getAllMonitors():
    #     print(mon, monitors.Monitor(mon).getSizePix())
    #
    # print("monitor size: ", win.monitor.getSizePix())

    mouse = event.Mouse(win=win)
    mouse.setVisible(0)
    # ==============================================================================
    # Run calibration
    # ==============================================================================
    dataframe = calibration(win, fileName, participant, pc, ip=ip, port=port, camera=camera)
    mouse.setVisible(2)
    win.close()

    # ==============================================================================
    # Save data
    # ========================================================================== ====
    dataframe.to_pickle(participant + '\\' + fileName + 'Header.p')
    dataframe.to_csv(participant + '\\' + fileName + 'Header.csv', index=False)

    ##==============================================================================
    # Clean up
    ##==============================================================================
    video_capture.release()
    cv2.destroyAllWindows()

    # ==============================================================================
    # Display video
    # ==============================================================================
    # dispCalVid(participant,fileName+'Header.p')
    # cv2.destroyAllWindows()