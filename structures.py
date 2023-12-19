import enum
import typing

from exceptions import PositionOutOfMapException, NotRectangleMapException
from cell import Cell

class Mail:
    @property
    def id(self): return self._id
    @property
    def destination(self): return self._destination

    def __init__(self, id: int, destination: int):
        self._id = id
        self._destination = destination

    @typing.override
    def __str__(self):
        return f"Mail#{self._id} to {self._destination}"

    @typing.override
    def __hash__(self):
        return self._id


class Direction(enum.Enum):
    up = 0
    left = 1
    down = 2
    right = 3

    @staticmethod
    def turn_count(a: "Direction", b: "Direction"):
        cnt = abs(a.value - b.value)
        match cnt:
            case 0: return 0
            case 1: return 1
            case 2: return 2
            case 3: return 1
            case _: return 0

    @property
    def inverse(self):
        return Direction((self.value + 2) % 4)


class Position:
    @property
    def x(self): return self._x
    @property
    def y(self): return self._y

    def __init__(self, x: int, y: int):
        self._x = x
        self._y = y

    @typing.override
    def __str__(self):
        return f"({self._x}, {self._y})"

    def get_next_on(self, direction: Direction):
        match direction:
            case Direction.up:
                return Position(self._x - 1, self._y)
            case Direction.left:
                return Position(self._x, self._y - 1)
            case Direction.down:
                return Position(self._x + 1, self._y)
            case Direction.right:
                return Position(self._x, self._y + 1)

    def __eq__(self, other: "Position"): # type: ignore
        return self._x == other._x and self._y == other._y

    @typing.override
    def __hash__(self):
        return hash((self._x, self._y))


TCell = typing.TypeVar("TCell", bound=Cell, covariant=True)

class Map(typing.Generic[TCell]):
    @property
    def inputs(self):
        return self._inputs
    @property
    def outputs(self):
        return self._outputs
    @property
    def charges(self):
        return self._charges
    @property
    def n(self):
        return self._n
    @property
    def m(self):
        return self._m

    def __init__(self, map_: typing.Sequence[typing.Sequence[TCell]]):
        self._map = map_
        self._n = len(map_)
        if self._n == 0:
            raise NotRectangleMapException()
        self._m = len(map_[0])
        if self._m == 0:
            raise NotRectangleMapException()
        self._inputs: dict[int, Position] = {}
        self._outputs: dict[int, Position] = {}
        self._charges: dict[int, Position] = {}
        for x, line in enumerate(self._map):
            if len(line) != self._m:
                raise NotRectangleMapException()
            for y, cell in enumerate(line):
                if cell.input_id is not None:
                    self._inputs[cell.input_id] = Position(x, y)
                if cell.output_id is not None:
                    self._outputs[cell.output_id] = Position(x, y)
                if cell.charge_id is not None:
                    self._charges[cell.charge_id] = Position(x, y)

        self.input_ids = tuple(self._inputs.keys())
        self.output_ids = tuple(self._outputs.keys())
        self.charge_ids = tuple(self._charges.keys())

    def has(self, position: Position):
        return (position.x >= 0 and position.x < self._n
                and position.y >= 0 and position.y < self._m)

    @typing.overload
    def __getitem__(self, position: Position) -> TCell:...
    @typing.overload
    def __getitem__(self, position: tuple[int, int]) -> TCell:...
    def __getitem__(self, position: Position | tuple[int, int]):
        if isinstance(position, tuple):
            position = Position(position[0], position[1])
        if not self.has(position):
            raise PositionOutOfMapException(position)
        return self._map[position.x][position.y]


class RobotType:
    @property
    def time_to_move(self): return self._time_to_move
    @property
    def time_to_turn(self): return self._time_to_turn
    @property
    def time_to_put(self): return self._time_to_put
    @property
    def time_to_take(self): return self._time_to_take

    def __init__(self,
                 time_to_move: int,
                 time_to_turn: int,
                 time_to_put: int,
                 time_to_take: int):
        self._time_to_move = time_to_move
        self._time_to_turn = time_to_turn
        self._time_to_put = time_to_put
        self._time_to_take = time_to_take
