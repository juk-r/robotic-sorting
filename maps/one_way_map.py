import typing
import random
import enum

from structures import Map, TCell, Position, Direction

class OneWayMap(Map[TCell]):
    """Map that between every neighbors cells only 1 direction is allowed"""
    class Way(enum.Flag):
        unknown = 0
        backward = 1
        forward = 2

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

    @typing.override
    def can_go(self, pos: Position, direction:Direction) -> bool:
        if not self.has(pos.get_next_on(direction)):
            return False
        match direction:
            case Direction.up:
                return bool(self._vertical[pos.x - 1][pos.y] & OneWayMap.Way.backward)
            case Direction.down:
                return bool(self._vertical[pos.x][pos.y] & OneWayMap.Way.forward)
            case Direction.left:
                return bool(self._horizontal[pos.x][pos.y - 1] & OneWayMap.Way.backward)
            case Direction.right:
                return bool(self._horizontal[pos.x][pos.y] & OneWayMap.Way.forward)

    @staticmethod
    def generate_random(map_: Map[TCell]):
        """generates random connected (if possible) map"""
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
                        if x>0 and not vertical[x-1][y] and map_._map[x-1][y].free:
                            vertical[x-1][y] = OneWayMap.Way.backward
                            generate(x-1, y)
                    case Direction.down:
                        if x<map_.n-1 and not vertical[x][y] and map_._map[x+1][y].free:
                            vertical[x][y] = OneWayMap.Way.forward
                            generate(x+1, y)
                    case Direction.left:
                        if y>0 and not horizontal[x][y-1] and map_._map[x][y-1].free:
                            horizontal[x][y-1] = OneWayMap.Way.backward
                            generate(x, y-1)
                    case Direction.right:
                        if y<map_.m-1 and not horizontal[x][y] and map_._map[x][y+1].free:
                            horizontal[x][y] = OneWayMap.Way.forward
                            generate(x, y+1)
        generate(map_.inputs[tuple(map_.inputs.keys())[0]].x,
                 map_.inputs[tuple(map_.inputs.keys())[0]].y)
        return OneWayMap(map_._map, horizontal, vertical)
