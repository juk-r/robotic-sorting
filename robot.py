import enum
import logging
import simpy
import typing

from structures import Position, Direction, Mail, RobotType
from exceptions import RobotWithoutMailException, RobotWithMailException

if typing.TYPE_CHECKING:
    from brains import Brain
    import simpy.core


class Robot:
    class Action(enum.Enum):
        idle = 0
        move = 1
        take = 2
        put = 3
        charge = 4
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
    def charge(self):
        return self._charge
    @property
    def mail(self):
        return self._mail
    @property
    def id(self):
        return self._id

    def __init__(self, env: simpy.Environment,
                 type_: RobotType,
                 brain: "Brain",
                 position: Position,
                 direction: Direction,
                 charge: float,
                 wait_time: float = -1):
        self._id = Robot._last_robot_id
        Robot._last_robot_id += 1

        self._env = env
        self._type = type_
        self._brain = brain
        self._position = position
        self._direction = direction
        self._charge = charge
        self.wait_time = wait_time

        self._cell_request = self._brain.map[position].request()
        self._action = env.process(self._run())

        self._mail: Mail | None = None
        self._start_charge_time: simpy.core.SimTime | None = None
        self._event: simpy.Event = env.event()
        self._aborted = False
        self.timeout = False

    def _new_abortable_event(self, event: simpy.Event | None = None):
        def cancel_event(evt: simpy.Event):
            if not self._event.triggered:
                self._event.succeed(evt.value)
                self._aborted = False
        self._event = self._env.event()
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
        request = self._brain.map[next_position].request()
        logging.info(f"{self} is waiting for {next_position} to free.")
        if self.wait_time > 0:
            start_time = self._env.now
            yield self._new_abortable_event(request) | self._env.timeout(self.wait_time)
            self.timeout = (self._env.now - start_time) >= self.wait_time
        else:
            yield self._new_abortable_event(request)
            self.timeout = False
        if self._aborted:
            request.cancel()
            return
        if self.timeout:
            request.cancel()
            logging.info(f"{self} waited too much ({self.wait_time}).")
            return
        logging.info(f"{self} is moving to {next_position}.")
        yield self._env.timeout(self._type.time_to_move)
        self._brain.map[self._position].release(self._cell_request)
        self._position = next_position
        self._cell_request = request

    def _take(self) -> typing.Generator[simpy.Event, Mail, None]:
        if self._mail is not None:
            raise RobotWithMailException(self)
        logging.info(f"{self} is waiting for mail.")
        self._mail = yield self._new_abortable_event(
            self._brain.map[self._position].get_input())
        if self._aborted:
            return
        logging.info(f"{self} is taking {self._mail}.")
        yield self._env.timeout(self._type.time_to_take)

    def _put(self):
        if self._mail is None:
            raise RobotWithoutMailException(self)
        logging.info(f"{self} is putting {self._mail}.")
        self._mail = None
        yield self._env.timeout(self._type.time_to_put)

    @property
    def time_to_full_charge(self):
        return 100*(1-self._charge)

    def get_charge_after(self, charge_time: float) -> float:
        return min(1, self._charge + 0.01*charge_time)

    def _do_charge(self) -> typing.Generator[simpy.Event, None, None]:
        raise NotImplementedError()
        start_time = self._env.now
        logging.log(f"{self} is charging.")
        yield self._new_abortable_event(self._env.timeout(self.time_to_full_charge))
        self._charge = self.get_charge_after(self._env.now - start_time)

    def _turn(self, new_direction: Direction):
        logging.info(f"{self} is turning to {new_direction}.")
        yield self._env.timeout(Direction.turn_count(self._direction, new_direction)\
                          * self._type.time_to_turn)
        self._direction = new_direction

    def _run(self):
        yield self._cell_request
        while True:
            match act := self._brain.get_next_action(self):
                case Robot.Action.idle:
                    yield self._env.process(self._idle())
                case Robot.Action.move:
                    yield self._env.process(self._move())
                case Robot.Action.take:
                    yield self._env.process(self._take())
                case Robot.Action.put:
                    yield self._env.process(self._put())
                case Robot.Action.charge:
                    yield self._env.process(self._do_charge())
                case Robot.Action.turn_to_up | Robot.Action.turn_to_left\
                        | Robot.Action.turn_to_down | Robot.Action.turn_to_right as turn:
                    yield self._env.process(self._turn(Direction(turn.value-10)))
            if act is not Robot.Action.move:
                self.timeout = False

    @typing.override
    def __str__(self):
        return f"Robot#{self._id}"
