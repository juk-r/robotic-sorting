import abc
import typing

if typing.TYPE_CHECKING:
    import simpy
    from robot import Robot
    from structures import Map

class Brain(abc.ABC):
    @property
    def map(self):
        return self._map

    def __init__(self, env: "simpy.Environment", map_: "Map"):
        self._env = env
        self._map = map_
        self._idle_robots: list["Robot"] = []
        self._charging_robots: list["Robot"] = []


    @abc.abstractmethod
    def get_next_action(self, robot: "Robot") -> "Robot.Action":
        pass
