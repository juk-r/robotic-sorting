import csv
import json
import simpy
import simpy.resources.store
import typing

from structures import Map, Direction
from cell import SafeCell, MailInputGetter, Cell
from robot import RobotType, SafeRobot
from brains import OnlineBrain
from exceptions import DataImportException
from typing import Any
from modelling import Model

CellT = typing.TypeVar("CellT", bound=Cell)

def import_json(file_path: str):
    with open(file_path) as file:
        return json.load(file)

def import_cell(env: simpy.Environment, 
                data: dict[str, typing.Any], 
                get_mail_input: MailInputGetter,
                CellType: type[CellT]) -> CellT:
    free: bool = data["free"] if "free" in data else True
    input_id: int | None = data["inputId"] if "inputId" in data else None
    output_id: int | None = data["outputId"] if "outputId" in data else None
    charge_id: int | None = data["chargeId"] if "chargeId" in data else None
    return CellType(env, get_mail_input, input_id, output_id, charge_id, free)

def import_safe_map(env: simpy.Environment,
               data: dict[str, typing.Any], 
               get_mail_input: MailInputGetter
               ) -> tuple[Map[SafeCell], float]:
    return Map([
        [import_cell(env, cell, get_mail_input, SafeCell) for cell in line] 
        for line in data['cells']
        ]), data['span']

def import_map(env: simpy.Environment,
               data: dict[str, typing.Any], 
               get_mail_input: MailInputGetter
               ) -> tuple[Map[Cell], float]:
    return Map([
        [import_cell(env, cell, get_mail_input, Cell) for cell in line] 
        for line in data['cells']
        ]), data['span']

def import_str_position(position: str, n: int) -> tuple[int, int]:
    if len(position) != 2:
        raise DataImportException(f"Invalid position: {position}")
    return (n-int(position[1]), "abcdefghi".find(position[0]))

def import_map_csv(env: simpy.Environment,
                   map_: str,
                   map_details: str,
                   get_mail_input: MailInputGetter,
                   ) -> Map[Any]:
    inputs: dict[tuple[int, int], int] = {}
    outputs: dict[tuple[int, int], int] = {}
    cells: list[list[SafeCell]] = []
    with open(map_details) as map_details_file, open(map_, 'r') as map_file:
        map_reader = csv.reader(map_file, delimiter=' ')
        n = sum(1 for _ in map_reader)
        map_file.seek(0)
        for row in csv.reader(map_details_file, delimiter=' '):
            match row[0]:
                case "Y":
                    outputs[import_str_position(row[1], n)] = int(row[2])
                case "T":
                    inputs[import_str_position(row[1], n)] = int(row[2])
                case other:
                    raise DataImportException(
                        f"Invalid map details, expected Y or T, got {other}")
        for i, row in enumerate(map_reader):
            cells.append([])
            for j, item in enumerate(row):
                match item:
                    case "G":
                        cells[i].append(SafeCell(env))
                    case "R":
                        cells[i].append(SafeCell(env, free=False))
                    case "T":
                        cells[i].append(SafeCell(env, get_mail_input, inputs[i,j]))
                    case "Y":
                        cells[i].append(SafeCell(env, output_id=outputs[i,j]))
                    case other:
                        raise DataImportException(
                            f"Invalid map, expected G, R, T or Y, got {other}")
    return Map(cells)

def import_robot_type(data: dict[str, typing.Any], 
                      span: float) -> RobotType:
    return RobotType(span/data['speed'], data['timeToTurn'], 
                     data['TimeToPut'], data['TimeToTake'])

def import_direction(direction: str):
    match direction:
        case "up": return Direction.up
        case "left": return Direction.left
        case "down": return Direction.down
        case "right": return Direction.right
        case _: raise ValueError(f"{direction} is not direction")

def import_robot(env: Model[Any, Any, Any],
                 data: dict[str, typing.Any], 
                 span: float) -> SafeRobot:
    return SafeRobot(env, import_robot_type(data, span), 
                 data['position'], data['direction'])

def import_state(env: simpy.Environment, 
                 data: dict[str, typing.Any], 
                 brain_from_map: typing.Callable[[Map[Any]], OnlineBrain[Any]], 
                 get_mail_input: MailInputGetter
                 ) -> tuple[OnlineBrain[Any], Map[Any], list[SafeRobot]]:
    raise NotImplementedError()
    map, span = import_safe_map(env, data['map'], get_mail_input)
    brain = brain_from_map(map)
    types = {type_['typeName']: import_robot_type(type_, span) 
                   for type_ in data['robotTypes']}
    robots = [import_robot(env, brain, 
                           robot.update(types[robot["robotType"]]), span)
              for robot in data['robots']]
    return brain, map, robots

def import_probabilities(file_name: str) -> dict[int, float]:
    result: dict[int, float] = {}
    with open(file_name) as file:
        for row in csv.reader(file, delimiter=' '):
            result[int(row[0])] = float(row[1])
    return result
