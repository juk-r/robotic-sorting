import typing
import simpy
import collections

from brains.brain import Brain
from robot import Robot

if typing.TYPE_CHECKING:
    from maps import DirectionMap
    from structures import Direction


class DirectionBrain(Brain):
    def __init__(self, env: simpy.Environment, map_: "DirectionMap"):
        super().__init__(env, map_)
        self._map: DirectionMap
        self._input_destinations = collections.defaultdict[Robot, int](
            lambda: self._next_input(None))
        self._last = 0

    def _next_input(self, robot: Robot | None):
        self._last += 1
        return self._map.input_ids[self._last % len(self._map.input_ids)]

    def _turn_move(self, robot: "Robot", direction: "Direction"):
        if robot.direction == direction:
            return robot.Action.move
        return Robot.Action.turn_to(direction)

    @typing.override
    def _go_with_mail(self, robot: "Robot", destination: int):
        return self._turn_move(robot, self._map[robot.position].to_outputs[destination])

    @typing.override
    def _go_without_mail(self, robot: "Robot", destination: int) -> "Robot.Action":
        return self._turn_move(robot, self._map[robot.position].to_inputs[destination])

    @typing.override
    def _mail_put(self, robot: Robot):
        self._input_destinations[robot] = self._next_input(robot)
