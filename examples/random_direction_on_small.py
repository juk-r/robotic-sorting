import simpy
import json
import random

from cell import Cell
from maps import OneWayMap, DirectionMap
from mail_factories import MailFromLog
from import_data import import_map
from structures import Direction, Position
from robot import Robot, RobotType
from brains.direction_brain import DirectionBrain

def print_map(map_: OneWayMap[Cell]):
    for i in range(2*map_.n -1):
        for j in range(map_.m):
            if i%2 == 0:
                if j!=0:
                    if map_.horizontal[i//2][j-1].value == 1:
                        print('→| |', end='')
                    elif map_.horizontal[i//2][j-1].value == 0:
                        print('←| |', end='')
                    else:
                        print(' | |', end='')
                else: print('| |', end='')
            else:
                if map_.vertical[i//2][j].value == 1:
                    print(' ↓  ', end='')
                elif map_.vertical[i//2][j].value == 0:
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
    env = simpy.Environment()   
    factory = MailFromLog(env, r_s)

    with open("data\\small_map.json") as file:   
        simple_map = import_map(env, json.load(file), factory)[0]
    
    way_map = OneWayMap.generate_random(simple_map)
    map_ = DirectionMap.generate_shortest(way_map)
    brain = DirectionBrain(env, map_)
    robots = [Robot(env, robot_type, brain, Position(0, i), Direction.down, 1) for i in range(3)]
    env.run(TEST_TIME)
    if brain.count > max_:
        max_ = brain.count
        best_map = way_map

print(f"BEST: {TEST_TIME/max_} seconds per mail")
print_map(best_map)
