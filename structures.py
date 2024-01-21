import dataclasses
import enum
import typing

from exceptions import PositionOutOfMapException, NotRectangleMapException
from cell import Cell

@dataclasses.dataclass(frozen=True, slots=True)
class Mail:
    id: int
    destination: int

    @typing.override
    def __str__(self):
        return f"Mail#{self.id} to {self.destination}"


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
    
    @typing.override
    def __repr__(self):
        return self.name[0]


@dataclasses.dataclass(frozen=True, slots=True)
class Position:
    x: int
    y: int

    @typing.override
    def __repr__(self):
        return f"({self.x}, {self.y})"

    def get_next_on(self, direction: Direction):
        match direction:
            case Direction.up:
                return Position(self.x - 1, self.y)
            case Direction.left:
                return Position(self.x, self.y - 1)
            case Direction.down:
                return Position(self.x + 1, self.y)
            case Direction.right:
                return Position(self.x, self.y + 1)


TCell = typing.TypeVar("TCell", bound=Cell, covariant=True)

class Map(typing.Generic[TCell]):
    @property
    def inputs(self):
        return self._inputs
    @property
    def outputs(self):
        return self._outputs
    @property
    def n(self):
        return self._n
    @property
    def m(self):
        return self._m
    @property
    def cells(self):
        return self._map

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
        for x, line in enumerate(self._map):
            if len(line) != self._m:
                raise NotRectangleMapException()
            for y, cell in enumerate(line):
                cell.position = Position(x, y)
                if cell.input_id is not None:
                    self._inputs[cell.input_id] = Position(x, y)
                if cell.output_id is not None:
                    self._outputs[cell.output_id] = Position(x, y)

        self.input_ids = tuple(self._inputs.keys())
        self.output_ids = tuple(self._outputs.keys())

    def has(self, position: Position):
        return (0 <= position.x < self._n
                and 0 <= position.y < self._m
                and self._map[position.x][position.y].free)

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

    def __iter__(self) -> typing.Iterator[Position]:
        for x in range(self.n):
            for y in range(self.m):
                if self._map[x][y].free:
                    yield Position(x, y)

    def get_neighbors(self, position: Position) -> typing.Iterable[Position]:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if self.has(pos := Position(position.x+dx, position.y+dy)):
                yield pos

    def distance(self, pos1: Position, pos2: Position):
        """ Manhattan distance `|x|+|y|`"""
        return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)

    def can_go(self, position: Position, direction: Direction, /) -> bool:
        return self.has(position.get_next_on(direction))

@dataclasses.dataclass(frozen=True, slots=True)
class RobotType:
    time_to_move: int
    time_to_turn: int
    time_to_put: int
    time_to_take: int
