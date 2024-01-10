from cell import Cell
from mail_factories import RandomAlwaysReadyMail
from import_data import import_map, import_json
from structures import Direction, Position, Map
from robot import Robot, RobotType
from brains.path_brain import PathBrain
from modelling import Model

model = Model[Map[Cell], PathBrain, Robot[Cell]]()

mail_factory = RandomAlwaysReadyMail(model, range(1, 10))
map_ = import_map(model, import_json("data\\map1-simple.json"), mail_factory)[0]
model.set_map(map_)

robot_type = RobotType(1, 1, 1, 1)
model.set_brain(PathBrain(model, robot_type, True, False))
starts = [
    Position(2, 2),
    Position(2, 4),
    Position(2, 6),
    Position(3, 3),
    Position(3, 5),
    Position(4, 2),
    Position(4, 6),
]
robots = [Robot(model, robot_type, pos, Direction.down) for pos in starts]

for i, robot in enumerate(robots):
    model.brain.robots_rests[robot] = starts[i]
    model.add_robot(robot)

model.record(1000)
print(model.brain.count)
model.test(1000, 10)
