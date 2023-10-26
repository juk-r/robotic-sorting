import enum
import simpy
import typing

from structures import Position, Direction, Mail, RobotType
from exceptions import RobotWithoutMailException, RobotWithMailException

if typing.TYPE_CHECKING:
    from brain import Brain
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
    
    def __init__(self, env: simpy.Environment, 
                 type_: RobotType,
                 brain: "Brain",
                 position: Position, 
                 direction: Direction,
                 charge: float):
        self._env = env
        self._type = type_
        self._brain = brain
        self._position = position
        self._direction = direction
        self._charge = charge
        
        
        self._cell_request = self._brain.map[position].request()
        self._action = env.process(self._run())
        
        self._mail: Mail | None = None
        self._start_charge_time: simpy.core.SimTime | None = None
        self._event: simpy.Event | None = None
    
    
        
    def _idle(self):
        self._event = self._env.event()
        yield self._event
        self._event = None

    def _move(self):
        next_position = self._position.get_next_on(self._direction)
        request = self._brain.map[next_position].request()
        yield request
        yield self._env.timeout(self._type.time_to_move)
        self._brain.map[self._position].release(self._cell_request)
        self._position = next_position
        self._cell_request = request
        
    def _take(self) -> typing.Generator[simpy.Event, Mail, None]:
        if self._mail is not None:
            raise RobotWithMailException(self)
        self._mail: Mail | None = yield self._brain.map[self._position].get_input()
        yield self._env.timeout(self._type.time_to_take)

    def _put(self):
        if self._mail is None:
            raise RobotWithoutMailException(self)
        self._mail = None
        yield self._env.timeout(self._type.time_to_put)

    def _do_charge(self):
        start_time = self._env.now
        self._event = self._env.event()
        yield self._event | self._env.timeout(100*(1-self._charge))
        self._event = None
        self._charge = min(1, self._charge + 0.01*(self._env.now-start_time))

    def _turn(self, new_direction: Direction):
        yield self._env.timeout(Direction.turn_count(self._direction, new_direction)\
                          * self._type.time_to_turn)
        self._direction = new_direction

    def _run(self):
        yield self._cell_request
        while True:
            match self._brain.get_next_action(self):
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
    
