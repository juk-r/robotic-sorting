import csv
import json
import random
import simpy
import simpy.resources.store
import typing

from structures import Map, Direction, Position
from cell import SafeCell, MailInputGetter, Cell
from robot import RobotType, Robot, SafeRobot
from brains import OnlineBrain
from exceptions import InvalidDataFormat
from typing import Any
from modelling import Model
from mail_factories import RandomAlwaysReadyMail

CellT = typing.TypeVar("CellT", bound=Cell)
RobotT = typing.TypeVar("RobotT", bound=Robot[Cell])

def import_json(file_path: str):
    """short of `json.loads(open(file_path).read())`"""
    with open(file_path) as file:
        return json.load(file)

def import_cell(env: simpy.Environment, 
                data: dict[str, typing.Any], 
                get_mail_input: MailInputGetter,
                CellType: type[CellT]) -> CellT:
    free: bool = data["free"] if "free" in data else True
    input_id: int | None = data["inputId"] if "inputId" in data else None
    output_id: int | None = data["outputId"] if "outputId" in data else None
    return CellType(env, get_mail_input, input_id, output_id, free)

def import_safe_map(env: simpy.Environment,
               data: dict[str, typing.Any], 
               get_mail_input: MailInputGetter
               ) -> tuple[Map[SafeCell], float]:
    """returns `Map` of `SafeCell`s from dictionary (gotten from .json)"""
    return Map([
        [import_cell(env, cell, get_mail_input, SafeCell) for cell in line] 
        for line in data['cells']
        ]), data['span']

def import_map_stations(data: dict[str, typing.Any]) -> tuple[list[int], list[int]]:
    "return: two lists of stations - (inputs, outputs)"
    inputs: list[int] = []
    outputs: list[int] = []
    for line in data['cells']:
        for cell in line:
            if "inputId" in cell:
                inputs.append(cell["inputId"])
            if "outputId" in cell:
                outputs.append(cell["outputId"])
    return inputs, outputs

def import_map(env: simpy.Environment,
               data: dict[str, typing.Any], 
               get_mail_input: MailInputGetter
               ) -> tuple[Map[Cell], float]:
    """returns `Map` of `Cell`s from dictionary (gotten from .json)"""
    return Map([
        [import_cell(env, cell, get_mail_input, Cell) for cell in line] 
        for line in data['cells']
        ]), data['span']

def import_str_position(position: str, n: int) -> tuple[int, int]:
    if len(position) != 2:
        raise InvalidDataFormat(f"Invalid position: {position}")
    return (n-int(position[1]), "abcdefghi".find(position[0]))

def import_map_csv(env: simpy.Environment,
                   map_: str,
                   map_details: str,
                   get_mail_input: MailInputGetter,
                   ) -> Map[SafeCell]:
    """returns map from csv

    param map_: path to map.csv
    param map_details: path to map details
    param get_mail_input: mail factory
    """
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
                    raise InvalidDataFormat(
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
                        raise InvalidDataFormat(
                            f"Invalid map, expected G, R, T or Y, got {other}")
    return Map(cells)

def import_robot_type(data: dict[str, typing.Any]) -> RobotType:
    return RobotType(data['timeToMove'], data['timeToTurn'], 
                     data['timeToPut'], data['timeToTake'])

def import_direction(direction: str):
    match direction:
        case "up": return Direction.up
        case "left": return Direction.left
        case "down": return Direction.down
        case "right": return Direction.right
        case _: raise ValueError(f"{direction} is not direction")

def import_robot(env: Model[Any, Any, Any],
                 data: dict[str, typing.Any],
                 type: RobotType,
                 Type: type[RobotT]
                 ) -> RobotT:
    return Type(env, type, Position(data['x'], data['y']), import_direction(data['direction']),
                None if 'id' not in data else data['id'])

def import_robots(env: Model[Any, Any, Any],
                 data: dict[str, typing.Any],
                 type: RobotType,
                 ) -> list[Robot[Cell]]:
    return [import_robot(env, robot, type, Robot[Cell]) for robot in data["robots"]]

def import_safe_robots(env: Model[Any, Any, Any],
                 data: dict[str, typing.Any],
                 type: RobotType,
                 ) -> list[SafeRobot]:
    return [import_robot(env, robot, type, SafeRobot) for robot in data["robots"]]

def import_state(env: simpy.Environment, 
                 data: dict[str, typing.Any], 
                 brain_from_map: typing.Callable[[Map[Any]], OnlineBrain[Any]], 
                 get_mail_input: MailInputGetter
                 ) -> tuple[OnlineBrain[Any], Map[Any], list[SafeRobot]]:
    """Not implemented"""
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

def import_distribution(data: dict[str, typing.Any], outputs: list[int]) -> list[float]:
    result: list[float] = []
    not_present = sum(str(output) not in data for output in outputs)
    for output in outputs:
        if str(output) in data:
            result.append(data[str(output)])
        elif 'other' in data:
            result.append(data['other'] / not_present)
        else:
            raise ValueError("not all outputs are present")
    return result

def import_distributions(env: simpy.Environment, data: dict[str, typing.Any],
                        inputs: list[int], outputs: list[int],
                        ) -> RandomAlwaysReadyMail:
    other_input = None
    if 'other' in data['distribution']:
        other_input = import_distribution(data["distribution"]["other"], outputs)
    result: dict[int, list[float]] = {}
    for input in inputs:
        if str(input) in data['distribution']:
            result[input] = import_distribution(data["distribution"][str(input)], outputs)
        elif other_input is not None:
            result[input] = other_input
        else:
            raise ValueError("not all inputs are present")
    return RandomAlwaysReadyMail(env, lambda input: random.choices(outputs, result[input])[0])
