import random

from brains.brain import Brain
from robot import Robot

random.seed(0)

class RandomBrain(Brain):
    def new_robot(self, robot: Robot) -> None:
        "добавлен робот"

    def get_next_action(self, robot: Robot) -> Robot.Action:
        if robot.mail is None and self._model.map[robot.position].input_id is not None:
            # робот без посылки и текущая клетка - пункт получения
            return Robot.Action.take
        if robot.mail is not None and self._model.map[robot.position].output_id == robot.mail.destination:
            # робот c посылкой и текущая клетка - пункт назначения для посылки
            return Robot.Action.put
        # возможные действия робота
        actions = [
            Robot.Action.turn_to_up,
            Robot.Action.turn_to_left,
            Robot.Action.turn_to_down,
            Robot.Action.turn_to_right,
        ]
        if self._model.map.can_go(robot.position, robot.direction):
            # можно двигаться вперед
            actions.append(Robot.Action.move)
        return random.choice(actions)

    def collision_callback(self, robot: Robot) -> None:
        """столкновение роботов, ничего не делаем, 
        так как дальше будет вызван `get_next_action`"""
