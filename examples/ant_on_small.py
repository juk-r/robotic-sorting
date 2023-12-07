import simpy

from brains import AntBrain
from mail_factories import RandomAlwaysReadyMail
from robot import Robot
from structures import RobotType, Position, Direction
from import_data import import_map, import_json

env = simpy.Environment()
mail_factory = RandomAlwaysReadyMail(env, range(2))
map_ = import_map(env, import_json("data\\small_map.json"), mail_factory)[0]
robot_type = RobotType(1, 1, 1, 1)
brain = AntBrain(env, map_, robot_type, 0.5, 1.1, 0.1, 0.1)
robots = [Robot(env, robot_type, brain, Position(0, i), Direction.down, 1,10) for i in range(3)]
last_cnt=0

for i in range(1, 51):
    env.run(env.now+30000)
    brain.update()
    if i % 1 == 0:
        print(i, brain.count-last_cnt)
        last_cnt = brain.count

TEST_TIME = 100000
env.run(env.now+TEST_TIME)
print(f"average: {TEST_TIME/(brain.count-last_cnt)} seconds per mail")
