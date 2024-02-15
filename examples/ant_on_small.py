from brains import AntBrain
from mail_factories import RandomAlwaysReadyMail
from robot import SafeRobot
from structures import RobotType, Position, Direction, Map
from import_data import import_safe_map, import_json
from modelling import Model
from cell import SafeCell

model = Model[Map[SafeCell], AntBrain, SafeRobot]()

mail_factory = RandomAlwaysReadyMail(model, range(2))
model.set_map(import_safe_map(model, import_json("data\\small_map.json"), mail_factory)[0])

robot_type = RobotType(1, 1, 1, 1)
model.set_brain(AntBrain(model, robot_type, 0, 1.1, 0.5, 10))

for i in range(3):
    model.add_robot(SafeRobot(model, robot_type, Position(0, i), Direction.down, 0.5))

last_cnt=0
for i in range(1, 501):
    model.run(model.now+30000)
    model.brain.update()
    if i % 1 == 0:
        print(i, model.delivered_mails-last_cnt)
        last_cnt = model.delivered_mails

TEST_TIME = 100000
model.run(model.now+TEST_TIME)
print(f"average: {TEST_TIME/(model.delivered_mails-last_cnt)} seconds per mail")
