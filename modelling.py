import simpy
import typing

if typing.TYPE_CHECKING:
    from brains import Brain
    from structures import Map
    from robot import Robot
    from typing import Any

BrainT = typing.TypeVar("BrainT", bound="Brain[Any, Any]", covariant=True)
RobotT = typing.TypeVar("RobotT", bound="Robot[Any]", covariant=True)
MapT = typing.TypeVar("MapT", bound="Map[Any]", covariant=True)

class Model(simpy.Environment, typing.Generic[MapT,  BrainT, RobotT]):
    map: MapT
    brain: BrainT
    robots: list[RobotT]
    def __init__(self):
        super().__init__()
        self.robots = []

    def set_map(self, map: MapT): # type: ignore
        self.map = map

    def set_brain(self, brain: BrainT):  # type: ignore
        self.brain = brain

    def add_robot(self, robot: RobotT):  # type: ignore
        self.robots.append(robot)
        self.brain.new_robot(robot)
