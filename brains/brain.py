import abc
import typing

from robot import Robot, SafeRobot

if typing.TYPE_CHECKING:
    from modelling import Model
    from structures import Map
    from cell import Cell

RobotT = typing.TypeVar("RobotT", bound = "Robot[Cell]")
MapT = typing.TypeVar("MapT", bound = "Map[Cell]", covariant=True)

class Brain(abc.ABC, typing.Generic[MapT, RobotT]):
    """Abstract class for brain"""
    def __init__(self, model: "Model[MapT, typing.Self, RobotT]"):
        self._model = model

    @abc.abstractmethod
    def get_next_action(self, robot: RobotT) -> Robot.Action:
        """Called by robot"""

    @abc.abstractmethod
    def new_robot(self, robot: RobotT) -> None:
        """Called by model when adding new robot"""


class OnlineBrain(Brain[MapT, SafeRobot]):
    """Abstract class for brain which for every robot position knowns action"""
    def __init__(self, model: "Model[MapT, typing.Self, SafeRobot]"):
        super().__init__(model)
        self._idle_robots: list[SafeRobot] = []
        self._input_destinations: dict[SafeRobot, int] = {}

    @typing.override
    def get_next_action(self, robot: SafeRobot) -> Robot.Action:
        if robot.mail is not None:
            if robot.position == self._model.map.outputs[robot.mail.destination]:
                self._mail_put(robot)
                return Robot.Action.put
            return self._go_with_mail(robot, robot.mail.destination)
        else:
            if robot.position == self._model.map.inputs[self._input_destinations[robot]]:
                self._mail_taken(robot)
                return Robot.Action.take
            return self._go_without_mail(robot, self._input_destinations[robot])

    @abc.abstractmethod
    def _go_with_mail(self, robot: SafeRobot, destination: int) -> Robot.Action:
        """Called if robot has mail"""

    @abc.abstractmethod
    def _go_without_mail(self, robot: SafeRobot, destination: int) -> Robot.Action:
        """Called if robot does not have mail"""

    def _mail_taken(self, robot: SafeRobot):
        """Called before sending `Action.take`"""

    def _mail_put(self, robot: SafeRobot):
        """Called before sending `Action.put`"""
