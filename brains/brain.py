import abc
import typing

from robot import Robot

if typing.TYPE_CHECKING:
    import simpy
    from structures import Map

class Brain(abc.ABC):
    @property
    def map(self):
        return self._map
    @property
    def count(self):
        return self._count

    def __init__(self, env: "simpy.Environment", map_: "Map"):
        self._env = env
        self._map = map_
        self._idle_robots: list[Robot] = []
        self._charging_robots: list[Robot] = []
        self._input_destinations: dict[Robot, int] = {}
        self._count = 0


    def get_next_action(self, robot: Robot) -> Robot.Action:
        if robot.mail is not None:
            if robot.position == self._map.outputs[robot.mail.destination]:
                self._mail_put(robot)
                self._count += 1
                return Robot.Action.put
            return self._go_with_mail(robot, robot.mail.destination)
        else:
            if robot.position == self._map.inputs[self._input_destinations[robot]]:
                self._mail_taken(robot)
                return Robot.Action.take
            return self._go_without_mail(robot, self._input_destinations[robot])

    @abc.abstractmethod
    def _go_with_mail(self, robot: Robot, destination: int) -> Robot.Action: ...

    @abc.abstractmethod
    def _go_without_mail(self, robot: Robot, destination: int) -> Robot.Action: ...

    def _mail_taken(self, robot: Robot):
        pass

    def _mail_put(self, robot: Robot):
        pass
