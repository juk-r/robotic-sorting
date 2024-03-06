from maps import OneWayMap, DirectionMap
from import_data import import_safe_map, import_json, import_distribution, import_robot_type
from structures import Direction, Position
from robot import SafeRobot
from brains.direction_brain import DirectionBrain
from modelling import Model

model = Model[DirectionMap, DirectionBrain, SafeRobot]()
factory = import_distribution(model, import_json("data\\sample-distribution.json"))
simple_map = import_safe_map(model, import_json("data\\small_map.json"), factory)[0]
f = OneWayMap.Way.forward
b = OneWayMap.Way.backward
way_map = OneWayMap(
    simple_map.cells,
    [[f, f],
     [b, f],
     [b, b]],
    [[b, b, f],
     [b, f, f]]
    )
model.set_map(DirectionMap.generate_shortest(way_map))
robot_type = import_robot_type(import_json("data\\example\\robot-type.json"))
model.set_brain(DirectionBrain(model))
for i in range(3):
    model.add_robot(SafeRobot(model, robot_type, Position(0, i), Direction.down, 1))
model.add_robot(SafeRobot(model, robot_type, Position(1, 1), Direction.down, 1))
model.run(100)
print(f"{model.delivered_mails = }")
