#!/usr/bin/env python3
"""experiment controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot, Camera, Supervisor, Display, MouseState, Mouse
import numpy as np
import cv2
import random
import os
import ikpy
import math
from ikpy.chain import Chain


random.seed(10)


can_num = 0
pos_choice = "000"


reason_dict = { 'colorError' : "Can't sort color", 
                'graspError': "Unable to grasp", 
                'proximityError': "Can't reach in time"}

# 50-33 takes 100sec
max_cans = 20  # 20 is doable with 50 freq
freq = 20  # Less is more - 50 is doable

###########################################################################
###########################  Utility functions  ###########################

## Only used to change the proto files
# from pyutil import filereplace
# def fileChanger(textToSearch, textToReplace):
#     for file in os.listdir("resources"):
#         f = "resources/" + file
#         filereplace(f, textToSearch, textToReplace)

# fileChanger("mass 0.0001", "mass 0.1")


def displayScore(display, correct, incorrect, missed):
    h = int(display.getHeight() / 6)
    w = int(display.getWidth() / 2)
    marginW = int(display.getWidth()*0.05)
    marginH = int(display.getHeight()*0.05)
    x = h + marginH
    robot_correct, robot_incorrect = 0, 0

    display.setOpacity(1)
    display.setAlpha(1)
    display.fillRectangle(0, 0, display.getWidth(), display.getHeight())
    display.setAlpha(1)
    display.setColor(0xFF0000)
    display.setFont("Lucida Console", 64, True)
    display.drawText("Game Over!", 300, marginH)
    display.setFont("Lucida Console", 32, True)
    display.setColor(0x000000)
    display.drawText("User score:   Robot score:".format(correct), w-200, x)
    x += h
    display.drawText("Correct:         {}             {}".format(correct, robot_correct), marginW, x)
    x += h
    display.drawText("Incorrect:       {}             {}".format(incorrect, robot_incorrect), marginW, x)
    x += h
    display.fillRectangle(marginW, int(x-h/2), int(2*w-2*marginW), int(h/20))
    display.drawText("Missed: {}".format(missed), marginW, x)
    x += h
    display.setFont("Lucida Console", 48, True)
    display.drawText("Total score:     {}".format(correct-incorrect-missed), marginW, x)


def countCans(missed, total_cans):
    toRemove = []
    root_children_n = root_children.getCount()
    for n in range(root_children_n):
        if "CAN" in root_children.getMFNode(n).getDef():
            can = root_children.getMFNode(n)
            can_id = can.getId()
            x, y, z = can.getField("translation").getSFVec3f()
            # If we already have the can, check if it should be removed
            if can_id in list(total_cans.keys()):
                if x < -1:# and y >= 0.8:
                    missed += 1
                    toRemove.append(can)
                    del total_cans[can_id]
                elif z > 0.6 or z < 0.4:
                    del total_cans[can_id]
            # If the can is not in the list yet, we should add it
            else:
                if y >= 0.8:
                    trueColor = can.getDef().split('_')[0].lower()
                    total_cans[can_id] = []
                    total_cans[can_id].append(trueColor)
                    if random.random() <= 0.7:
                        total_cans[can_id].append(trueColor)
                    else:
                        options = ["yellow", "red", "green"]
                        options.remove(trueColor)
                        total_cans[can_id].append(random.choice(options))
                        #total_cans.append(can.getId())
    for item in toRemove:
        item.remove()

    for keys, vals in candidates.items():
      print (keys, vals)
    print("------------------------------------")
    #print(can_num)
    return total_cans, missed


def onConveyorRanked(cans):
    """
    Returns a ranked list of the cans that are on the conveyor belt
    """
    cansOnConveyor = cans[:]
    for canID in cans:  
        canX, canY, _ = supervisor.getFromId(canID).getField("translation").getSFVec3f()
        if canY <= 0.8 or canID == supervisor.getSelected().getId():
            cansOnConveyor.remove(canID)
    return cansOnConveyor


def drawImage(camera, colors, candidates):
    """
    Displays the image either in a new window, or on the Display
    """
    global crate_pos_img
    cameraData = camera.getImage()
    image = np.frombuffer(cameraData, np.uint8).reshape((camera.getHeight(), camera.getWidth(), 4))

    for obj in camera.getRecognitionObjects():
        # Get the id of the object
        obj_id = obj.get_id()
        if obj_id not in candidates.keys():
            #print(supervisor.getFromId(obj_id).getDef(), obj.get_position_on_image())
            continue
        reason = candidates[obj_id][2]
        # Check if the object is on the conveyor or not
        _, _, obj_z = supervisor.getFromId(obj_id).getField("translation").getSFVec3f()
        if obj_z > 0.6 or obj_z < 0.4 or reason == "":
            continue 
        # Assign color
        perceivedColor = candidates[obj_id][0][1]
        color = colors[perceivedColor] if reason != "graspError" else colors[candidates[obj_id][0][0]]
        #If the error is "graspError" and the trueColor != original
        #print(color)
        color = np.rint(np.array(color)*255)
        size = np.array(obj.get_size_on_image()) + padding
        start_point = np.array(obj.get_position_on_image()) - (size / 2) 
        start_point =  np.array([int(n) for n in start_point])
        end_point = start_point + size
        #color = np.rint(np.array(obj.get_colors())*255)
        thickness = 2
        #color = [0, 255, 0]

        color = ( int (color [ 0 ]), int (color [ 1 ]), int (color [ 2 ]))
        font = cv2.FONT_HERSHEY_SIMPLEX
        if reason.isdigit():
            image = cv2.rectangle(image, tuple(start_point), tuple(end_point), tuple(color), thickness)
            end_point = crate_pos_img["GREEN_ROBOT_CRATE"] if perceivedColor == "green" else crate_pos_img["RED_ROBOT_CRATE"]
            print(perceivedColor)
            start_point = np.array([int(n) for n in obj.get_position_on_image()])
            image = cv2.arrowedLine(image, tuple(start_point), tuple(end_point), tuple(color), thickness)
            start_point[1] -= 20
            text = reason
        if reason in list(reason_dict.keys()):
            text = reason_dict[reason]
        cv2.putText(image, text, tuple(start_point), font, 1, tuple(color), 2)


    if cameraData:
        # Displaying the camera image directly
        #ir = display_score.imageNew(cameraData, Display.BGRA, camera.getWidth(), camera.getHeight())
        # Displaying the processed image
        cv2.imwrite('tmp.jpg', image)
        ir = display_explanation.imageLoad('tmp.jpg')
        display_explanation.imagePaste(ir, 0, 0, False)
        display_explanation.imageDelete(ir)
    #imageRef = display.imageNew(cameraData, Display.ARGB, camera.getHeight(), camera.getWidth())
    #display.imagePaste(imageRef, 1024, 768)        
    #cv2.imshow("preview", image)
    #cv2.waitKey(timestep)


def generateCans():
    global can_num, pos_choice 
    can_num += 1
    #can_distances = ["000", "999", "555", "535", "515", "495", "475", "455"]
    can_distances = ["000", "999", "556", "479", "506", "490", "530"]
    can_distances.remove(pos_choice)
    can_colors = ["green", "yellow", "red"]
    pos_choice = random.choice(can_distances)
    can = "resources/" + random.choice(can_colors) + "_can_" + pos_choice + ".wbo"
    root_children.importMFNode(-1, can)


def endGame():
    [supervisor.step(64) for x in range(10)]
    displayScore(display_explanation, correctSort, wrongSort, missed)
    supervisor.step(64)
    supervisor.simulationSetMode(0)

def setPoseRobot():
    motors[1].setPosition(-0.44509)
    motors[2].setPosition(0)
    motors[3].setPosition(-1.12585)
    motors[4].setPosition(-1.5708)
    motors[5].setPosition(0)
    for key, val in candidates.items():
        if val[2] == '1':
            position_of_can = val[1]
            print(math.radians(math.acos(position_of_can[2])))
            motors[0].setPosition(math.acos(position_of_can[2]))


def moveFingers(fingers, mode="open"):

    if mode == "open":
        fingers[0].setPosition(0.04)
        fingers[1].setPosition(0.04)
    elif mode == "close":
        fingers[0].setPosition(0)
        fingers[1].setPosition(0)


def getFirstCan(candidates):
    for key, val in candidates.items():
        if val[2] == '1':
            return key


def pickTargets(total_cans, choices=5, min_dist = 0.5):
    """
    Gets five targets based on 3 criteria (assessing each can):
    1. Right color
    2. Furthest on the conveyor belt
    3. Right pose (graspable)
    4. Closeness to other candidate (can't make it in time)

    Returns:
        A dictionary with the IDs, where each ID contains:
            1. Perceived colour of the can
            2. Position of the can
            3. Additional text (explanation - if applicable)
    """

    # Check if yellow or green
    candidates = {}
    top5_dists = []
    top5_keys = []
    for key, val in total_cans.items():
        reason = ""
        candidates[key] = [val]
        candidates[key].append(supervisor.getFromId(key).getField("translation").getSFVec3f())
        if candidates[key][1][0] > 0.5:
            if val[1] in ["green", "red"]:
                if abs(supervisor.getFromId(key).getField("rotation").getSFRotation()[3]) > 0.3:
                    reason += "graspError"
                else:
                    top5_keys.append(key)
                    top5_dists.append(candidates[key][1][0])
            else:
                reason += "colorError"

        candidates[key].append(reason)
    #top_choices = sorted(zip(top5_dists, top5_keys), key=lambda x: x[1])[:choices]

    sorted_cans = sorted(zip(top5_dists, top5_keys), key=lambda x: x[1])
    
    top_choices = []

    for i in range(len(sorted_cans)):
        # we take the first one and last one always
        if i == 0:
            top_choices.append(sorted_cans[i])
        # Check distance to next can
        else:
            if abs(top_choices[-1][0] - sorted_cans[i][0]) <= min_dist:
                candidates[sorted_cans[i][1]][2] = "proximityError"
            else:
                top_choices.append(sorted_cans[i])
        if len(top_choices) == choices:
            break
    for i in range(len(top_choices)):
        candidates[top_choices[i][1]][2] = str(i+1)

    return candidates


def position_Checker():
    """
    Returns true if all joints are 0.02 rad within the desired angles
    """
    return all([abs(sensors[i].getValue() - joints[i+1]) < 0.02 for i in range(len(sensors))])


def tryGetCratePos():
    global crate_pos_img
    for obj in camera.getRecognitionObjects():
        obj_name = supervisor.getFromId(obj.get_id()).getDef()
        if obj_name == "RED_ROBOT_CRATE":
            crate_pos_img["RED_ROBOT_CRATE"] = obj.get_position_on_image()
        elif obj_name == "GREEN_ROBOT_CRATE":
            crate_pos_img["GREEN_ROBOT_CRATE"] = obj.get_position_on_image()
    #print("Trying")


###########################################################################
###########################  Global variables   ###########################

y = 0.88
x = 3.17


cam = True

supervisor = Supervisor()
robot = supervisor.getFromDef("UR3")

timestep = int(supervisor.getBasicTimeStep())

padding = np.array([10, 10])
camera = Camera("camera")
camera.enable(timestep)
camera.recognitionEnable(timestep)

display_explanation = supervisor.getDevice("display_explanation")

width = camera.getWidth()
height = camera.getHeight()

colors = {"yellow" : [0.309804, 0.913725, 1.0], "red" : [0.0, 0.0, 1.0], "green" : [0.0, 1.0, 0.0]}



selection = None
prevSelection = None
canSelection = None
can_height = 0.85
selectionName = None
canSelectionName = None

total_cans = {}
# Crate position on the recognition image
crate_pos_img = {"RED_ROBOT_CRATE" : [], "GREEN_ROBOT_CRATE" : []}

missed = 0
correctSort = 0
wrongSort = 0

joint_names = ['shoulder_pan_joint',
                'shoulder_lift_joint',
                'elbow_joint',
                'wrist_1_joint',
                'wrist_2_joint',
                'wrist_3_joint']
        
finger_names = ['right_finger', 'left_finger']                
motors = [0] * len(joint_names)
sensors = [0] * len(joint_names)
fingers = [0] * len(finger_names)
sensor_fingers = [0] * len(finger_names)

for i in range(len(joint_names)):  
    motors[i] = supervisor.getDevice(joint_names[i])   
    
    sensors[i] = supervisor.getDevice(joint_names[i] + '_sensor')
    sensors[i].enable(timestep)
    #motors[i].setPosition(float('inf'))
    motors[i].setVelocity(3.14)                
motors[0].setVelocity(1.5)         
for i in range(len(finger_names)):  
    fingers[i] = supervisor.getDevice(finger_names[i])
    sensor_fingers[i] = supervisor.getDevice(finger_names[i] + '_sensor')
    sensor_fingers[i].enable(timestep)

distance_sensor = supervisor.getDevice("distance_sensor1") 
distance_sensor.enable(timestep)  

my_chain = ikpy.chain.Chain.from_urdf_file("resources/robot2.urdf")      


prepare_grasp = True
go_to_bucket = False
prepare_grap2 = False
go_to_bucket2 = False
drop = False

candidates = {}

moveFingers(fingers) 


root_children = supervisor.getRoot().getField("children")

################################################################
#######################  Main Loop   ###########################

while supervisor.step(timestep) != -1:
    if not bool(crate_pos_img["GREEN_ROBOT_CRATE"]): tryGetCratePos()
    total_cans, missed = countCans(missed, total_cans)
    candidates = pickTargets(total_cans, 3)
    #print(total_cans)
    selection = supervisor.getSelected()
    selectionName = selection.getDef() if selection else ""
    selectionColor = selectionName.split('_')[0]

    # for keys, vals in total_cans.items():
    #     print (keys, vals)
    if "CAN" in selectionName:
        canSelection = selection
        canColor = selectionColor
        
    elif ("CRATE" in selectionName) and canSelection:
        new_position = selection.getField("translation").getSFVec3f()
        new_position[1] = can_height
        canSelection.getField("translation").setSFVec3f(new_position)
        if selectionColor == canColor: correctSort += 1
        else: wrongSort += 1 
        del total_cans[canSelection.getId()]
        canSelection = None

    # Check for missed ones:
    for canID in total_cans:  
        canX, _, _ = supervisor.getFromId(canID).getField("translation").getSFVec3f()
        if canX < -1.5:
            missed += 1

    prevSelection = selection
    
    if random.randrange(0,100) % freq == 0:
        if can_num < max_cans:
            generateCans()
            #supervisor.getFromDef("PHYSICS").getField("mass").setSFFloat(0.1)
        #pass
    #print("Correct: {}\t Incorrect: {}\t Missed: {}\t Total: {}".format(correctSort, wrongSort, missed, correctSort-wrongSort-missed))
    #print(onConveyorRanked(total_cans))
    if cam: drawImage(camera, colors, candidates)
    if can_num >= max_cans and not bool(total_cans):
        endGame()

    # if prepare_grasp == True and bool(total_cans):

    #      index = getFirstCan(candidates) #####SETTING THE CAN, CAN BE REPALCED BY AN ACTUAL ID#####
    #      goal = supervisor.getFromId(index).getField("translation")
    #      target = np.array(goal.getSFVec3f())
         
         
         
    #      setPoseRobot()
         
    #      #target_position = [target[2], 0.167, target[1]-0.48]
    #      #target_position = [target[2], 0.167, target[1]]
    
    #      #orientation_axis = "Y"
    #      #target_orientation = [0, 0, -1]
        
    #      #joints = my_chain.inverse_kinematics(target_position, target_orientation=target_orientation, orientation_mode=orientation_axis)
        
    #      #for i in range(len(joint_names)):
    #      #    motors[i].setPosition(joints[i+1])    
    #      #print(joints)
    #      #prepare_grasp = not position_Checker()
    #      #print(distance_sensor.getValue())
    #      prepare_grasp = False

    # if  prepare_grasp == False and distance_sensor.getValue() < 800 and target[0] < 0.19 :
         
    #      for i in range(len(joint_names)):
    #          motors[1].setPosition(0.15)    
       
    #      prepare_grap2 = True        

    # if  prepare_grap2 == True and distance_sensor.getValue() < 200:
        
    #      motors[1].setPosition(sensors[1].getValue())

    #      moveFingers(fingers, "close")

    #      go_to_bucket = True        
    #      prepare_grap2 = False

    # if  go_to_bucket == True and go_to_bucket2 == False and sensor_fingers[0].getValue() < 0.012 or sensor_fingers[1].getValue() < 0.012:

    #      for i in range(len(joint_names)):
    #              motors[1].setPosition(-1)
         
    # if go_to_bucket == True and go_to_bucket2 == False and sensors[1].getValue()-0.2 < -1 < sensors[1].getValue()+0.2:
    #              go_to_bucket2 = True    
    #              go_to_bucket = False
    
    
    
    # if go_to_bucket2 == True:
    #       print(index)
    #       go_to_bucket2 = False     
    #       if total_cans[index] == "green":
    #           for i in range(len(joint_names)):
    #                   motors[0].setPosition(1.5)
    #                   drop = True

    #       elif total_cans[index] == "red":
    #           for i in range(len(joint_names)):
    #                   motors[0].setPosition(-1.8)
    #                   drop = True

    
         
    # if  drop == True and sensors[0].getValue()-0.01 < 1.5 < sensors[0].getValue()+0.01 or sensors[0].getValue()-0.01 < -1.8 < sensors[0].getValue()+0.01:
    #     moveFingers(fingers, mode = "open") 
    #     go_to_bucket2 == False
    #     prepare_grasp = True
    #     drop = False
    # if bool(total_cans): 
    #      goal = supervisor.getFromId(index).getField("translation")
    #      target = np.array(goal.getSFVec3f())          
    
