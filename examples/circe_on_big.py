from maps import OneWayMap, DirectionMap
from mail_factories import RandomAlwaysReadyMail
from import_data import import_safe_map, import_json
from structures import Direction, Position
from robot import SafeRobot, RobotType
from brains.direction_brain import DirectionBrain
from modelling import Model

model = Model[DirectionMap, DirectionBrain, SafeRobot]()
factory = RandomAlwaysReadyMail(model, range(1, 10))
simple_map = import_safe_map(model, import_json("data\\map1-simple.json"), factory)[0]
u = OneWayMap.Way.unknown
f = OneWayMap.Way.forward
b = OneWayMap.Way.backward
way_map = OneWayMap(
    simple_map.cells,
    [[u,f,f,f,f,f,f,u],
     [u,u,u,u,u,u,u,u],
     [f,f,f,f,f,f,f,f],
     [u,u,u,u,u,u,u,u],
     [u,u,u,u,u,u,u,u],
     [u,u,u,u,u,u,u,u],
     [u,u,u,u,u,u,u,u],
     [b,b,b,b,b,b,b,b],
     [u,u,u,u,u,u,u,u]],
    [[u,u,b,u,u,u,f,u,u],
     [b,u,b,u,u,u,f,u,f],
     [b,u,b,u,u,u,f,u,f],
     [b,u,b,u,u,u,f,u,f],
     [b,u,b,u,u,u,f,u,f],
     [b,u,b,u,u,u,f,u,f],
     [b,u,b,u,u,u,f,u,f],
     [u,u,u,u,u,u,u,u,u]]
    )
model.set_map(DirectionMap.generate_shortest(way_map))
model.set_brain(DirectionBrain(model))
robot_type = RobotType(1, 1, 1, 1)
for i in range(7):
    model.add_robot(SafeRobot(model, robot_type, Position(2, i+2), Direction.down, 1))

model.test(1000, 10)
