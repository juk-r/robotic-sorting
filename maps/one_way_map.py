import typing
import random
import enum

from structures import Map, TCell, Position, Direction

class OneWayMap(Map[TCell]):
    class Way(enum.Enum):
        unknown = -1
        backward = 0
        forward = 1

    @property
    def horizontal(self):
        return self._horizontal
    @property
    def vertical(self):
        return self._vertical

    def __init__(self, map_: typing.Sequence[typing.Sequence[TCell]],
                 horizontal: typing.Sequence[typing.Sequence[Way]],
                 vertical: typing.Sequence[typing.Sequence[Way]]):
        super().__init__(map_)
        self._horizontal = horizontal
        self._vertical = vertical

    def can_go(self, position: Position, direction:Direction):
        match direction:
            case Direction.up:
                if 0 < position.x < self._n and 0 <= position.y < self._m:
                    return self._vertical[position.x - 1][position.y].value == 0
            case Direction.down:
                if 0 <= position.x < self._n-1 and 0 <= position.y < self._m:
                    return self._vertical[position.x][position.y].value == 1
            case Direction.left:
                if 0 <= position.x < self._n and 0 < position.y < self._m :
                    return self._horizontal[position.x][position.y - 1].value == 0
            case Direction.right:
                if 0 <= position.x < self._n and 0 <= position.y < self._m-1:
                    return self._horizontal[position.x][position.y].value == 1
        return False

    @staticmethod
    def generate_random(map_: Map[TCell]):
        horizontal = [[OneWayMap.Way.unknown for _ in range(map_._m - 1)]
                      for _ in range(map_._n)]
        vertical = [[OneWayMap.Way.unknown for _ in range(map_._m)]
                    for _ in range(map_._n - 1)]
        def generate(x: int, y: int):
            directions = [Direction.up, Direction.left,
                          Direction.down, Direction.right]
            random.shuffle(directions)
            for direction in directions:
                match direction:
                    case Direction.up:
                        if x>0 and vertical[x-1][y].value==-1 and map_[x-1, y].free:
                            vertical[x-1][y] = OneWayMap.Way.backward
                            generate(x-1, y)
                    case Direction.down:
                        if x<map_.n-1 and vertical[x][y].value==-1 and map_[x+1, y].free:
                            vertical[x][y] = OneWayMap.Way.forward
                            generate(x+1, y)
                    case Direction.left:
                        if y>0 and horizontal[x][y-1].value==-1 and map_[x, y-1].free:
                            horizontal[x][y-1] = OneWayMap.Way.backward
                            generate(x, y-1)
                    case Direction.right:
                        if y<map_.m-1 and horizontal[x][y].value==-1 and map_[x, y+1].free:
                            horizontal[x][y] = OneWayMap.Way.forward
                            generate(x, y+1)
        generate(map_.inputs[tuple(map_.inputs.keys())[0]].x,
                 map_.inputs[tuple(map_.inputs.keys())[0]].y)
        return OneWayMap(map_._map, horizontal, vertical)
            