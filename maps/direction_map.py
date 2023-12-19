import typing
import simpy

from structures import Map, Direction, Position
from cell import SafeCell, MailInputGetter
from maps.one_way_map import OneWayMap


class DirectionCell(SafeCell):
    @property
    def to_inputs(self):
        return self._to_inputs
    @property
    def to_outputs(self):
        return self._to_outputs
    @property
    def to_charges(self):
        return self._to_charges

    def __init__(self, env: simpy.Environment,
                 get_mail_input: MailInputGetter,
                 to_inputs: dict[int, Direction],
                 to_outputs: dict[int, Direction],
                 to_charges: dict[int, Direction],
                 input_id: int | None = None,
                 output_id: int | None = None,
                 charge_id: int | None = None,
                 free: bool = True):
        super().__init__(env, get_mail_input, input_id, output_id, charge_id, free)
        self._to_inputs = to_inputs
        self._to_outputs = to_outputs
        self._to_charges = to_charges

    @staticmethod
    def from_cell(cell: SafeCell,
                 to_inputs: dict[int, Direction],
                 to_outputs: dict[int, Direction],
                 to_charges: dict[int, Direction]):
        result = DirectionCell.__new__(DirectionCell)
        result.__dict__.update(cell.__dict__)
        result._to_inputs = to_inputs
        result._to_outputs = to_outputs
        result._to_charges = to_charges
        return result


TDirectionCell = typing.TypeVar("TDirectionCell", bound=DirectionCell)

class GenericDirectionMap(Map[TDirectionCell]):
    def __init__(self, map_: typing.Sequence[typing.Sequence[TDirectionCell]]):
        super().__init__(map_)

    @staticmethod
    def generate_shortest(map_: OneWayMap[SafeCell]) -> "GenericDirectionMap[DirectionCell]":
        to_inputs: list[list[dict[int, Direction]]] = \
            [[{} for _ in range(map_.m)] for _ in range(map_.n)]
        to_outputs: list[list[dict[int, Direction]]] = \
            [[{} for _ in range(map_.m)] for _ in range(map_.n)]
        to_charges: list[list[dict[int, Direction]]] = \
            [[{} for _ in range(map_.m)] for _ in range(map_.n)]
        used: list[list[bool]]
        go_next: list[Position]
        def dfs(array: list[list[dict[int, Direction]]],
                id: int, pos: Position):
            if used[pos.x][pos.y]:
                return
            used[pos.x][pos.y] = True
            for direction in (Direction.up, Direction.left,
                              Direction.down, Direction.right):
                new_position = pos.get_next_on(direction)
                if map_.can_go(new_position, direction.inverse) and\
                        not used[new_position.x][new_position.y]:
                    array[new_position.x][new_position.y][id] = direction.inverse
                    go_next.append(new_position)

        for type_ in ('inputs', 'outputs', 'charges'):
            d: dict[int, Position] = map_.__dict__["_" + type_]
            for id_, start in d.items():
                used = [[False for _ in range(map_.m)] for _ in range(map_.n)]
                go_next = [start]
                i = 0
                while i < len(go_next):
                    dfs(locals()[f"to_{type_}"], id_, go_next[i])
                    i += 1
        return GenericDirectionMap(
            [[DirectionCell.from_cell(map_[x,y], to_inputs[x][y], 
                                      to_outputs[x][y], to_charges[x][y])
              for y in range(map_.m)] for x in range(map_.n)])

DirectionMap = GenericDirectionMap[DirectionCell]
