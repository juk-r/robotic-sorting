import typing
import simpy
import collections

from brain import Brain
from maps import DirectionMap
from robot import Robot


class DirectionBrain(Brain):
    @property
    def count(self):
        return self._count
    def __init__(self, env: simpy.Environment, map_: DirectionMap):
        super().__init__(env, map_)
        self._map: DirectionMap
        self._destinations = collections.defaultdict[Robot, int](
            lambda: self._next_input(None))
        self._count = 0
        self._last = 0

    def _next_input(self, robot: Robot | None):
        self._last += 1
        return self._map.input_ids[self._last % len(self._map.input_ids)]
    
    @typing.override
    def get_next_action(self, robot: Robot) -> Robot.Action:
        if robot.mail is not None:
            if robot.position == self._map.outputs[robot.mail.destination]:
                self._destinations[robot] = self._next_input(robot)
                self._count += 1
                return Robot.Action.put
            direction = self._map[robot.position].to_outputs[robot.mail.destination]
        else:
            if robot.position == self._map.inputs[self._destinations[robot]]:
                return Robot.Action.take
            direction = self._map[robot.position].to_inputs[self._destinations[robot]]
        if robot.direction == direction:
            return robot.Action.move
        return Robot.Action.turn_to(direction)
