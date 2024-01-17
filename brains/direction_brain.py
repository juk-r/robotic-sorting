import typing

from brains.brain import OnlineBrain
from robot import SafeRobot

if typing.TYPE_CHECKING:
    from maps import DirectionMap
    from structures import Direction
    from modelling import Model


class DirectionBrain(OnlineBrain["DirectionMap"]):
    """
    Uses `DirectionMap`, for each cell knows direction for robot to go.
    Deadlock appears if cycle with length less than number of robots exists.
    """
    def __init__(self, model: "Model[DirectionMap, typing.Self, SafeRobot]"):
        super().__init__(model)
        self._last = 0

    @typing.override
    def new_robot(self, robot: SafeRobot):
        self._input_destinations[robot] = self._next_input(robot)

    def _next_input(self, robot: SafeRobot | None):
        self._last += 1
        return self._model.map.input_ids[self._last % len(self._model.map.input_ids)]

    def _turn_move(self, robot: "SafeRobot", direction: "Direction"):
        if robot.direction == direction:
            return robot.Action.move
        return SafeRobot.Action.turn_to(direction)

    @typing.override
    def _go_with_mail(self, robot: "SafeRobot", destination: int):
        return self._turn_move(robot, self._model.map[robot.position].to_outputs[destination])

    @typing.override
    def _go_without_mail(self, robot: "SafeRobot", destination: int) -> "SafeRobot.Action":
        return self._turn_move(robot, self._model.map[robot.position].to_inputs[destination])

    @typing.override
    def _mail_put(self, robot: SafeRobot):
        self._input_destinations[robot] = self._next_input(robot)
