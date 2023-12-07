import collections
import random
import typing
import simpy

from brains.brain import Brain
from robot import Robot
from structures import Map, RobotType, Position, Direction

class AntBrain(Brain):
    class _Pheromones:
        def __init__(self, p: float, q: float, rho: float,
                     times: typing.Sequence[float],
                     next_: "typing.Sequence[Robot.Action]"):
            self._p = p
            self._q = q
            self._rho = rho
            self._times = times
            self._pheromones = [1.0 for _ in times]
            self._next = next_
            self.to_update: typing.Final = [0.0]*len(times)

        def get(self):
            weights: list[float] = []
            for pher, time in zip(self._pheromones, self._times):
                weights.append(pher**self._p / time**self._p)
            res = random.choices(range(len(self._next)), weights)[0]
            return res, self._next[res]

        def update(self):
            for i, val in enumerate(self.to_update):
                self._pheromones[i] = (1-self._rho)*self._pheromones[i] + val

    def __init__(self, env: simpy.Environment, map_: Map,
                 robot_type: RobotType, q: float, p: float, rho: float,
                 Q: float):
        """
        param q: greed, power of inverse time, > 0
        param p: herd, power of pheromone, > 1
        param rho: pheromone evaporation coefficient, 0 < ... < 1
        param Q: constant to add, > 0
        """
        def new_pheromones(ids: typing.Iterable[int]):
            def actions(position: Position, direction: Direction):
                times: list[float] = []
                acts: list[Robot.Action] = []
                if (map_.has(position.get_next_on(direction))
                        and map_[position.get_next_on(direction)].free):
                    times.append(robot_type.time_to_move)
                    acts.append(Robot.Action.move)
                for new_direction in Direction:
                    if new_direction != direction and map_.has(position.get_next_on(new_direction)):
                        times.append(robot_type.time_to_turn)
                        acts.append(Robot.Action.turn_to(new_direction))
                return (times, acts)
            return {
                (id_, Position(x, y), direc):
                    AntBrain._Pheromones(p, q, rho, *actions(Position(x, y), direc))
                for id_ in ids
                for x in range(map_.n)
                for y in range(map_.m)
                for direc in Direction            
            }

        super().__init__(env, map_)
        self._q = q
        self._p = p
        self._rho = rho
        self._Q = Q

        self._to_inputs = new_pheromones(map_.input_ids)
        self._to_outputs = new_pheromones(map_.output_ids)
        self._to_charges = new_pheromones(map_.charge_ids)
        self._last = 0
        self._input_destinations = collections.defaultdict[Robot, int](
            lambda: self._next_input(None))
        self._given_actions: dict[Robot, list[tuple[AntBrain._Pheromones, int]]] = {}
        self._start_time: dict[Robot, float] = {}

        self._to_do: dict[Robot, Robot.Action | None] = {}

    def _new_robot(self, robot: Robot):
        if robot not in self._given_actions:
            self._given_actions[robot] = []
        if robot not in self._to_do:
            self._to_do[robot] = None
        if robot not in self._start_time:
            self._start_time[robot] = self._env.now

    def _next_input(self, robot: Robot | None):
        self._last += 1
        return self._map.input_ids[self._last % len(self._map.input_ids)]

    def _go(self, robot: Robot, pheromones: _Pheromones):
        if robot.timeout:
            self._given_actions[robot].pop()
        self._new_robot(robot)
        if (act := self._to_do[robot]) is not None:
            self._to_do[robot] = None
            return act
        next_ = pheromones.get()
        if robot not in self._given_actions:
            self._given_actions[robot] = []
        self._given_actions[robot].append((pheromones, next_[0]))
        if next_[1] in (Robot.Action.turn_to_up, Robot.Action.turn_to_left,
                        Robot.Action.turn_to_down, Robot.Action.turn_to_right):
            self._to_do[robot] = Robot.Action.move
        return next_[1]

    @typing.override
    def _go_with_mail(self, robot: Robot, destination: int):
        pheromones = self._to_outputs[destination, robot.position, robot.direction]
        return self._go(robot, pheromones)

    @typing.override
    def _go_without_mail(self, robot: Robot, destination: int):
        pheromones = self._to_inputs[destination, robot.position, robot.direction]
        return self._go(robot, pheromones)

    @typing.override
    def _mail_put(self, robot: Robot):
        self._new_robot(robot)
        for pheromone, i in self._given_actions[robot]:
            pheromone.to_update[i] += self._Q/(self._env.now - self._start_time[robot])
        self._given_actions[robot].clear()
        self._start_time[robot] = self._env.now
        self._input_destinations[robot] = self._next_input(robot)

    @typing.override
    def _mail_taken(self, robot: Robot):
        self._new_robot(robot)
        for pheromone, i in self._given_actions[robot]:
            pheromone.to_update[i] += self._Q/(self._env.now - self._start_time[robot])
        self._given_actions[robot].clear()
        self._start_time[robot] = self._env.now

    def update(self):
        for to in (self._to_inputs, self._to_outputs, self._to_charges):
            for ph in to.values():
                ph.update()
