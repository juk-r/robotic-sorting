import json
import random

from cell import SafeCell
from maps import OneWayMap, DirectionMap
from mail_factories import MailFromLog
from import_data import import_safe_map
from structures import Direction, Position
from robot import SafeRobot, RobotType
from brains.direction_brain import DirectionBrain
from modelling import Model

def print_map(map_: OneWayMap[SafeCell]):
    for i in range(2*map_.n -1):
        for j in range(map_.m):
            if i%2 == 0:
                if j!=0:
                    if map_.horizontal[i//2][j-1] == OneWayMap.Way.forward:
                        print('→| |', end='')
                    elif map_.horizontal[i//2][j-1] == OneWayMap.Way.backward:
                        print('←| |', end='')
                    else:
                        print(' | |', end='')
                else: print('| |', end='')
            else:
                if map_.vertical[i//2][j] == OneWayMap.Way.forward:
                    print(' ↓  ', end='')
                elif map_.vertical[i//2][j] == OneWayMap.Way.backward:
                    print(' ↑  ', end='')
                else:
                    print('    ', end='')
        print()
    print("===="*map_.m)

r_s = [MailFromLog.MailLog(i, random.randint(0, 1), 10*i, random.randint(0, 1)) for i in range(50000)]

robot_type = RobotType(1, 1, 1, 1)
max_ = 0
max_n = 0
best_map = None
TEST_TIME = 10000

for n in range(100):
    model = Model[DirectionMap, DirectionBrain, SafeRobot]()
    factory = MailFromLog(model, r_s)
    with open("data\\small_map.json") as file:   
        simple_map = import_safe_map(model, json.load(file), factory)[0]
    way_map = OneWayMap.generate_random(simple_map)
    model.set_map(DirectionMap.generate_shortest(way_map))
    model.set_brain(DirectionBrain(model))
    for i in range(3):
        model.add_robot(SafeRobot(model, robot_type, Position(0, i), Direction.down, 1))
    model.run(TEST_TIME)
    if model.delivered_mails > max_:
        max_ = model.delivered_mails
        best_map = way_map

print(f"BEST: {TEST_TIME/max_} seconds per mail")
print_map(best_map)
