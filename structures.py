import enum

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
        
    def __str__(self):
        return f"Mail#{self._id} to {self._destination}"


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


class Position:
    @property
    def x(self): return self._x
    @property
    def y(self): return self._y

    def __init__(self, x: int, y: int):
        self._x = x
        self._y = y
    
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


class Map:
    def __init__(self, map_: list[list[Cell]]):
        self._map = map_
        self._n = len(map_)
        if self._n == 0:
            raise NotRectangleMapException()
        self._m = len(map_[0])
        if self._m == 0:
            raise NotRectangleMapException()
        for line in self._map:
            if len(line) != self._m:
                raise NotRectangleMapException()

    def __getitem__(self, position: Position):
        if position.x < 0 or position.x >= self._n\
                or position.y < 0 or position.y >= self._m:
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