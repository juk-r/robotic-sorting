import enum
import logging
import simpy
import typing

from structures import Position, Direction, Mail, RobotType
from exceptions import RobotWithoutMailException, RobotWithMailException, IncorrectOutputException

if typing.TYPE_CHECKING:
    from brains import Brain, OnlineBrain
    import simpy.core
    from structures import Map
    from cell import Cell, SafeCell
    from modelling import Model


CellT = typing.TypeVar("CellT", bound="Cell", covariant=True)

class Robot(typing.Generic[CellT]):
    class Action(enum.Enum):
        idle = 0
        move = 1
        take = 2
        put = 3
        turn_to_up = 10
        turn_to_left = 11
        turn_to_down = 12
        turn_to_right = 13

        @staticmethod
        def turn_to(direction: Direction):
            return Robot.Action(10 + direction.value)

    _last_robot_id: int = 0

    @property
    def position(self):
        return self._position
    @property
    def direction(self):
        return self._direction
    @property
    def mail(self):
        return self._mail
    @property
    def id(self):
        return self._id
    @property
    def type(self):
        return self._type

    def __init__(self, model: "Model[Map[CellT], Brain[Map[CellT], Robot[Cell]], Robot[Cell]]",
                 type_: RobotType,
                 position: Position,
                 direction: Direction,
                 ):
        self._id = Robot._last_robot_id
        Robot._last_robot_id += 1

        self._model = model
        self._type = type_
        self._position = position
        self._direction = direction

        self._cell_request = model.map[position].reserve()
        self._action = model.process(self._run())

        self._mail: Mail | None = None
        self._start_charge_time: simpy.core.SimTime | None = None
        self._event: simpy.Event = model.event()
        self._aborted = False
        self.timeout = False

    def _new_abortable_event(self, event: simpy.Event | None = None):
        def cancel_event(evt: simpy.Event):
            if not self._event.triggered:
                self._event.succeed(evt.value)
                self._aborted = False
        self._event = self._model.event()
        if event is not None:
            event.callbacks.append(cancel_event) # pyright: ignore[reportUnknownMemberType]
        return self._event

    def abort(self):
        if self._event.triggered:
            logging.warn(f"Tried to abort {self}'s event.")
            return False
        logging.info(f"{self}'s event aborted.")
        self._event.succeed()
        self._aborted = True
        return True

    def _idle(self):
        logging.info(f"{self} is idle.")
        yield self._new_abortable_event()

    def _move(self) -> typing.Generator[simpy.Event, bool, None]:
        next_position = self._position.get_next_on(self._direction)
        request = self._model.map[next_position].reserve()
        yield request
        logging.info(f"{self} is moving to {next_position}.")
        yield self._model.timeout(self._type.time_to_move)
        self._model.map[self._position].unreserve(self._cell_request)
        self._position = next_position
        self._cell_request = request

    def _take(self) -> typing.Generator[simpy.Event, Mail, None]:
        if self._mail is not None:
            raise RobotWithMailException(self)
        logging.info(f"{self} is waiting for mail.")
        self._mail = yield self._new_abortable_event(
            self._model.map[self._position].get_input())
        if self._aborted:
            return
        logging.info(f"{self} is taking {self._mail}.")
        yield self._model.timeout(self._type.time_to_take)

    def _put(self):
        if self._mail is None:
            raise RobotWithoutMailException(self)
        if self._model.map[self.position].output_id != self._mail.destination:
            raise IncorrectOutputException(self._mail, self._model.map[self.position])
        logging.info(f"{self} is putting {self._mail}.")
        self._mail = None
        yield self._model.timeout(self._type.time_to_put)

    def _turn(self, new_direction: Direction):
        logging.info(f"{self} is turning to {new_direction}.")
        yield self._model.timeout(Direction.turn_count(self._direction, new_direction)\
                          * self._type.time_to_turn)
        self._direction = new_direction

    def _run(self):
        yield self._cell_request
        while True:
            match self._model.brain.get_next_action(self):
                case Robot.Action.idle:
                    yield self._model.process(self._idle())
                case Robot.Action.move:
                    yield self._model.process(self._move())
                case Robot.Action.take:
                    yield self._model.process(self._take())
                case Robot.Action.put:
                    yield self._model.process(self._put())
                case Robot.Action.turn_to_up | Robot.Action.turn_to_left\
                        | Robot.Action.turn_to_down | Robot.Action.turn_to_right as turn:
                    yield self._model.process(self._turn(Direction(turn.value-10)))
    
    @typing.override
    def __str__(self):
        return f"Robot#{self._id}"


class SafeRobot(Robot["SafeCell"]):
    def __init__(self, model: "Model[Map[SafeCell], OnlineBrain[Map[SafeCell]], SafeRobot]",
                 type_: RobotType,
                 position: Position,
                 direction: Direction,
                 wait_time: float = -1):
        super().__init__(model, type_, position, direction) # type: ignore
        self.wait_time = wait_time

    @typing.override
    def _move(self) -> typing.Generator[simpy.Event, bool, None]:
        next_position = self._position.get_next_on(self._direction)
        request = self._model.map[next_position].reserve()
        logging.info(f"{self} is waiting for {next_position} to free.")
        if self.wait_time > 0:
            start_time = self._model.now
            yield self._new_abortable_event(request) | self._model.timeout(self.wait_time)
            self.timeout = (self._model.now - start_time) >= self.wait_time
        else:
            yield self._new_abortable_event(request)
            self.timeout = False
        if self.timeout:
            logging.info(f"{self} waited too much ({self.wait_time}).")
        if self.timeout or self._aborted:
            self._model.map[next_position].unreserve(request)
            return
        logging.info(f"{self} is moving to {next_position}.")
        yield self._model.timeout(self._type.time_to_move)
        self._model.map[self._position].unreserve(self._cell_request)
        self._position = next_position
        self._cell_request = request

    @typing.override
    def _run(self):
        yield self._cell_request
        while True:
            match act := self._model.brain.get_next_action(self):
                case Robot.Action.idle:
                    yield self._model.process(self._idle())
                case Robot.Action.move:
                    yield self._model.process(self._move())
                case Robot.Action.take:
                    yield self._model.process(self._take())
                case Robot.Action.put:
                    yield self._model.process(self._put())
                case Robot.Action.turn_to_up | Robot.Action.turn_to_left\
                        | Robot.Action.turn_to_down | Robot.Action.turn_to_right:
                    yield self._model.process(self._turn(Direction(act.value-10)))
            if act is not Robot.Action.move:
                self.timeout = False
