import abc
import typing

from robot import Robot

if typing.TYPE_CHECKING:
    from modelling import Model
    from structures import Map
    from cell import Cell

RobotT = typing.TypeVar("RobotT", bound = "Robot[Cell]")
MapT = typing.TypeVar("MapT", bound = "Map[Cell]", covariant=True)

class Brain(abc.ABC, typing.Generic[MapT, RobotT]):
    @property
    def count(self):
        return self._count

    def __init__(self, model: "Model[MapT, typing.Self, RobotT]"):
        self._model = model
        self._idle_robots: list[RobotT] = []
        self._input_destinations: dict[RobotT, int] = {}
        self._count = 0

    def get_next_action(self, robot: RobotT) -> Robot.Action:
        if robot.mail is not None:
            if robot.position == self._model.map.outputs[robot.mail.destination]:
                self._mail_put(robot)
                self._count += 1
                return Robot.Action.put
            return self._go_with_mail(robot, robot.mail.destination)
        else:
            if robot.position == self._model.map.inputs[self._input_destinations[robot]]:
                self._mail_taken(robot)
                return Robot.Action.take
            return self._go_without_mail(robot, self._input_destinations[robot])

    @abc.abstractmethod
    def _go_with_mail(self, robot: RobotT, destination: int) -> Robot.Action: ...

    @abc.abstractmethod
    def _go_without_mail(self, robot: RobotT, destination: int) -> Robot.Action: ...

    def _mail_taken(self, robot: RobotT):
        pass

    def _mail_put(self, robot: RobotT):
        pass

    def new_robot(self, robot: RobotT):
        pass
